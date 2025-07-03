"""
GitHub API client for data collection
"""
import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from github import Github
from core.database import db_manager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("github_client")

class GitHubClient:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.github = Github(self.token, base_url=os.getenv("GITHUB_API_URL", "https://api.github.com"))
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {self.token}",
            "Accept": "application/vscode.github.v3+json"
        })
        self.base_url = os.getenv("GITHUB_API_URL", "https://api.github.com")
        self.username = os.getenv("GITHUB_USERNAME")  # Store authenticated username from .env
    
    def get_repository_commits(self, repo_full_name: str, since: datetime = None, 
                             until: datetime = None) -> List[Dict[str, Any]]:
        """Get commits from a repository"""
        commit_data = []
        try:
            repo = self.github.get_repo(repo_full_name)
            
            # Default to last 30 days if no date range provided
            if not since:
                since = datetime.utcnow() - timedelta(days=30)
            
            # Make sure until is None or a proper datetime
            if until is not None and not isinstance(until, datetime):
                until = None
            
            # Log the exact parameters for debugging
            logger.info(f"Getting commits for {repo_full_name} since {since} until {until or 'now'}")
                
            # Get commits with proper parameters
            commits = repo.get_commits(since=since, until=until)
            
            # Process each commit
            for commit in commits:
                try:
                    # Get detailed commit stats
                    commit_details = repo.get_commit(commit.sha)
                    
                    # Construct commit info with all required fields
                    commit_info = {
                        'sha': commit.sha,
                        'message': commit.commit.message,
                        'author_username': commit.author.login if commit.author else 'unknown',
                        'author_email': commit.commit.author.email,
                        'committed_at': commit.commit.author.date,
                        'repo_name': repo.name,
                        'repo_full_name': repo.full_name,
                        'repo_id': repo.id,
                        'additions': commit_details.stats.additions,
                        'deletions': commit_details.stats.deletions,
                        'changed_files': len(commit_details.files),
                        'files': []
                    }
                    
                    # Add file-level changes
                    for file in commit_details.files:
                        commit_info['files'].append({
                            'filename': file.filename,
                            'status': file.status,
                            'additions': file.additions,
                            'deletions': file.deletions,
                            'changes': file.changes
                        })
                    
                    commit_data.append(commit_info)
                    logger.debug(f"Added commit {commit.sha[:7]} from {commit.commit.author.date}")
                except Exception as e:
                    logger.error(f"Error processing commit {commit.sha}: {str(e)}")
                    # Continue processing other commits
                    continue
        except Exception as e:
            logger.error(f"Error getting commits from {repo_full_name}: {str(e)}")
            return commit_data  # Return empty list or partial data on error
        
        logger.info(f"Found {len(commit_data)} commits for {repo_full_name}")
        return commit_data
    def get_repository_pull_requests(self, repo_full_name: str, state: str = "all",
                                   since: datetime = None) -> List[Dict[str, Any]]:
        """Get pull requests from a repository"""
        pr_data = []
        try:
            repo = self.github.get_repo(repo_full_name)
            
            # Get PRs
            prs = repo.get_pulls(state=state, sort="updated", direction="desc")
            
            for pr in prs:
                try:
                    # Filter by date if provided
                    if since and pr.created_at < since:
                        continue
                    
                    pr_info = {
                        'github_id': pr.id,
                        'number': pr.number,
                        'title': pr.title,
                        'state': pr.state,
                        'author_username': pr.user.login if pr.user else "unknown",
                        'repo_name': repo.name,
                        'repo_full_name': repo.full_name,
                        'repo_id': repo.id,
                        'created_at': pr.created_at,
                        'updated_at': pr.updated_at,
                        'merged_at': pr.merged_at,
                        'closed_at': pr.closed_at,
                        'additions': pr.additions,
                        'deletions': pr.deletions,
                        'changed_files': pr.changed_files,
                        'reviews': []
                    }
                    
                    # Try to get reviews if PR is not a draft
                    if not pr.draft:
                        try:
                            reviews = pr.get_reviews()
                            for review in reviews:
                                pr_info['reviews'].append({
                                    'id': review.id,
                                    'state': review.state,
                                    'author_username': review.user.login if review.user else "unknown",
                                    'submitted_at': review.submitted_at
                                })
                        except Exception as e:
                            print(f"Error getting reviews for PR #{pr.number}: {str(e)}")
                    
                    pr_data.append(pr_info)
                except Exception as e:
                    print(f"Error processing PR #{pr.number if hasattr(pr, 'number') else 'unknown'}: {str(e)}")
                    continue
        except Exception as e:
            print(f"Error getting pull requests from {repo_full_name}: {str(e)}")
            return pr_data  # Return empty list on error
            
            # Get PR reviews
            reviews = pr.get_reviews()
            for review in reviews:
                pr_info['reviews'].append({
                    'github_id': review.id,
                    'reviewer_username': review.user.login,
                    'state': review.state,
                    'submitted_at': review.submitted_at
                })
            
            pr_data.append(pr_info)
        
        return pr_data
    
    def get_organization_repositories(self, org_name: str) -> List[Dict[str, Any]]:
        """Get all repositories in an organization"""
        org = self.github.get_organization(org_name)
        repos = org.get_repos()
        
        repo_data = []
        for repo in repos:
            repo_data.append({
                'id': repo.id,
                'name': repo.name,
                'full_name': repo.full_name,
                'default_branch': repo.default_branch,
                'language': repo.language,
                'size': repo.size,
                'created_at': repo.created_at,
                'updated_at': repo.updated_at
            })
        
        return repo_data
    
    def get_repository_events(self, repo_full_name: str, event_types: List[str] = None) -> List[Dict[str, Any]]:
        """Get repository events (for webhook-like data)"""
        url = f"{self.base_url}/repos/{repo_full_name}/events"
        response = self.session.get(url)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get events: {response.status_code}")
        
        events = response.json()
        
        if event_types:
            events = [event for event in events if event['type'] in event_types]
        
        return events
    
    def get_user_activity(self, username: str, since: datetime = None) -> Dict[str, Any]:
        """Get user activity across all accessible repositories"""
        user = self.github.get_user(username)
        
        if not since:
            since = datetime.utcnow() - timedelta(days=30)
        
        activity = {
            'commits': [],
            'pull_requests': [],
            'issues': [],
            'reviews': []
        }
        
        # Get user's recent activity
        events = user.get_events()
        for event in events:
            if event.created_at < since:
                continue
            
            if event.type == "PushEvent":
                for commit in event.payload.get('commits', []):
                    activity['commits'].append({
                        'sha': commit['sha'],
                        'message': commit['message'],
                        'repo': event.repo.full_name,
                        'created_at': event.created_at
                    })
            
            elif event.type == "PullRequestEvent":
                pr = event.payload['pull_request']
                activity['pull_requests'].append({
                    'number': pr['number'],
                    'title': pr['title'],
                    'action': event.payload['action'],
                    'repo': event.repo.full_name,
                    'created_at': event.created_at
                })
        
        return activity
    
    def sync_repository_data(self, repo_full_name: str, days: int = 30) -> Dict[str, int]:
        """Sync repository data to database"""
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Get and store commits
            try:
                commits = self.get_repository_commits(repo_full_name, since=since)
                stored_commits = 0
                
                for commit_data in commits:
                    try:
                        db_manager.store_commit(commit_data)
                        stored_commits += 1
                    except Exception as e:
                        print(f"Error storing commit {commit_data.get('sha', 'unknown')}: {e}")
            except Exception as e:
                print(f"Error getting commits for {repo_full_name}: {e}")
                commits = []
                stored_commits = 0
            
            # Get and store pull requests
            try:
                prs = self.get_repository_pull_requests(repo_full_name, since=since)
                stored_prs = 0
                
                for pr_data in prs:
                    try:
                        db_manager.store_pull_request(pr_data)
                        stored_prs += 1
                    except Exception as e:
                        print(f"Error storing PR {pr_data.get('number', 'unknown')}: {e}")
            except Exception as e:
                print(f"Error getting PRs for {repo_full_name}: {e}")
                prs = []
                stored_prs = 0
            
            print(f"Repository {repo_full_name}: Found {len(commits)} commits and {len(prs)} PRs in the last {days} days")
            
            return {
                'commits_stored': stored_commits,
                'pull_requests_stored': stored_prs,
                'commits': commits,
                'pull_requests': prs
            }
        except Exception as e:
            print(f"Error synchronizing repository {repo_full_name}: {str(e)}")
            return {
                'commits_stored': 0,
                'pull_requests_stored': 0,
                'commits': [],
                'pull_requests': []
            }
    
    def sync_organization_data(self, org_name: str, days: int = 30) -> Dict[str, Any]:
        """Sync all repositories in an organization"""
        repos = self.get_organization_repositories(org_name)
        results = {
            'repositories_processed': 0,
            'total_commits': 0,
            'total_pull_requests': 0,
            'errors': []
        }
        
        for repo in repos:
            try:
                sync_result = self.sync_repository_data(repo['full_name'], days)
                results['repositories_processed'] += 1
                results['total_commits'] += sync_result['commits_stored']
                results['total_pull_requests'] += sync_result['pull_requests_stored']
            except Exception as e:
                results['errors'].append({
                    'repository': repo['full_name'],
                    'error': str(e)
                })
        
        return results
    
    def validate_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Validate GitHub webhook signature"""
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    def process_webhook_event(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Process incoming webhook event"""
        try:
            if event_type == "push":
                return self._process_push_event(payload)
            elif event_type == "pull_request":
                return self._process_pull_request_event(payload)
            elif event_type == "pull_request_review":
                return self._process_review_event(payload)
            else:
                print(f"Unhandled event type: {event_type}")
                return False
        except Exception as e:
            print(f"Error processing webhook event: {e}")
            return False
    
    def _process_push_event(self, payload: Dict[str, Any]) -> bool:
        """Process push event from webhook"""
        repo = payload['repository']
        commits = payload['commits']
        
        for commit in commits:
            commit_data = {
                'sha': commit['id'],
                'message': commit['message'],
                'author_username': payload['pusher']['name'],
                'author_email': commit['author']['email'],
                'committed_at': datetime.fromisoformat(commit['timestamp'].replace('Z', '+00:00')),
                'repo_name': repo['name'],
                'repo_full_name': repo['full_name'],
                'repo_id': repo['id'],
                'additions': 0,  # Not available in webhook payload
                'deletions': 0,  # Not available in webhook payload
                'changed_files': len(commit.get('added', [])) + len(commit.get('modified', [])) + len(commit.get('removed', []))
            }
            
            db_manager.store_commit(commit_data)
        
        return True
    
    def _process_pull_request_event(self, payload: Dict[str, Any]) -> bool:
        """Process pull request event from webhook"""
        pr = payload['pull_request']
        repo = payload['repository']
        
        pr_data = {
            'github_id': pr['id'],
            'number': pr['number'],
            'title': pr['title'],
            'state': pr['state'],
            'author_username': pr['user']['login'],
            'repo_name': repo['name'],
            'repo_full_name': repo['full_name'],
            'repo_id': repo['id'],
            'created_at': datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00')),
            'updated_at': datetime.fromisoformat(pr['updated_at'].replace('Z', '+00:00')),
            'merged_at': datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00')) if pr['merged_at'] else None,
            'closed_at': datetime.fromisoformat(pr['closed_at'].replace('Z', '+00:00')) if pr['closed_at'] else None,
            'additions': pr.get('additions', 0),
            'deletions': pr.get('deletions', 0),
            'changed_files': pr.get('changed_files', 0)
        }
        
        db_manager.store_pull_request(pr_data)
        return True
    
    def _process_review_event(self, payload: Dict[str, Any]) -> bool:
        """Process pull request review event from webhook"""
        # Implementation for review events
        # This would update the pull request review data
        return True


# Global GitHub client instance
github_client = GitHubClient()
