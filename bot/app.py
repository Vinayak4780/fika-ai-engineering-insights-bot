"""
Slack bot application and handlers
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from agents.pipeline import agent_orchestrator
from visualization.charts import chart_generator
from core.database import db_manager


class SlackBot:
    """Main Slack bot application"""
    
    def __init__(self):
        # Initialize Slack app
        self.app = App(
            token=os.getenv("SLACK_BOT_TOKEN"),
            signing_secret=os.getenv("SLACK_SIGNING_SECRET")
        )
        
        self.client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        
        # Register command handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register Slack command handlers"""
        
        @self.app.command("/dev-report")
        def handle_dev_report(ack, respond, command):
            """Handle /dev-report command"""
            ack()
            
            try:
                # Parse command arguments
                args = self._parse_command_args(command['text'])
                
                # Process the request
                result = self._process_dev_report_request(args, command['user_id'], command['channel_id'])
                
                if result['success']:
                    # Send successful response
                    respond(result['message'])
                    
                    # Upload charts if available
                    if result.get('charts'):
                        self._upload_charts(result['charts'], command['channel_id'])
                else:
                    respond(f"❌ Error generating report: {result['error']}")
            
            except Exception as e:
                respond(f"❌ Error processing request: {str(e)}")
        
        @self.app.command("/dev-status")
        def handle_dev_status(ack, respond, command):
            """Handle /dev-status command for quick status check"""
            ack()
            
            try:
                # Get quick status
                status = self._get_quick_status()
                respond(status)
            except Exception as e:
                respond(f"❌ Error getting status: {str(e)}")
        
        @self.app.command("/dev-help")
        def handle_dev_help(ack, respond, command):
            """Handle /dev-help command"""
            ack()
            
            help_text = """
🤖 **Engineering Performance Bot Help**

**Available Commands:**
• `/dev-report daily` - Daily performance summary
• `/dev-report weekly` - Weekly team insights  
• `/dev-report monthly` - Monthly DORA metrics analysis
• `/dev-report team <team-name>` - Team-specific report
• `/dev-report engineer <username>` - Individual engineer report
• `/dev-status` - Quick status overview
• `/dev-help` - Show this help message

**Report Types:**
• **Daily**: Last 24 hours activity and trends
• **Weekly**: 7-day performance analysis with DORA metrics
• **Monthly**: 30-day comprehensive analysis and insights

**Examples:**
• `/dev-report weekly`
• `/dev-report team backend`
• `/dev-report engineer john.doe`

*Reports include charts, insights, and actionable recommendations*
"""
            respond(help_text)
        
        @self.app.event("app_mention")
        def handle_mention(event, say):
            """Handle mentions of the bot"""
            user = event['user']
            text = event['text']
            
            if 'help' in text.lower():
                say(f"<@{user}> Use `/dev-help` to see available commands!")
            elif 'report' in text.lower():
                say(f"<@{user}> Use `/dev-report weekly` to get a performance report!")
            else:
                say(f"<@{user}> I'm here to help with engineering performance insights! Use `/dev-help` for commands.")
    
    def _parse_command_args(self, command_text: str) -> Dict[str, Any]:
        """Parse command arguments"""
        args = {
            'report_type': 'weekly',  # default
            'target_type': 'all',     # all, team, engineer
            'target_name': None,
            'time_period': 7          # days
        }
        
        if not command_text:
            return args
        
        parts = command_text.strip().split()
        
        for i, part in enumerate(parts):
            if part.lower() in ['daily', 'weekly', 'monthly']:
                args['report_type'] = part.lower()
                if part.lower() == 'daily':
                    args['time_period'] = 1
                elif part.lower() == 'weekly':
                    args['time_period'] = 7
                elif part.lower() == 'monthly':
                    args['time_period'] = 30
            
            elif part.lower() == 'team' and i + 1 < len(parts):
                args['target_type'] = 'team'
                args['target_name'] = parts[i + 1]
            
            elif part.lower() == 'engineer' and i + 1 < len(parts):
                args['target_type'] = 'engineer'
                args['target_name'] = parts[i + 1]
        
        return args
    
    def _process_dev_report_request(self, args: Dict[str, Any], user_id: str, channel_id: str) -> Dict[str, Any]:
        """Process dev report request and generate response"""
        
        try:
            # Determine target IDs
            team_id = None
            engineer_id = None
            
            if args['target_type'] == 'team' and args['target_name']:
                team_id = self._get_team_id_by_name(args['target_name'])
                if not team_id:
                    return {
                        'success': False,
                        'error': f"Team '{args['target_name']}' not found"
                    }
            
            elif args['target_type'] == 'engineer' and args['target_name']:
                engineer_id = self._get_engineer_id_by_username(args['target_name'])
                if not engineer_id:
                    return {
                        'success': False,
                        'error': f"Engineer '{args['target_name']}' not found"
                    }
            
            # Execute agent pipeline
            result = agent_orchestrator.process_request(
                request_type=args['report_type'],
                team_id=team_id,
                engineer_id=engineer_id,
                time_period=args['time_period']
            )
            
            if result.error:
                return {
                    'success': False,
                    'error': result.error
                }
            
            # Generate charts
            charts = chart_generator.generate_performance_charts(
                result.raw_data,
                result.analysis_results
            )
            
            # Format response message
            message = self._format_report_message(result, args)
            
            return {
                'success': True,
                'message': message,
                'charts': charts
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_team_id_by_name(self, team_name: str) -> int:
        """Get team ID by name"""
        teams = db_manager.get_all_teams()
        for team in teams:
            if team.name.lower() == team_name.lower():
                return team.id
        return None
    
    def _get_engineer_id_by_username(self, username: str) -> int:
        """Get engineer ID by GitHub username"""
        with db_manager.get_session() as session:
            from core.models import Engineer
            engineer = session.query(Engineer).filter(
                Engineer.github_username == username
            ).first()
            return engineer.id if engineer else None
    
    def _format_report_message(self, result, args: Dict[str, Any]) -> str:
        """Format the report message for Slack"""
        
        # Header
        report_type = args['report_type'].title()
        period = args['time_period']
        
        if args['target_type'] == 'team':
            header = f"📊 **{report_type} Performance Report - Team {args['target_name']}**"
        elif args['target_type'] == 'engineer':
            header = f"👨‍💻 **{report_type} Performance Report - {args['target_name']}**"
        else:
            header = f"🏢 **{report_type} Performance Report - Organization**"
        
        header += f" _(Last {period} days)_"
        
        # Quick stats
        basic = result.raw_data.get('basic_stats', {})
        quality = result.analysis_results.get('quality_indicators', {})
        risk = result.analysis_results.get('risk_assessment', {})
        
        quick_stats = f"""
**📈 Quick Stats:**
• Commits: {basic.get('total_commits', 0)}
• Pull Requests: {basic.get('total_pull_requests', 0)}
• Lines Changed: +{basic.get('lines_added', 0)} -{basic.get('lines_deleted', 0)}
• Quality Grade: {quality.get('grade', 'N/A')}
• Risk Level: {risk.get('overall_risk_level', 'UNKNOWN')}
"""
        
        # Key insights
        insights_text = ""
        if result.insights:
            insights_text = "**🔍 Key Insights:**\n"
            for i, insight in enumerate(result.insights[:3], 1):
                insights_text += f"{i}. {insight}\n"
        
        # DORA metrics
        dora = result.raw_data.get('dora_metrics', {})
        dora_text = f"""
**🎯 DORA Metrics:**
• Lead Time: {dora.get('lead_time_days', 0):.1f} days
• Deploy Frequency: {dora.get('deployment_frequency', 0):.2f}/day
• Change Failure Rate: {dora.get('change_failure_rate', 0):.1f}%
• MTTR: {dora.get('mttr_hours', 0):.1f} hours
"""
        
        # Combine all parts
        message = f"{header}\n{quick_stats}\n{insights_text}\n{dora_text}"
        
        # Add footer
        message += f"\n_📊 Charts and detailed analysis attached_\n_Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        
        return message
    
    def _upload_charts(self, charts: List[Dict[str, str]], channel_id: str):
        """Upload charts to Slack channel"""
        import base64
        import tempfile
        
        for chart in charts:
            try:
                # Decode base64 chart data
                chart_data = base64.b64decode(chart['data'])
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    tmp_file.write(chart_data)
                    tmp_file.flush()
                    
                    # Upload to Slack
                    response = self.client.files_upload_v2(
                        channel=channel_id,
                        file=tmp_file.name,
                        title=chart['title'],
                        filename=f"{chart['type']}_chart.png"
                    )
                    
                    # Clean up temporary file
                    os.unlink(tmp_file.name)
            
            except Exception as e:
                print(f"Error uploading chart {chart['title']}: {e}")
    
    def _get_quick_status(self) -> str:
        """Get quick status overview"""
        
        try:
            # Get last 24 hours activity
            result = agent_orchestrator.process_request(
                request_type="daily",
                time_period=1
            )
            
            if result.error:
                return f"❌ Unable to get status: {result.error}"
            
            basic = result.raw_data.get('basic_stats', {})
            
            status = f"""
🚀 **System Status: OPERATIONAL**

**📊 Last 24 Hours:**
• {basic.get('total_commits', 0)} commits pushed
• {basic.get('total_pull_requests', 0)} pull requests created
• {basic.get('files_changed', 0)} files modified

**🎯 System Health:**
• Data Pipeline: ✅ Active
• GitHub Integration: ✅ Connected  
• AI Analysis: ✅ Operational
• Chart Generation: ✅ Available

_Use `/dev-report weekly` for detailed insights_
"""
            return status
        
        except Exception as e:
            return f"❌ Status check failed: {str(e)}"
    
    def start(self):
        """Start the Slack bot"""
        handler = SocketModeHandler(self.app, os.getenv("SLACK_APP_TOKEN"))
        print("🤖 Engineering Performance Bot starting...")
        handler.start()


def create_slack_app():
    """Create and return Slack bot instance"""
    return SlackBot()


if __name__ == "__main__":
    bot = create_slack_app()
    bot.start()
