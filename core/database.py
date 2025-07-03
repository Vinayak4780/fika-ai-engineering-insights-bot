"""
Database connection and operations
"""
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, and_, func
from sqlalchemy.orm import sessionmaker, Session
from core.models import Base, Engineer, Team, Repository, Commit, PullRequest, Deployment, Incident, MetricSnapshot


class DatabaseManager:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", "sqlite:///./performance.db")
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.timezone_name = os.getenv("TIMEZONE", "UTC")
    
    def get_current_datetime(self):
        """Get current datetime with configured timezone"""
        return datetime.now(timezone.utc)
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def get_or_create_engineer(self, github_username: str, email: str = None, team_name: str = None) -> Engineer:
        """Get or create an engineer record"""
        with self.get_session() as session:
            engineer = session.query(Engineer).filter(Engineer.github_username == github_username).first()
            
            if not engineer:
                team = None
                if team_name:
                    team = session.query(Team).filter(Team.name == team_name).first()
                    if not team:
                        team = Team(name=team_name)
                        session.add(team)
                        session.flush()
                
                engineer = Engineer(
                    github_username=github_username,
                    email=email,
                    team_id=team.id if team else None
                )
                session.add(engineer)
                session.commit()
                session.refresh(engineer)
            
            return engineer
    
    def get_or_create_repository(self, name: str, full_name: str, github_id: int) -> Repository:
        """Get or create a repository record"""
        with self.get_session() as session:
            repo = session.query(Repository).filter(Repository.github_id == github_id).first()
            
            if not repo:
                repo = Repository(
                    name=name,
                    full_name=full_name,
                    github_id=github_id
                )
                session.add(repo)
                session.commit()
                session.refresh(repo)
            
            return repo
    
    def store_commit(self, commit_data: Dict[str, Any]) -> Commit:
        """Store commit data"""
        with self.get_session() as session:
            # Check if commit already exists
            existing = session.query(Commit).filter(Commit.sha == commit_data['sha']).first()
            if existing:
                return existing
            
            # Get or create engineer and repository
            engineer = self.get_or_create_engineer(commit_data['author_username'])
            repository = self.get_or_create_repository(
                commit_data['repo_name'],
                commit_data['repo_full_name'],
                commit_data['repo_id']
            )
            
            commit = Commit(
                sha=commit_data['sha'],
                message=commit_data['message'],
                author_id=engineer.id,
                repository_id=repository.id,
                committed_at=commit_data['committed_at'],
                additions=commit_data.get('additions', 0),
                deletions=commit_data.get('deletions', 0),
                changed_files=commit_data.get('changed_files', 0)
            )
            
            session.add(commit)
            session.commit()
            session.refresh(commit)
            return commit
    
    def store_pull_request(self, pr_data: Dict[str, Any]) -> PullRequest:
        """Store pull request data"""
        with self.get_session() as session:
            # Check if PR already exists
            existing = session.query(PullRequest).filter(PullRequest.github_id == pr_data['github_id']).first()
            if existing:
                # Update existing PR
                existing.state = pr_data['state']
                existing.updated_at = pr_data.get('updated_at')
                existing.merged_at = pr_data.get('merged_at')
                existing.closed_at = pr_data.get('closed_at')
                existing.additions = pr_data.get('additions', 0)
                existing.deletions = pr_data.get('deletions', 0)
                existing.changed_files = pr_data.get('changed_files', 0)
                session.commit()
                return existing
            
            # Get or create engineer and repository
            engineer = self.get_or_create_engineer(pr_data['author_username'])
            repository = self.get_or_create_repository(
                pr_data['repo_name'],
                pr_data['repo_full_name'],
                pr_data['repo_id']
            )
            
            pr = PullRequest(
                github_id=pr_data['github_id'],
                number=pr_data['number'],
                title=pr_data['title'],
                state=pr_data['state'],
                author_id=engineer.id,
                repository_id=repository.id,
                created_at=pr_data['created_at'],
                updated_at=pr_data.get('updated_at'),
                merged_at=pr_data.get('merged_at'),
                closed_at=pr_data.get('closed_at'),
                additions=pr_data.get('additions', 0),
                deletions=pr_data.get('deletions', 0),
                changed_files=pr_data.get('changed_files', 0)
            )
            
            session.add(pr)
            session.commit()
            session.refresh(pr)
            return pr
    
    def get_engineer_commits(self, engineer_id: int, days: int = 30) -> List[Commit]:
        """Get commits by engineer in the last N days"""
        with self.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            return session.query(Commit).filter(
                and_(
                    Commit.author_id == engineer_id,
                    Commit.committed_at >= cutoff
                )
            ).all()
    
    def get_team_commits(self, team_id: int, days: int = 30) -> List[Commit]:
        """Get commits by team in the last N days"""
        with self.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            return session.query(Commit).join(Engineer).filter(
                and_(
                    Engineer.team_id == team_id,
                    Commit.committed_at >= cutoff
                )
            ).all()
    
    def get_engineer_pull_requests(self, engineer_id: int, days: int = 30) -> List[PullRequest]:
        """Get pull requests by engineer in the last N days"""
        with self.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            return session.query(PullRequest).filter(
                and_(
                    PullRequest.author_id == engineer_id,
                    PullRequest.created_at >= cutoff
                )
            ).all()
    
    def get_deployments(self, repository_id: int = None, days: int = 30) -> List[Deployment]:
        """Get deployments in the last N days"""
        with self.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = session.query(Deployment).filter(Deployment.deployed_at >= cutoff)
            
            if repository_id:
                query = query.filter(Deployment.repository_id == repository_id)
            
            return query.all()
    
    def get_incidents(self, days: int = 30) -> List[Incident]:
        """Get incidents in the last N days"""
        with self.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            return session.query(Incident).filter(Incident.created_at >= cutoff).all()
    
    def store_metric_snapshot(self, team_id: int = None, engineer_id: int = None, 
                            metric_type: str = None, metric_data: Dict[str, Any] = None):
        """Store a metric snapshot"""
        with self.get_session() as session:
            snapshot = MetricSnapshot(
                date=datetime.utcnow(),
                team_id=team_id,
                engineer_id=engineer_id,
                metric_type=metric_type,
                metric_data=metric_data
            )
            session.add(snapshot)
            session.commit()
    
    def get_engineers_by_team(self, team_id: int) -> List[Engineer]:
        """Get all engineers in a team"""
        with self.get_session() as session:
            return session.query(Engineer).filter(Engineer.team_id == team_id).all()
    
    def get_all_teams(self) -> List[Team]:
        """Get all teams"""
        with self.get_session() as session:
            return session.query(Team).all()
    
    def get_repository_stats(self, repository_id: int, days: int = 30) -> Dict[str, Any]:
        """Get repository statistics"""
        with self.get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Commit stats
            commit_stats = session.query(
                func.count(Commit.id).label('total_commits'),
                func.sum(Commit.additions).label('total_additions'),
                func.sum(Commit.deletions).label('total_deletions'),
                func.sum(Commit.changed_files).label('total_files_changed')
            ).filter(
                and_(
                    Commit.repository_id == repository_id,
                    Commit.committed_at >= cutoff
                )
            ).first()
            
            # PR stats
            pr_stats = session.query(
                func.count(PullRequest.id).label('total_prs'),
                func.avg(
                    func.julianday(PullRequest.merged_at) - func.julianday(PullRequest.created_at)
                ).label('avg_pr_cycle_time')
            ).filter(
                and_(
                    PullRequest.repository_id == repository_id,
                    PullRequest.created_at >= cutoff,
                    PullRequest.state == 'merged'
                )
            ).first()
            
            return {
                'commits': commit_stats._asdict() if commit_stats else {},
                'pull_requests': pr_stats._asdict() if pr_stats else {}
            }


# Global database manager instance
db_manager = DatabaseManager()
