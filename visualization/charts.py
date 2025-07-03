"""
Data visualization and chart generation
"""
import os
import io
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import seaborn as sns


class ChartGenerator:
    """Generate charts and visualizations for performance data"""
    
    def __init__(self):
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Configure matplotlib for better-looking charts
        plt.rcParams.update({
            'figure.figsize': (12, 8),
            'axes.titlesize': 16,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 11,
            'font.size': 10
        })
    
    def create_dora_metrics_chart(self, data: Dict[str, Any]) -> str:
        """Create DORA metrics dashboard chart"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('DORA Metrics Dashboard', fontsize=18, fontweight='bold')
        
        dora = data.get('dora_metrics', {})
        
        # Lead Time
        lead_time = dora.get('lead_time_days', 0)
        ax1.bar(['Lead Time'], [lead_time], color='skyblue', alpha=0.8)
        ax1.set_ylabel('Days')
        ax1.set_title('Lead Time for Changes')
        ax1.set_ylim(0, max(10, lead_time * 1.2))
        
        # Add reference line for good practice (< 1 day)
        ax1.axhline(y=1, color='green', linestyle='--', alpha=0.7, label='Target (1 day)')
        ax1.legend()
        
        # Add value label on bar
        ax1.text(0, lead_time + 0.1, f'{lead_time:.1f}d', ha='center', va='bottom', fontweight='bold')
        
        # Deployment Frequency
        deploy_freq = dora.get('deployment_frequency', 0)
        ax2.bar(['Deployment Frequency'], [deploy_freq], color='lightgreen', alpha=0.8)
        ax2.set_ylabel('Deployments per Day')
        ax2.set_title('Deployment Frequency')
        ax2.set_ylim(0, max(2, deploy_freq * 1.2))
        
        # Add reference line for good practice (> 1 per day)
        ax2.axhline(y=1, color='green', linestyle='--', alpha=0.7, label='Target (1/day)')
        ax2.legend()
        ax2.text(0, deploy_freq + 0.02, f'{deploy_freq:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Change Failure Rate
        failure_rate = dora.get('change_failure_rate', 0)
        color = 'lightcoral' if failure_rate > 15 else 'lightgreen'
        ax3.bar(['Change Failure Rate'], [failure_rate], color=color, alpha=0.8)
        ax3.set_ylabel('Percentage (%)')
        ax3.set_title('Change Failure Rate')
        ax3.set_ylim(0, max(20, failure_rate * 1.2))
        
        # Add reference line for good practice (< 15%)
        ax3.axhline(y=15, color='orange', linestyle='--', alpha=0.7, label='Threshold (15%)')
        ax3.legend()
        ax3.text(0, failure_rate + 0.5, f'{failure_rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # Mean Time to Recovery
        mttr = dora.get('mttr_hours', 0)
        color = 'lightcoral' if mttr > 24 else 'lightgreen'
        ax4.bar(['MTTR'], [mttr], color=color, alpha=0.8)
        ax4.set_ylabel('Hours')
        ax4.set_title('Mean Time to Recovery')
        ax4.set_ylim(0, max(48, mttr * 1.2))
        
        # Add reference line for good practice (< 24 hours)
        ax4.axhline(y=24, color='orange', linestyle='--', alpha=0.7, label='Threshold (24h)')
        ax4.legend()
        ax4.text(0, mttr + 1, f'{mttr:.1f}h', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        return self._save_chart_to_string(fig)
    
    def create_velocity_chart(self, data: Dict[str, Any]) -> str:
        """Create development velocity chart"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Development Velocity Metrics', fontsize=16, fontweight='bold')
        
        basic = data.get('basic_stats', {})
        
        # Commits and PRs
        metrics = ['Commits', 'Pull Requests']
        values = [basic.get('total_commits', 0), basic.get('total_pull_requests', 0)]
        colors = ['#FF6B6B', '#4ECDC4']
        
        bars = ax1.bar(metrics, values, color=colors, alpha=0.8)
        ax1.set_title('Development Activity')
        ax1.set_ylabel('Count')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + max(values) * 0.01,
                    f'{value}', ha='center', va='bottom', fontweight='bold')
        
        # Code changes
        lines_added = basic.get('lines_added', 0)
        lines_deleted = basic.get('lines_deleted', 0)
        files_changed = basic.get('files_changed', 0)
        
        change_metrics = ['Lines Added', 'Lines Deleted', 'Files Changed']
        change_values = [lines_added, lines_deleted, files_changed]
        change_colors = ['#95E1D3', '#F38BA8', '#A8DADC']
        
        bars2 = ax2.bar(change_metrics, change_values, color=change_colors, alpha=0.8)
        ax2.set_title('Code Changes')
        ax2.set_ylabel('Count')
        
        # Add value labels
        for bar, value in zip(bars2, change_values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + max(change_values) * 0.01,
                    f'{value}', ha='center', va='bottom', fontweight='bold')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        return self._save_chart_to_string(fig)
    
    def create_quality_scorecard(self, analysis_data: Dict[str, Any]) -> str:
        """Create quality scorecard visualization"""
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.suptitle('Code Quality Scorecard', fontsize=16, fontweight='bold')
        
        quality_indicators = analysis_data.get('quality_indicators', {})
        
        # Scores
        scores = {
            'Velocity': quality_indicators.get('velocity_score', 0),
            'Quality': quality_indicators.get('quality_score', 0),
            'Collaboration': quality_indicators.get('collaboration_score', 0),
            'Overall': quality_indicators.get('overall_score', 0)
        }
        
        # Create horizontal bar chart
        y_pos = range(len(scores))
        values = list(scores.values())
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        bars = ax.barh(y_pos, values, color=colors, alpha=0.8)
        
        # Customize chart
        ax.set_yticks(y_pos)
        ax.set_yticklabels(scores.keys())
        ax.set_xlabel('Score (0-100)')
        ax.set_xlim(0, 100)
        
        # Add score labels
        for i, (bar, value) in enumerate(zip(bars, values)):
            width = bar.get_width()
            ax.text(width + 1, bar.get_y() + bar.get_height()/2.,
                   f'{value:.1f}', ha='left', va='center', fontweight='bold')
        
        # Add grade
        overall_grade = quality_indicators.get('grade', 'N/A')
        ax.text(85, len(scores) - 0.5, f'Grade: {overall_grade}', 
               fontsize=20, fontweight='bold', 
               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))
        
        # Add reference lines
        for threshold, label, color in [(90, 'Excellent', 'green'), (70, 'Good', 'orange'), (50, 'Fair', 'red')]:
            ax.axvline(x=threshold, color=color, linestyle='--', alpha=0.5)
            ax.text(threshold, -0.7, label, ha='center', va='top', color=color, fontweight='bold')
        
        plt.tight_layout()
        return self._save_chart_to_string(fig)
    
    def create_risk_assessment_chart(self, analysis_data: Dict[str, Any]) -> str:
        """Create risk assessment visualization"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Risk Assessment Dashboard', fontsize=16, fontweight='bold')
        
        risk_assessment = analysis_data.get('risk_assessment', {})
        churn_analysis = analysis_data.get('churn_analysis', {})
        
        # Risk level gauge
        risk_score = risk_assessment.get('risk_score', 0)
        risk_level = risk_assessment.get('overall_risk_level', 'LOW')
        
        # Create gauge chart
        theta = (risk_score / 100) * 180  # Convert to angle (0-180 degrees)
        
        # Draw gauge background
        ax1.add_patch(Rectangle((-1, 0), 2, 1, facecolor='lightgreen', alpha=0.3))
        ax1.add_patch(Rectangle((-1, 0.33), 2, 0.34, facecolor='yellow', alpha=0.3))
        ax1.add_patch(Rectangle((-1, 0.67), 2, 0.33, facecolor='lightcoral', alpha=0.3))
        
        # Draw gauge needle
        import numpy as np
        angle_rad = np.radians(180 - theta)
        needle_x = np.cos(angle_rad) * 0.8
        needle_y = np.sin(angle_rad) * 0.8
        
        ax1.arrow(0, 0, needle_x, needle_y, head_width=0.05, head_length=0.05, 
                 fc='black', ec='black', linewidth=3)
        
        # Labels
        ax1.text(-0.8, 0.17, 'LOW', ha='center', fontweight='bold', color='green')
        ax1.text(0, 0.5, 'MODERATE', ha='center', fontweight='bold', color='orange')
        ax1.text(0.8, 0.83, 'HIGH', ha='center', fontweight='bold', color='red')
        
        ax1.set_xlim(-1.2, 1.2)
        ax1.set_ylim(0, 1.2)
        ax1.set_aspect('equal')
        ax1.axis('off')
        ax1.set_title(f'Risk Level: {risk_level}\nScore: {risk_score:.1f}/100')
        
        # Churn analysis
        churn_data = {
            'Total Churn': churn_analysis.get('total_churn', 0),
            'Churn Rate': churn_analysis.get('churn_rate', 0),
            'Risk Score': churn_analysis.get('risk_score', 0)
        }
        
        bars = ax2.bar(range(len(churn_data)), list(churn_data.values()), 
                      color=['#FF9999', '#66B2FF', '#FFD700'], alpha=0.8)
        ax2.set_xticks(range(len(churn_data)))
        ax2.set_xticklabels(churn_data.keys(), rotation=45)
        ax2.set_title('Code Churn Metrics')
        ax2.set_ylabel('Value')
        
        # Add value labels
        for bar, value in zip(bars, churn_data.values()):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + max(churn_data.values()) * 0.01,
                    f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        return self._save_chart_to_string(fig)
    
    def create_team_comparison_chart(self, teams_data: List[Dict[str, Any]]) -> str:
        """Create team comparison chart"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Team Performance Comparison', fontsize=18, fontweight='bold')
        
        team_names = [team['name'] for team in teams_data]
        
        # Velocity comparison
        commits = [team['metrics']['basic_stats']['total_commits'] for team in teams_data]
        ax1.bar(team_names, commits, color='skyblue', alpha=0.8)
        ax1.set_title('Total Commits')
        ax1.set_ylabel('Commits')
        plt.setp(ax1.get_xticklabels(), rotation=45)
        
        # Quality comparison
        quality_scores = [team['metrics']['quality_indicators']['quality_score'] for team in teams_data]
        ax2.bar(team_names, quality_scores, color='lightgreen', alpha=0.8)
        ax2.set_title('Quality Scores')
        ax2.set_ylabel('Score (0-100)')
        ax2.set_ylim(0, 100)
        plt.setp(ax2.get_xticklabels(), rotation=45)
        
        # Lead time comparison
        lead_times = [team['metrics']['dora_metrics']['lead_time_days'] for team in teams_data]
        ax3.bar(team_names, lead_times, color='orange', alpha=0.8)
        ax3.set_title('Lead Time')
        ax3.set_ylabel('Days')
        plt.setp(ax3.get_xticklabels(), rotation=45)
        
        # Risk scores
        risk_scores = [team['metrics']['risk_assessment']['risk_score'] for team in teams_data]
        colors = ['lightcoral' if score > 50 else 'lightgreen' for score in risk_scores]
        ax4.bar(team_names, risk_scores, color=colors, alpha=0.8)
        ax4.set_title('Risk Scores')
        ax4.set_ylabel('Risk Score (0-100)')
        ax4.set_ylim(0, 100)
        plt.setp(ax4.get_xticklabels(), rotation=45)
        
        plt.tight_layout()
        return self._save_chart_to_string(fig)
    
    def create_trend_chart(self, historical_data: List[Dict[str, Any]]) -> str:
        """Create trend analysis chart"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle('Performance Trends', fontsize=16, fontweight='bold')
        
        dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in historical_data]
        
        # Commits trend
        commits = [d['commits'] for d in historical_data]
        ax1.plot(dates, commits, marker='o', linewidth=2, markersize=6, color='#FF6B6B')
        ax1.set_title('Commits Over Time')
        ax1.set_ylabel('Commits')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        # Quality trend
        quality_scores = [d['quality_score'] for d in historical_data]
        ax2.plot(dates, quality_scores, marker='s', linewidth=2, markersize=6, color='#4ECDC4')
        ax2.set_title('Quality Score Trend')
        ax2.set_ylabel('Quality Score')
        ax2.set_ylim(0, 100)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        # Lead time trend
        lead_times = [d['lead_time'] for d in historical_data]
        ax3.plot(dates, lead_times, marker='^', linewidth=2, markersize=6, color='#95E1D3')
        ax3.set_title('Lead Time Trend')
        ax3.set_ylabel('Days')
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        # Failure rate trend
        failure_rates = [d['failure_rate'] for d in historical_data]
        ax4.plot(dates, failure_rates, marker='D', linewidth=2, markersize=6, color='#F38BA8')
        ax4.set_title('Change Failure Rate Trend')
        ax4.set_ylabel('Percentage (%)')
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        
        # Rotate x-axis labels for better readability
        for ax in [ax1, ax2, ax3, ax4]:
            plt.setp(ax.get_xticklabels(), rotation=45)
        
        plt.tight_layout()
        return self._save_chart_to_string(fig)
    
    def _save_chart_to_string(self, fig) -> str:
        """Save chart to base64 string for easy transmission"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        
        # Convert to base64 string
        chart_data = base64.b64encode(buffer.getvalue()).decode()
        
        plt.close(fig)  # Free memory
        buffer.close()
        
        return chart_data
    
    def generate_performance_charts(self, raw_data: Dict[str, Any], 
                                  analysis_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate all performance charts"""
        charts = []
        
        try:
            # DORA metrics chart
            dora_chart = self.create_dora_metrics_chart(raw_data)
            charts.append({
                'title': 'DORA Metrics Dashboard',
                'type': 'dora_metrics',
                'data': dora_chart
            })
        except Exception as e:
            print(f"Error creating DORA chart: {e}")
        
        try:
            # Velocity chart
            velocity_chart = self.create_velocity_chart(raw_data)
            charts.append({
                'title': 'Development Velocity',
                'type': 'velocity',
                'data': velocity_chart
            })
        except Exception as e:
            print(f"Error creating velocity chart: {e}")
        
        try:
            # Quality scorecard
            quality_chart = self.create_quality_scorecard(analysis_data)
            charts.append({
                'title': 'Code Quality Scorecard',
                'type': 'quality',
                'data': quality_chart
            })
        except Exception as e:
            print(f"Error creating quality chart: {e}")
        
        try:
            # Risk assessment
            risk_chart = self.create_risk_assessment_chart(analysis_data)
            charts.append({
                'title': 'Risk Assessment',
                'type': 'risk',
                'data': risk_chart
            })
        except Exception as e:
            print(f"Error creating risk chart: {e}")
        
        return charts


# Global chart generator instance
chart_generator = ChartGenerator()
