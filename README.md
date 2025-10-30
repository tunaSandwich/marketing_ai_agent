# Marketing Agent - Reddit Growth Agent for Goodpods

A sophisticated Reddit Growth Agent that discovers podcast recommendation requests and generates authentic, helpful responses using LLM + RAG while maintaining brand voice and platform compliance.

## 🎯 Project Overview

This system helps Goodpods (and potentially other brands) engage authentically on Reddit by:

- **Discovering** relevant podcast recommendation requests using intelligent search patterns
- **Generating** helpful responses using Claude + brand-specific knowledge
- **Maintaining** authentic voice and brand safety through evaluation systems
- **Tracking** metrics and engagement for optimization
- **Supporting** human review workflow for quality control

### Key Features

- 🔍 **Smart Discovery**: AI-powered post detection with intent classification
- 🤖 **LLM Integration**: Claude-powered response generation with brand context
- 🛡️ **Brand Safety**: Configurable brand packs with voice guidelines and claim validation
- 📊 **Human Review**: Optional approval workflow with evaluation scoring
- 📈 **Metrics Tracking**: Comprehensive engagement and performance monitoring
- 🔧 **Platform Compliance**: Reddit API rate limiting and anti-detection measures

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Reddit Developer Account
- Anthropic API Key (Claude)
- uv package manager (recommended)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd marketing-agent

# Install dependencies with uv (recommended)
uv sync --dev

# Or use pip
pip install -e .[dev]

# Set up pre-commit hooks
pre-commit install
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# - REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
# - ANTHROPIC_API_KEY
# - Other configuration options
```

### First Run

```bash
# Test connections
python -c "from src.utils.config import get_settings; print('✓ Config loaded')"

# Run discovery in dry-run mode
python -m src.main --mode discover --dry-run

# Generate test responses
python -m src.main --mode generate --limit 3
```

## 📁 Project Structure

```
marketing-agent/
├── src/                    # Main source code
│   ├── reddit/            # Reddit API integration
│   │   ├── adapter.py     # Reddit API wrapper
│   │   └── search.py      # Discovery logic
│   ├── llm/               # LLM integration
│   │   ├── client.py      # Claude API client
│   │   └── prompts.py     # Prompt templates
│   ├── brand/             # Brand pack system
│   │   └── loader.py      # Brand config loader
│   ├── utils/             # Shared utilities
│   │   └── config.py      # Configuration management
│   └── models.py          # Data models
├── brands/                # Brand configurations
│   └── goodpods/         # Goodpods brand pack
│       ├── config.yaml   # Brand configuration
│       └── knowledge/    # RAG knowledge base
├── tests/                # Test suite
├── scripts/              # Helper scripts
└── .claude/              # Claude Code integration
```

## 🛠️ Development

### Code Quality Tools

This project uses modern Python tooling for quality and consistency:

```bash
# Format code
ruff format .

# Lint code
ruff check . --fix

# Type checking
mypy src/

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# All checks (runs automatically on commit)
pre-commit run --all-files
```

### Development Workflow

1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Write tests first**: Follow TDD principles
3. **Implement feature**: Keep functions small and focused
4. **Run quality checks**: Ensure all linters and tests pass
5. **Commit changes**: Pre-commit hooks will run automatically
6. **Submit for review**: Create pull request

### Testing

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_models.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

## 🎨 Brand Pack System

### Configuration Structure

Each brand has its own configuration in `brands/{brand_id}/`:

```yaml
# brands/goodpods/config.yaml
brand_id: "goodpods"
brand_name: "Goodpods - Your Podcast Player"
voice_guidelines: |
  - Helpful and enthusiastic about podcast discovery
  - Natural and conversational, like a fellow podcast lover
allowed_claims:
  - "Free podcast player with social features"
  - "Discover podcasts through friends' recommendations"
primary_cta: "https://goodpods.app/discover"
subreddits_tier1: ["podcasts", "podcast"]
```

### Creating New Brands

```bash
# Create brand template
python -c "
from src.brand.loader import BrandLoader
loader = BrandLoader(Path('brands'))
loader.create_brand_template('new_brand')
"

# Edit the generated config
vim brands/new_brand/config.yaml

# Add knowledge files
echo '# Product Features' > brands/new_brand/knowledge/features.md
```

## 🤖 Usage Examples

### Discovery Mode

```bash
# Discover opportunities (dry run)
python -m src.main --mode discover --dry-run --limit 10

# Discover and process
python -m src.main --mode discover --brand goodpods
```

### Response Generation

```bash
# Generate responses for specific posts
python -m src.main --mode generate --post-ids "abc123,def456"

# Generate with specific brand
python -m src.main --mode generate --brand goodpods --limit 5
```

### Full Orchestration

```bash
# Run the full pipeline
python -m src.main --mode pilot --replies-per-day 10

# Monitor in real-time
python -m src.main --mode monitor
```

## 📊 Monitoring & Metrics

### Key Metrics Tracked

- **Discovery Rate**: Posts found per hour
- **Approval Rate**: Human approval percentage
- **Engagement**: Upvotes, clicks, replies
- **Quality Scores**: AI evaluation metrics
- **Compliance**: Platform violations, rate limits

### Accessing Metrics

```bash
# View today's metrics
python -m src.metrics --date today

# Generate weekly report
python -m src.metrics --report weekly

# Real-time dashboard
streamlit run dashboard/app.py
```

## 🔒 Security & Compliance

### Platform Compliance

- **Rate Limiting**: Automatic enforcement of Reddit API limits
- **Account Health**: Karma and age requirement checking
- **Natural Behavior**: Randomized timing and activity patterns
- **Content Quality**: AI evaluation before posting

### Security Features

- **Credential Management**: Environment variable based secrets
- **Claim Validation**: Allowed claims whitelist enforcement
- **Content Safety**: Brand guideline compliance checking
- **Audit Trail**: Comprehensive logging of all actions

## 🚨 Troubleshooting

### Common Issues

**Rate Limiting Errors**
```bash
# Check current rate limit status
python -c "from src.reddit.adapter import RedditAdapter; print('Rate limit OK')"
```

**Authentication Failures**
```bash
# Verify credentials
python -c "from src.utils.config import get_settings; s = get_settings(); print(f'Reddit: {s.reddit.username}')"
```

**Test Failures**
```bash
# Run tests with verbose output
pytest -v --tb=short

# Check specific test
pytest tests/test_models.py::TestRedditPost -v
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debug info
python -m src.main --debug --mode discover --limit 1
```

## 🤝 Contributing

### Code Style

- **Type Hints**: Required on all functions
- **Docstrings**: Google-style documentation
- **Error Handling**: Comprehensive exception handling
- **Testing**: 80%+ coverage target
- **Logging**: Structured logging with loguru

### Pull Request Process

1. Fork the repository
2. Create feature branch from `main`
3. Write tests for new functionality
4. Ensure all quality checks pass
5. Update documentation if needed
6. Submit pull request with clear description

### Adding New Features

1. **Start with tests**: Define expected behavior
2. **Update models**: Add new data structures if needed
3. **Implement core logic**: Keep functions focused
4. **Add configuration**: Make features configurable
5. **Document usage**: Update README and CLAUDE.md

## 📋 Roadmap

### Phase 1: Foundation (✅ Complete)
- [x] Project structure and tooling
- [x] Core data models and interfaces
- [x] Basic Reddit and LLM integration
- [x] Brand pack system
- [x] Initial test suite

### Phase 2: MVP Implementation (🚧 In Progress)
- [ ] Reddit discovery implementation
- [ ] Response generation pipeline
- [ ] Evaluation and routing system
- [ ] Human review interface
- [ ] Basic metrics tracking

### Phase 3: Enhancement (📋 Planned)
- [ ] RAG integration with vector database
- [ ] Advanced evaluation rubrics
- [ ] Multi-brand concurrent processing
- [ ] A/B testing framework
- [ ] Advanced analytics dashboard

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Documentation**: See [CLAUDE.md](CLAUDE.md) for detailed technical info
- **Issues**: Report bugs via GitHub Issues
- **Questions**: Check existing issues or create new one

---

**⚡ Quick Commands Reference**

```bash
# Development
uv sync --dev              # Install dependencies
pytest                     # Run tests
ruff format . && ruff check .  # Format and lint
pre-commit run --all-files # Run all quality checks

# Application
python -m src.main --mode discover --dry-run  # Test discovery
python -m src.main --mode generate --limit 3  # Generate responses
python -m src.main --mode pilot --replies-per-day 5  # Full pipeline

# Monitoring
tail -f logs/app.log       # View logs
streamlit run dashboard/app.py  # Metrics dashboard
```

Built with ❤️ for authentic community engagement.