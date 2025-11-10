# Marketing Agent - Claude Context & Memory

## Project Overview

This is a Reddit Growth Agent MVP for Goodpods (podcast discovery app). The system discovers podcast recommendation requests on Reddit and generates authentic, helpful responses using LLM + RAG while maintaining brand voice and platform compliance.

**Key Goals:**
- Discover relevant podcast recommendation requests on Reddit
- Generate helpful, authentic responses using Claude + RAG
- Maintain brand voice consistency for Goodpods
- Include human review workflow for quality control
- Track metrics and ensure platform compliance

## Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   Brand Pack        │────▶│   Orchestrator       │────▶│ Reddit Adapter      │
│ - Voice/tone        │     │ - Discovery loop     │     │ - Search posts      │
│ - Claims            │     │ - RAG lookup         │     │ - Post replies      │  
│ - Docs/FAQs         │     │ - Draft generation   │     │ - Track metrics     │
│ - Guidelines        │     │ - Evaluation         │     │                     │
└─────────────────────┘     └──────────────────────┘     └─────────────────────┘
                                      │
                                      ▼
                            ┌──────────────────────┐
                            │    Evaluator         │
                            │ - Score drafts       │
                            │ - Route decisions    │
                            │ - Log outcomes       │
                            └──────────────────────┘
```

## Module Structure

### `src/reddit/`
- `adapter.py`: Reddit API wrapper with rate limiting and compliance
- `search.py`: Discovery logic for finding relevant posts

### `src/llm/`
- `client.py`: Claude API client with retry logic
- `prompts.py`: Prompt templates for response generation

### `src/brand/`
- `loader.py`: Brand pack configuration loading and validation

### `src/utils/`
- `config.py`: Configuration management with Pydantic

### `brands/goodpods/`
- `config.yaml`: Brand-specific configuration
- `knowledge/`: Documents for RAG indexing

## Development Commands

### Environment Setup
```bash
# Install dependencies with uv (preferred)
uv sync --dev
uv run pytest

# Or with pip
pip install -e .[dev]
```

### Code Quality
```bash
# Format and lint
ruff format .
ruff check . --fix

# Type checking
mypy src/

# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### Running the Application
```bash
# Discovery mode (dry run)
python -m src.main --mode discover --dry-run

# Generate responses
python -m src.main --mode generate --limit 5

# Start orchestrator
python -m src.main --mode pilot --replies-per-day 3
```

## Code Style Guidelines

### Core Principles
1. **Type hints everywhere**: Every function must have proper type annotations
2. **Pydantic for data validation**: Use Pydantic models for all configuration and data structures
3. **Functional approach**: Prefer pure functions over stateful classes where possible
4. **Error handling**: Use proper exception handling with tenacity for retries
5. **Logging**: Use loguru for structured logging
6. **Testing**: Write tests alongside code, aim for 80%+ coverage

### Code Patterns

#### Configuration Loading
```python
from pydantic import BaseModel
from pydantic_settings import BaseSettings

class RedditConfig(BaseModel):
    client_id: str
    client_secret: str
    user_agent: str

class Settings(BaseSettings):
    reddit: RedditConfig
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "_"
```

#### API Clients
```python
from tenacity import retry, stop_after_attempt, wait_exponential
import httpx

class RedditAdapter:
    def __init__(self, config: RedditConfig) -> None:
        self._config = config
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search_posts(self, query: str) -> list[RedditPost]:
        # Implementation with proper error handling
```

#### Data Models
```python
from pydantic import BaseModel, Field
from datetime import datetime

class RedditPost(BaseModel):
    id: str
    title: str
    content: str
    subreddit: str
    score: int
    created_at: datetime
    url: str = Field(..., description="Full URL to the post")
```

## File Boundaries & Responsibilities

### What to READ when working on features:
- **Reddit integration**: `src/reddit/`, Reddit-related tests
- **LLM features**: `src/llm/`, prompt templates
- **Brand configuration**: `brands/goodpods/`, `src/brand/`
- **Core orchestration**: `src/main.py`, `src/orchestrator.py`
- **Tests**: Always check corresponding test files

### What NOT to read unless specifically needed:
- `documents/project_summary.md` (comprehensive spec - only for major architectural changes)
- Hidden directories (`.git`, `.pytest_cache`, etc.)
- Coverage reports and build artifacts

### When adding new features:
1. Start with tests (TDD approach)
2. Update type hints and docstrings
3. Add proper error handling
4. Update configuration if needed
5. Run full test suite and linting

## Brand Pack System

### Configuration Structure
```yaml
brand_id: "goodpods"
brand_name: "Goodpods - Your Podcast Player"
voice_guidelines: |
  - Helpful and enthusiastic about podcast discovery
  - Knowledgeable but not condescending
  - Natural and conversational, like a fellow podcast lover
allowed_claims:
  - "Free podcast player with social features"
  - "Discover podcasts through friends' recommendations"
cta_links:
  primary: "https://goodpods.app/discover"
  tracking_base: "?utm_source=reddit&utm_medium=comment&utm_campaign=growth_agent"
```

### RAG Integration
- Documents stored in `brands/{brand_id}/knowledge/`
- Future: Vector embeddings for semantic search
- Claim validation against allowed list

## Reddit Compliance

### Platform Rules
- **Account age**: 90+ days required
- **Karma requirements**: 100+ karma minimum
- **Rate limiting**: Max 30 requests/minute
- **Posting frequency**: Max 1 post per subreddit per day
- **Content quality**: Authentic, helpful responses only

### Anti-Detection Measures
- Randomized timing (±15 minutes)
- Natural response variation
- Mix of read/vote/comment activity
- Graceful backoff on rate limits

## Testing Strategy

### Test Organization
```
tests/
├── test_reddit/         # Reddit adapter tests
├── test_llm/           # LLM client tests  
├── test_brand/         # Brand pack tests
├── test_utils/         # Utility tests
└── fixtures/           # Shared test fixtures
```

### Test Categories
- **Unit tests**: Individual functions and classes
- **Integration tests**: Component interactions
- **Reddit tests**: API integration (mocked)
- **LLM tests**: Claude integration (mocked)

### Mocking Strategy
- Mock external APIs in tests
- Use pytest fixtures for common setups
- Test error conditions and edge cases

## Environment Variables

### Required
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`: Reddit API access
- `ANTHROPIC_API_KEY`: Claude API access
- `REDDIT_USERNAME`, `REDDIT_PASSWORD`: Bot account credentials

### Optional
- `LOG_LEVEL`: Logging verbosity (default: INFO)
- `MAX_REPLIES_PER_DAY`: Rate limiting (default: 10)
- `AUTO_POST_THRESHOLD`: Auto-posting score threshold (default: 40)

## Performance Considerations

### Rate Limiting
- Reddit: 30 requests/minute
- Claude: Per API tier limits
- Implement exponential backoff

### Scalability
- Single-threaded execution for MVP
- Brand isolation for multi-brand support

## Security Best Practices

### Credentials
- Never commit API keys or passwords
- Use environment variables for all secrets
- Rotate credentials regularly

### Content Safety
- Validate all claims against allowlist
- Human review for sensitive content
- Audit trail for all actions

## Debugging & Monitoring

### Logging
```python
from loguru import logger

logger.info("Processing post", post_id=post.id, subreddit=post.subreddit)
logger.error("API error", error=str(e), retry_count=retry_count)
```

### Metrics to Track
- Discovery rate (posts found/hour)
- Approval rate (human reviews)
- Engagement metrics (upvotes, clicks)
- Error rates by component

## Development Workflow

### Day-to-Day Development
1. Pull latest changes
2. Create feature branch
3. Write tests first (TDD)
4. Implement feature
5. Run full test suite
6. Submit for review

### Pre-commit Checklist
- [ ] All tests pass
- [ ] Ruff formatting applied
- [ ] MyPy type checking passes
- [ ] No debug prints or TODO comments
- [ ] Updated docstrings if needed

## Common Patterns

### Error Handling
```python
from tenacity import retry, stop_after_attempt
from loguru import logger

@retry(stop=stop_after_attempt(3))
async def api_call() -> ResponseModel:
    try:
        response = await client.request(...)
        return parse_response(response)
    except APIError as e:
        logger.error("API error", error=str(e))
        raise
```

### Configuration Access
```python
from src.utils.config import get_settings

settings = get_settings()
reddit_config = settings.reddit
```

### Testing with Fixtures
```python
@pytest.fixture
def mock_reddit_post():
    return RedditPost(
        id="test123",
        title="Looking for true crime podcasts",
        content="Any recommendations?",
        subreddit="podcasts",
        score=10,
        created_at=datetime.now(),
        url="https://reddit.com/test"
    )

def test_discovery(mock_reddit_post):
    # Test implementation
```

## Future Enhancements

### Planned Features
- Vector database integration for RAG
- Multi-brand concurrent processing
- Advanced metrics dashboard
- A/B testing framework

### Technical Debt
- Currently no vector DB (RAG simplified for MVP)
- Single-threaded processing
- Basic evaluation rubric

## Troubleshooting

### Common Issues
- **Rate limiting**: Check Reddit API usage
- **Authentication errors**: Verify credentials in .env
- **Test failures**: Ensure all dependencies installed
- **Type errors**: Check mypy configuration

### Debug Commands
```bash
# Check configuration
python -c "from src.utils.config import get_settings; print(get_settings())"

# Test Reddit connection
python -c "from src.reddit.adapter import RedditAdapter; print('Reddit OK')"

# Test Claude connection  
python -c "from src.llm.client import ClaudeClient; print('Claude OK')"
```



# Protected Files - DO NOT EDIT

The following files contain sensitive credentials and should NEVER be modified by Claude Code:

## ⛔ NEVER EDIT THESE FILES:
- `.env` - Contains API keys and secrets
- `.env.local`
- `.env.production`
- Any file matching `*.env`

## 🔐 Credentials Policy:
- If you need to reference environment variables, show the user which ones are needed
- NEVER read, modify, or suggest changes to credential files
- If credentials are missing, ask the user to add them manually
- Always use placeholder values in examples (e.g., `YOUR_API_KEY_HERE`)

## ✅ Safe Configuration Changes:
- `src/utils/config.py` - Structure only, not values
- Documentation about required env vars
- Example `.env.example` files with placeholders

---

## Project Status: Foundation Phase

**Current State**: Project structure and tooling setup complete
**Next Steps**: Implement core Reddit discovery and LLM integration
**Target**: MVP with 10+ approved replies/day, <5min review time

Remember: Focus on clean, testable, production-ready code from day 1. No shortcuts!
