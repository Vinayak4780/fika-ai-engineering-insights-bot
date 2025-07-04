# PupilTree - Engineering Performance Bot

A chat-first, AI-powered system that provides insights into engineering team performance using LangChain agents and GitHub data analysis.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Data Harvester │───▶│   Diff Analyst  │───▶│ Insight Narrator│
│     Agent       │    │     Agent       │    │     Agent       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  GitHub API     │    │   SQLite DB     │    │   Slack Bot     │
│  Integration    │    │  performance.db │    │   Interface     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

```bash
# Option 1: Docker Compose (recommended)
docker compose up --build

# Option 2: Manual setup
# Activate your virtual environment first
python -m venv myenv
myenv\Scripts\activate  # Windows
# source myenv/bin/activate  # Linux/Mac
pip install -r requirements.txt

python main.py setup   # Initialize database and apply fixes
python main.py         # Start the Slack bot
```

## Features

- 🤖 **LangChain/LangGraph Agents**: Pipeline of specialized agents for data processing
- 📊 **DORA Metrics**: Lead time, deployment frequency, change failure rate, MTTR  
- 💬 **Chat-First Interface**: Slack bot with `/dev-report` command
- 📈 **Performance Analytics**: Code activity analysis and team performance tracking
- 🔍 **GitHub Integration**: Comprehensive GitHub API integration
- 📅 **Time-Based Reports**: Daily, weekly, monthly insights
- 📊 **Data Visualization**: Chart generation with matplotlib

## Installation & Setup

1. **Clone and setup**:
   ```bash
   git clone <repo>
   cd pupil_tree
   ```

2. **Configure environment**:
   ```bash
   # Create and activate virtual environment
   python -m venv myenv
   myenv\Scripts\activate  # Windows
   # source myenv/bin/activate  # Linux/Mac
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Create .env file
   cp .env.example .env
   # Edit .env with your API keys
   ```
   
   Required environment variables:
   - `GITHUB_TOKEN`: Personal access token for GitHub API
   - `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `SLACK_APP_TOKEN`: Slack app credentials
   - `GROQ_API_KEY` or other LLM provider credentials

3. **Initialize database and run**:
   ```bash
   # Setup the database and initialize data
   python main.py setup
   
   # Start the bot
   python main.py
   ```

4. **Docker alternative**:
   ```bash
   # Build and start using Docker
   docker compose up --build
   ```

5. **Use in Slack**:
   ```
   /dev-report weekly
   /dev-report daily team:backend
   /dev-report monthly
   ```

## Slack Bot Setup

1. Create a new Slack app at https://api.slack.com/apps
2. Add bot token scopes: `chat:write`, `commands`, `files:write`
3. Install app to workspace and get tokens
4. Add tokens to `.env` file
5. Set up slash command `/dev-report` pointing to your bot

## Environment Configuration

All credentials and configuration settings should be stored in a `.env` file:

```ini
# 1. GitHub Configuration (required)
GITHUB_TOKEN=your_github_token
GITHUB_USERNAME=your_github_username

# 2. Slack Configuration (required)
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_SIGNING_SECRET=your_slack_signing_secret
SLACK_APP_TOKEN=your_slack_app_token

# 3. LLM Provider (required)
LLM_PROVIDER=groq  # Options: groq, openai, anthropic
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama3-8b-8192

# 4. Database Configuration (optional)
DATABASE_URL=sqlite:///./performance.db  # Default: SQLite

# 5. Application Settings (optional)
LOG_LEVEL=INFO
TIMEZONE=UTC
```

For security, never commit your actual `.env` file to version control.

## Usage in Slack

The bot responds to `/dev-report` commands:

```
/dev-report weekly          # Weekly team performance 
/dev-report daily           # Daily metrics
/dev-report monthly         # Monthly analysis
/dev-report team:backend    # Team-specific report
```

## Testing Mode

To see the bot in action without Slack setup:

```bash
# Run the test mode to verify functionality
python main.py test
```

This runs the agent pipeline and displays sample insights without starting the Slack bot, giving you an instant view of the system's capabilities with realistic data.

## Project Structure

The project follows a modular architecture with several main components:

```
pupil_tree/
├── agents/                 # LangGraph agent implementations
│   └── pipeline.py         # Agent pipeline orchestration
├── bot/                   # Slack bot interface
│   └── app.py             # Slack app setup and handlers
├── core/                  # Core business logic
│   ├── database.py        # Database operations
│   ├── metrics.py         # DORA metrics calculation
│   └── models.py          # Database models
├── integrations/          # External service integrations
│   ├── github_client.py   # GitHub API client
│   └── llm_client.py      # LLM abstraction layer
├── visualization/         # Chart and report generation
│   └── charts.py          # Matplotlib chart generation
├── scripts/               # Utility scripts
│   ├── init_db.py         # Database initialization
│   ├── seed_data.py       # Sample data generation
│   ├── setup.py           # Setup script
│   └── various utilities  # Helper and fix scripts
├── docker-compose.yml     # Container orchestration
├── Dockerfile             # Container definition
├── main.py                # Application entry point
├── performance.db         # SQLite database
└── requirements.txt       # Python dependencies
```

## Prerequisites

- Python 3.10+
- Slack workspace with bot permissions
- GitHub personal access token
- Groq API key (for Llama models) or OpenAI API key

## Core Components

### Agent Pipeline

The system uses a LangGraph agent pipeline that processes data in stages:

1. **Data Collection**: Retrieves GitHub commits, PRs, and deployments
2. **Analysis**: Processes raw data to calculate performance metrics
3. **Insight Generation**: Creates human-readable narratives from analysis results

### Database Structure

The SQLite database (`performance.db`) contains the following tables:

- **Engineers**: Developer information linked to GitHub accounts
- **Teams**: Team structures and configurations
- **Repositories**: GitHub repositories tracked by the system
- **Commits**: Git commit history and metadata
- **PullRequests**: PR data including reviews and status
- **Deployments**: Release information
- **Incidents**: Production issues and resolution data
- **MetricSnapshots**: Point-in-time performance metrics

### Metrics Tracked

- **DORA Metrics**
  - Lead Time for Changes
  - Deployment Frequency
  - Change Failure Rate
  - Mean Time to Restore

- **Performance Metrics**
  - Commit frequency
  - Code churn
  - PR review time
  - Deployment success rate

### Visualization

The `ChartGenerator` class provides visualization capabilities:
- DORA metrics dashboards
- Team performance charts
- Individual developer metrics
- Trend analysis

## Docker Support

The project includes Docker configuration for easy deployment:

- `Dockerfile`: Defines the container image based on Python 3.10
- `docker-compose.yml`: Orchestrates the application and database initialization

To build and run with Docker:

```bash
docker compose up --build
```

This will:
1. Build the container image
2. Run database initialization script
3. Start the Slack bot application

## Scripts Directory

The `scripts/` directory contains various utility scripts:

- `init_db.py`: Initialize the database schema
- `seed_data.py`: Create test data for development
- `setup.py`: Combined setup script
- `fix_*.py`: Various fixes for common issues
- `check_*.py`: Diagnostic tools
- `update_repos.py`: Update GitHub repository data
- `setup_demo.py`: Set up demonstration mode
