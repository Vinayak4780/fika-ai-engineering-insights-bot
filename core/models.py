"""
Database models for the engineering performance bot
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel

Base = declarative_base()


class Engineer(Base):
    __tablename__ = "engineers"
    
    id = Column(Integer, primary_key=True)
    github_username = Column(String(100), unique=True, nullable=False)
    slack_user_id = Column(String(50))
    email = Column(String(200))
    team_id = Column(Integer, ForeignKey("teams.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    team = relationship("Team", back_populates="engineers")
    commits = relationship("Commit", back_populates="author")
    pull_requests = relationship("PullRequest", back_populates="author")


class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slack_channel = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    engineers = relationship("Engineer", back_populates="team")


class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    full_name = Column(String(300), nullable=False)
    github_id = Column(Integer, unique=True)
    default_branch = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    commits = relationship("Commit", back_populates="repository")
    pull_requests = relationship("PullRequest", back_populates="repository")


class Commit(Base):
    __tablename__ = "commits"
    
    id = Column(Integer, primary_key=True)
    sha = Column(String(40), unique=True, nullable=False)
    message = Column(Text)
    author_id = Column(Integer, ForeignKey("engineers.id"))
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    committed_at = Column(DateTime, nullable=False)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    changed_files = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    author = relationship("Engineer", back_populates="commits")
    repository = relationship("Repository", back_populates="commits")
    file_changes = relationship("FileChange", back_populates="commit")


class PullRequest(Base):
    __tablename__ = "pull_requests"
    
    id = Column(Integer, primary_key=True)
    github_id = Column(Integer, unique=True, nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String(500))
    state = Column(String(20))  # open, closed, merged
    author_id = Column(Integer, ForeignKey("engineers.id"))
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    merged_at = Column(DateTime)
    closed_at = Column(DateTime)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    changed_files = Column(Integer, default=0)
    
    author = relationship("Engineer", back_populates="pull_requests")
    repository = relationship("Repository", back_populates="pull_requests")
    reviews = relationship("PullRequestReview", back_populates="pull_request")


class PullRequestReview(Base):
    __tablename__ = "pull_request_reviews"
    
    id = Column(Integer, primary_key=True)
    github_id = Column(Integer, unique=True, nullable=False)
    pull_request_id = Column(Integer, ForeignKey("pull_requests.id"))
    reviewer_id = Column(Integer, ForeignKey("engineers.id"))
    state = Column(String(20))  # approved, changes_requested, commented
    submitted_at = Column(DateTime, nullable=False)
    
    pull_request = relationship("PullRequest", back_populates="reviews")
    reviewer = relationship("Engineer")


class FileChange(Base):
    __tablename__ = "file_changes"
    
    id = Column(Integer, primary_key=True)
    commit_id = Column(Integer, ForeignKey("commits.id"))
    filename = Column(String(500), nullable=False)
    status = Column(String(20))  # added, modified, removed, renamed
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    
    commit = relationship("Commit", back_populates="file_changes")


class Deployment(Base):
    __tablename__ = "deployments"
    
    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    environment = Column(String(50))  # production, staging, development
    sha = Column(String(40), nullable=False)
    status = Column(String(20))  # success, failure, pending
    deployed_at = Column(DateTime, nullable=False)
    deploy_duration = Column(Float)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    
    repository = relationship("Repository")


class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    severity = Column(String(20))  # critical, high, medium, low
    status = Column(String(20))  # open, investigating, resolved
    created_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime)
    caused_by_deployment_id = Column(Integer, ForeignKey("deployments.id"))
    
    deployment = relationship("Deployment")


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"))
    engineer_id = Column(Integer, ForeignKey("engineers.id"))
    metric_type = Column(String(50), nullable=False)  # dora, churn, review_latency
    metric_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    team = relationship("Team")
    engineer = relationship("Engineer")


class AgentExecution(Base):
    __tablename__ = "agent_executions"
    
    id = Column(Integer, primary_key=True)
    agent_name = Column(String(100), nullable=False)
    execution_id = Column(String(100), nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(String(20))  # success, failure, running
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    
# Pydantic models for API serialization
class EngineerResponse(BaseModel):
    id: int
    github_username: str
    email: Optional[str]
    team_name: Optional[str]
    
    class Config:
        from_attributes = True


class CommitMetrics(BaseModel):
    total_commits: int
    lines_added: int
    lines_deleted: int
    files_changed: int
    avg_commit_size: float


class DORAMetrics(BaseModel):
    lead_time_days: float
    deployment_frequency: float
    change_failure_rate: float
    mean_time_to_recovery_hours: float


class ChurnAnalysis(BaseModel):
    total_churn: int
    churn_rate: float
    high_risk_files: List[str]
    correlation_score: float


class PerformanceReport(BaseModel):
    engineer: EngineerResponse
    period_start: datetime
    period_end: datetime
    commit_metrics: CommitMetrics
    dora_metrics: DORAMetrics
    churn_analysis: ChurnAnalysis
    review_metrics: dict
    insights: List[str]
