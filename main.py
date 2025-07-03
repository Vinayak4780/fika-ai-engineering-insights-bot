"""
Main application entry point
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main application entry point"""
    
    # Check if we should run setup or test
    if len(sys.argv) > 1:
        if sys.argv[1] == "setup":
            from scripts.setup import setup
            setup()
            return
        elif sys.argv[1] == "test":
            from agents.pipeline import agent_orchestrator
            print("🧪 Testing agent pipeline...")
            
            # Test the agent pipeline
            result = agent_orchestrator.process_request(
                request_type="weekly",
                time_period=7
            )
            
            if hasattr(result, 'error') and result.error:
                print(f"❌ Test failed: {result.error}")
            else:
                print("✅ Agent pipeline test successful!")
                insights = getattr(result, 'insights', []) or []
                narrative = getattr(result, 'narrative', '') or ''
                print(f"📊 Generated {len(insights)} insights")
                print(f"📝 Narrative length: {len(narrative)} characters")
                
                # Show some sample insights
                if insights:
                    print("\n🔍 Sample Insights:")
                    for i, insight in enumerate(insights[:3], 1):
                        print(f"  {i}. {insight[:100]}...")
            return
    
    # Start the Slack bot
    try:
        print("🚀 Starting Engineering Performance Bot...")
        
        # Check required environment variables
        required_vars = ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("Please check your .env file")
            return
        
        # Initialize database if it doesn't exist
        from core.database import db_manager
        db_manager.create_tables()
        
        # Start the bot
        from bot.app import create_slack_app
        bot = create_slack_app()
        bot.start()
        
    except KeyboardInterrupt:
        print("\n👋 Bot shutting down...")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
