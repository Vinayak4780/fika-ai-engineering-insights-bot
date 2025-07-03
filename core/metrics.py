"""
DORA metrics and performance calculations
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from core.database import db_manager
from core.models import Engineer, Team, Commit, PullRequest, Deployment, Incident


@dataclass
class DORAMetrics:
    lead_time_days: float
    deployment_frequency: float  # deployments per day
    change_failure_rate: float  # percentage
    mean_time_to_recovery_hours: float


@dataclass
class CodeChurnMetrics:
    total_churn: int
    churn_rate: float
    high_churn_files: List[str]
    risk_score: float


@dataclass
class ReviewMetrics:
    avg_review_time_hours: float
    review_participation_rate: float
    pr_cycle_time_hours: float
    approval_rate: float


class MetricsCalculator:
    def __init__(self):
        self.db = db_manager
    
    def calculate_dora_metrics(self, team_id: int = None, engineer_id: int = None, days: int = 30) -> DORAMetrics:
        """Calculate DORA metrics for a team or engineer"""
        
        # Lead Time (commit to deployment)
        lead_time = self._calculate_lead_time(team_id, engineer_id, days)
        
        # Deployment Frequency
        deployment_freq = self._calculate_deployment_frequency(team_id, days)
        
        # Change Failure Rate
        change_failure_rate = self._calculate_change_failure_rate(team_id, days)
        
        # Mean Time to Recovery
        mttr = self._calculate_mttr(team_id, days)
        
        return DORAMetrics(
            lead_time_days=lead_time,
            deployment_frequency=deployment_freq,
            change_failure_rate=change_failure_rate,
            mean_time_to_recovery_hours=mttr
        )
    
    def _calculate_lead_time(self, team_id: int, engineer_id: int, days: int) -> float:
        """Calculate lead time from commit to deployment"""
        with self.db.get_session() as session:
            # Get commits in the period
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            if engineer_id:
                commits = session.query(Commit).filter(
                    Commit.author_id == engineer_id,
                    Commit.committed_at >= cutoff
                ).all()
            elif team_id:
                commits = self.db.get_team_commits(team_id, days)
            else:
                commits = session.query(Commit).filter(Commit.committed_at >= cutoff).all()
            
            # Get deployments and match with commits
            deployments = self.db.get_deployments(days=days)
            
            lead_times = []
            for commit in commits:
                # Find the first deployment after this commit
                for deployment in deployments:
                    if (deployment.deployed_at > commit.committed_at and 
                        deployment.repository_id == commit.repository_id):
                        lead_time = (deployment.deployed_at - commit.committed_at).total_seconds() / 86400  # days
                        lead_times.append(lead_time)
                        break
            
            return sum(lead_times) / len(lead_times) if lead_times else 0.0
    
    def _calculate_deployment_frequency(self, team_id: int, days: int) -> float:
        """Calculate deployment frequency (deployments per day)"""
        deployments = self.db.get_deployments(days=days)
        successful_deployments = [d for d in deployments if d.status == 'success']
        
        return len(successful_deployments) / days if days > 0 else 0.0
    
    def _calculate_change_failure_rate(self, team_id: int, days: int) -> float:
        """Calculate percentage of deployments that cause failures"""
        deployments = self.db.get_deployments(days=days)
        incidents = self.db.get_incidents(days=days)
        
        if not deployments:
            return 0.0
        
        # Count deployments that caused incidents
        failed_deployments = 0
        for deployment in deployments:
            for incident in incidents:
                if incident.caused_by_deployment_id == deployment.id:
                    failed_deployments += 1
                    break
        
        return (failed_deployments / len(deployments)) * 100
    
    def _calculate_mttr(self, team_id: int, days: int) -> float:
        """Calculate mean time to recovery in hours"""
        incidents = self.db.get_incidents(days=days)
        resolved_incidents = [i for i in incidents if i.resolved_at]
        
        if not resolved_incidents:
            return 0.0
        
        recovery_times = []
        for incident in resolved_incidents:
            recovery_time = (incident.resolved_at - incident.created_at).total_seconds() / 3600  # hours
            recovery_times.append(recovery_time)
        
        return sum(recovery_times) / len(recovery_times)
    
    def calculate_code_churn_metrics(self, engineer_id: int = None, team_id: int = None, days: int = 30) -> CodeChurnMetrics:
        """Calculate code churn and risk metrics"""
        
        if engineer_id:
            commits = self.db.get_engineer_commits(engineer_id, days)
        elif team_id:
            commits = self.db.get_team_commits(team_id, days)
        else:
            with self.db.get_session() as session:
                cutoff = datetime.utcnow() - timedelta(days=days)
                commits = session.query(Commit).filter(Commit.committed_at >= cutoff).all()
        
        # Calculate total churn (additions + deletions)
        total_churn = sum(commit.additions + commit.deletions for commit in commits)
        
        # Calculate churn rate (churn per commit)
        churn_rate = total_churn / len(commits) if commits else 0.0
        
        # Identify high-churn files (requires file-level analysis)
        high_churn_files = self._identify_high_churn_files(commits)
        
        # Calculate risk score based on churn patterns
        risk_score = self._calculate_churn_risk_score(commits)
        
        return CodeChurnMetrics(
            total_churn=total_churn,
            churn_rate=churn_rate,
            high_churn_files=high_churn_files,
            risk_score=risk_score
        )
    
    def _identify_high_churn_files(self, commits: List[Commit]) -> List[str]:
        """Identify files with high churn rates"""
        # For now, return empty list since we don't have file-level data seeded
        # In a real implementation, this would analyze file_changes
        return []
    
    def _calculate_churn_risk_score(self, commits: List[Commit]) -> float:
        """Calculate risk score based on churn patterns (0-100)"""
        if not commits:
            return 0.0
        
        # Factors contributing to risk:
        # 1. High churn rate
        # 2. Frequency of large commits
        # 3. Inconsistent commit patterns
        
        total_churn = sum(commit.additions + commit.deletions for commit in commits)
        avg_churn_per_commit = total_churn / len(commits)
        
        # Large commit penalty (commits > 300 lines)
        large_commits = sum(1 for commit in commits if (commit.additions + commit.deletions) > 300)
        large_commit_ratio = large_commits / len(commits)
        
        # Calculate base risk score
        risk_score = min(100, (avg_churn_per_commit / 10) + (large_commit_ratio * 50))
        
        return risk_score
    
    def calculate_review_metrics(self, engineer_id: int = None, team_id: int = None, days: int = 30) -> ReviewMetrics:
        """Calculate code review metrics"""
        
        with self.db.get_session() as session:
            if engineer_id:
                prs = self.db.get_engineer_pull_requests(engineer_id, days)
            elif team_id:
                cutoff = datetime.utcnow() - timedelta(days=days)
                prs = session.query(PullRequest).join(Engineer).filter(
                    Engineer.team_id == team_id,
                    PullRequest.created_at >= cutoff
                ).all()
            else:
                cutoff = datetime.utcnow() - timedelta(days=days)
                prs = session.query(PullRequest).filter(PullRequest.created_at >= cutoff).all()
            
            if not prs:
                return ReviewMetrics(0.0, 0.0, 0.0, 0.0)
            
            # For now, return mock review metrics since we don't have review data seeded
            # In a real implementation, this would analyze PR reviews
            return ReviewMetrics(
                avg_review_time_hours=8.5,  # Mock data
                review_participation_rate=85.0,  # Mock data
                pr_cycle_time_hours=24.0,  # Mock data
                approval_rate=92.0  # Mock data
            )
    
    def generate_performance_summary(self, engineer_id: int = None, team_id: int = None, 
                                   days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive performance summary"""
        
        dora_metrics = self.calculate_dora_metrics(team_id, engineer_id, days)
        churn_metrics = self.calculate_code_churn_metrics(engineer_id, team_id, days)
        review_metrics = self.calculate_review_metrics(engineer_id, team_id, days)
        
        # Get basic commit/PR stats
        if engineer_id:
            commits = self.db.get_engineer_commits(engineer_id, days)
            prs = self.db.get_engineer_pull_requests(engineer_id, days)
        elif team_id:
            commits = self.db.get_team_commits(team_id, days)
            with self.db.get_session() as session:
                cutoff = datetime.utcnow() - timedelta(days=days)
                prs = session.query(PullRequest).join(Engineer).filter(
                    Engineer.team_id == team_id,
                    PullRequest.created_at >= cutoff
                ).all()
        else:
            # Get all commits and PRs for the organization
            with self.db.get_session() as session:
                cutoff = datetime.utcnow() - timedelta(days=days)
                commits = session.query(Commit).filter(Commit.committed_at >= cutoff).all()
                prs = session.query(PullRequest).filter(PullRequest.created_at >= cutoff).all()
        
        return {
            'period_days': days,
            'basic_stats': {
                'total_commits': len(commits),
                'total_pull_requests': len(prs),
                'lines_added': sum(c.additions for c in commits),
                'lines_deleted': sum(c.deletions for c in commits),
                'files_changed': sum(c.changed_files for c in commits)
            },
            'dora_metrics': {
                'lead_time_days': dora_metrics.lead_time_days,
                'deployment_frequency': dora_metrics.deployment_frequency,
                'change_failure_rate': dora_metrics.change_failure_rate,
                'mttr_hours': dora_metrics.mean_time_to_recovery_hours
            },
            'code_quality': {
                'total_churn': churn_metrics.total_churn,
                'churn_rate': churn_metrics.churn_rate,
                'risk_score': churn_metrics.risk_score,
                'high_risk_files': len(churn_metrics.high_churn_files)
            },
            'review_metrics': {
                'avg_review_time_hours': review_metrics.avg_review_time_hours,
                'review_participation_rate': review_metrics.review_participation_rate,
                'pr_cycle_time_hours': review_metrics.pr_cycle_time_hours,
                'approval_rate': review_metrics.approval_rate
            }
        }


# Global metrics calculator instance
metrics_calculator = MetricsCalculator()
