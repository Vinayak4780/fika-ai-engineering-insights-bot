# Engineering Performance Bot MVP

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
│  GitHub API     │    │  Analytics DB   │    │   Slack Bot     │
│   Webhooks      │    │   (SQLite)      │    │   Interface     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

```bash
# Option 1: Docker Compose (recommended)
docker compose up --build

# Option 2: Manual setup
python main.py setup   # Initialize database and apply fixes
python main.py         # Start the Slack bot
```

## Features

- 🤖 **LangChain/LangGraph Agents**: Data Harvester → Diff Analyst → Insight Narrator
- 📊 **DORA Metrics**: Lead time, deployment frequency, change failure rate, MTTR  
- 💬 **Chat-First Interface**: Slack bot with `/dev-report` command
- 📈 **Diff Analytics**: Code churn analysis, risk assessment, outlier detection
- 🔍 **GitHub Integration**: Real-time webhook processing and REST API data
- 📅 **Time-Based Reports**: Daily, weekly, monthly insights
- 🎯 **Business Value Mapping**: Technical metrics linked to business outcomes

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repo>
   cd engineering-performance-bot
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```
   
   Required environment variables:
   - `GITHUB_TOKEN`: Personal access token for GitHub API
   - `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `SLACK_APP_TOKEN`: Slack app credentials
   - `DATABASE_URL`: Database connection string
   - `GROQ_API_KEY` or other LLM provider credentials

3. **Run with one command**:
   ```bash
   docker compose up --build
   ```

4. **Use in Slack**:
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

All credentials and configuration settings are stored in the `.env` file:

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

Copy the `.env.example` file and fill in your credentials:

```bash
cp .env.example .env
# Edit with your preferred text editor
```

For security, never commit your actual `.env` file to version control.

# Database
DATABASE_URL=sqlite:///./data/performance.db
```

## Usage in Slack

The bot responds to `/dev-report` commands:

```
/dev-report weekly          # Weekly team performance 
/dev-report daily           # Daily metrics
/dev-report monthly         # Monthly analysis
/dev-report team:backend    # Team-specific report
```

## Demo Mode

To see the bot in action without Slack setup:

```bash
# Run the test mode to verify functionality
python main.py test
```

This runs the agent pipeline and displays sample insights without starting the Slack bot.

This gives reviewers an instant view of the system's capabilities with realistic data.

## API Endpoints (Optional)

While the challenge focuses on chat-first, we also provide JSON API:

- `GET /metrics` - Performance metrics with parameters
- `GET /report` - Comprehensive reports  
- `GET /charts` - Performance visualizations
- `GET /dashboard` - Interactive web interface

Access at: http://localhost:8000 (when running FastAPI mode)

- **Agent-Centric Design**: Three specialized LangGraph agents working in pipeline
- **GitHub Integration**: Real-time data ingestion via REST API and webhooks
- **DORA Metrics**: Tracks lead time, deployment frequency, change failure rate, and MTTR
- **Diff Analytics**: Code churn analysis and defect risk correlation
- **Slack Integration**: Interactive `/dev-report` command with rich visualizations
- **One-Command Bootstrap**: Simple setup with Docker Compose

## Quick Start

### Prerequisites
- Python 3.10+
- Slack workspace with bot permissions
- GitHub personal access token
- Groq API key (for Llama models) or OpenAI API key

### Installation

1. Clone and setup:
```bash
git clone <repo-url>
cd pupil_tree
python -m venv myenv
# Windows
myenv\Scripts\activate
# Linux/Mac
source myenv/bin/activate
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and tokens
```

3. Initialize database and seed data:
```bash
python scripts/init_db.py
python scripts/seed_data.py
```

4. Start the bot:
```bash
python main.py
```

Or use Docker:
```bash
docker-compose up
```

### Slack Bot Setup

1. Create a new Slack app at https://api.slack.com/apps
2. Add bot token scopes: `chat:write`, `commands`, `files:write`
3. Install app to workspace
4. Copy bot token to `.env`
5. Enable slash commands: `/dev-report`

## Usage

In Slack, use these commands:

- `/dev-report daily` - Daily performance summary
- `/dev-report weekly` - Weekly team insights
- `/dev-report monthly` - Monthly DORA metrics analysis

## Project Structure

```
pupil_tree/
├── agents/                 # LangGraph agent implementations
│   ├── data_harvester.py  # GitHub data collection
│   ├── diff_analyst.py    # Code churn and risk analysis
│   └── insight_narrator.py # AI narrative generation
├── bot/                   # Slack bot interface
│   ├── handlers.py        # Command handlers
│   └── app.py            # Slack app setup
├── core/                  # Core business logic
│   ├── models.py         # Data models
│   ├── database.py       # Database operations
│   └── metrics.py        # DORA metrics calculation
├── integrations/          # External service integrations
│   ├── github_client.py  # GitHub API client
│   └── llm_client.py     # LLM abstraction layer
├── visualization/         # Chart and report generation
│   └── charts.py         # Matplotlib/Plotly charts
├── scripts/              # Utility scripts
│   ├── init_db.py       # Database initialization
│   └── seed_data.py     # Sample data generation
├── docker-compose.yml    # Container orchestration
├── Dockerfile           # Container definition
├── .env.example         # Environment template
└── main.py             # Application entry point
```

## Configuration

### Environment Variables

```
# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Slack
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx
SLACK_SIGNING_SECRET=xxxxxxxxxxxxx

# Groq (default - fast Llama models)
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
LLM_PROVIDER=groq

# Database
DATABASE_URL=sqlite:///./performance.db
```

### Agent Configuration

The system uses three LangGraph agents:

1. **Data Harvester**: Collects GitHub events, commits, and PR data
2. **Diff Analyst**: Analyzes code changes and calculates risk metrics
3. **Insight Narrator**: Generates human-readable performance insights

## Metrics Tracked

### DORA Metrics
- **Lead Time**: Time from commit to deployment
- **Deployment Frequency**: How often deployments occur
- **Change Failure Rate**: Percentage of deployments causing failures
- **Mean Time to Recovery**: Average time to fix incidents

### Code Quality Metrics
- Lines added/deleted per commit
- Files touched per change
- Code churn correlation with defects
- Review latency and throughput

## API Endpoints

The bot exposes optional JSON endpoints:

- `GET /metrics/team/{team_id}` - Team performance data
- `GET /metrics/engineer/{engineer_id}` - Individual metrics
- `POST /webhook/github` - GitHub webhook receiver

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black .
flake8 .
```

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Define state schema and graph structure
3. Register in LangGraph workflow
4. Add integration tests

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check Slack permissions and token validity
2. **GitHub API rate limits**: Implement token rotation or caching
3. **Agent failures**: Check LLM API keys and quotas

### Logs

Application logs are available in `logs/` directory with structured JSON format for easy parsing.

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push branch: `git push origin feature/new-feature`
5. Submit pull request

## License

MIT License - see LICENSE file for details.
