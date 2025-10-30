# Goodpods Reddit Growth Agent MVP
## Project Documentation & Implementation Guide

**Project Name:** Goodpods Reddit Growth Agent  
**Document Version:** 1.0  
**Last Updated:** October 29, 2025  
**Project Status:** Pre-Development  
**Document Purpose:** Comprehensive guide for building a reusable growth agent for Reddit engagement

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Project Overview](#project-overview)
3. [Architecture Design](#architecture-design)
4. [Implementation Phases](#implementation-phases)
5. [Technical Specifications](#technical-specifications)
6. [Brand Pack Configuration](#brand-pack-configuration)
7. [Reddit Integration Strategy](#reddit-integration-strategy)
8. [Prompting & Evaluation Framework](#prompting-evaluation-framework)
9. [Metrics & Success Tracking](#metrics-success-tracking)
10. [Risk Management](#risk-management)
11. [Quick Start Guide](#quick-start-guide)
12. [Appendices](#appendices)

---

## 1. Executive Summary

### The Problem
Goodpods needs scalable, authentic engagement on Reddit to grow their podcast player user base, but manual outreach is time-intensive and difficult to scale while maintaining brand consistency.

### The Solution
A reusable growth agent that:
- Discovers relevant podcast recommendation requests on Reddit
- Generates brand-aligned responses using RAG (Retrieval-Augmented Generation)
- Engages users with optional human review
- Maintains per-brand isolation for future scalability

### MVP Scope
- **Single Channel:** Reddit comment replies
- **Single Intent:** "Podcast recommendation requests" (e.g., "looking for a podcast about true crime")
- **Execution:** Single-threaded with LLM evaluation and manual approval workflow
- **Target:** 10+ approved replies/day with <5 min human review time

### Success Criteria
✓ >5% click-through rate on shared links  
✓ Zero platform violations in first 30 days  
✓ <$50/day operational cost  
✓ System reusable for future brands via Brand Pack swapping

---

## 2. Project Overview

### Project Metadata
- **Team Size:** 1 person + LLMs
- **Timeline:** 2 weeks to MVP
- **Budget:** <$1/day operational costs
- **Tech Stack:** TBD based on vendor evaluation

### Core Principles
1. **Minimal Complexity:** Start with the smallest viable slice
2. **Brand Isolation:** No cross-brand data leakage
3. **Platform Compliance:** Strict adherence to Reddit rules
4. **Human-in-the-Loop:** Optional review for quality control
5. **Reusability:** Generic system with swappable Brand Packs

### What's In Scope (MVP)
- Reddit API integration for discovery and posting
- Single-intent detection: podcast recommendations
- RAG-powered response generation
- Basic evaluation and routing logic
- Manual review interface
- Simple metrics tracking

### What's Out of Scope (Deferred)
- Other platforms (Twitter/X, LinkedIn, Discord)
- Multiple intent types
- Auto-scheduling or rate optimization
- A/B testing framework
- Multi-brand concurrent processing
- Advanced analytics
- Automated account management

---

## 3. Architecture Design

### System Components

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

### Component Responsibilities

#### Brand Pack
- Stores brand-specific configuration
- Contains voice guidelines and allowed claims
- Houses documentation for RAG indexing
- Defines CTA links and tracking parameters

#### Orchestrator
- Main execution loop
- Coordinates between components
- Manages state and workflow
- Handles error recovery

#### Reddit Adapter
- Wraps Reddit API functionality
- Handles authentication and rate limiting
- Provides abstraction for future channel additions
- Manages post/comment interactions

#### Evaluator
- Scores draft quality against rubric
- Determines routing (auto-post vs review)
- Logs decisions for analysis
- Provides feedback for improvement

### Data Flow
1. **Discovery:** Reddit Adapter searches for matching posts
2. **Context Building:** Orchestrator gathers post context
3. **RAG Lookup:** Relevant brand content retrieved
4. **Draft Generation:** LLM creates response using template
5. **Evaluation:** Scorer assesses quality and safety
6. **Routing:** Decision on auto-post vs human review
7. **Action:** Post reply or queue for review
8. **Tracking:** Log all actions and outcomes

### Data Isolation Strategy
- Each Brand Pack in isolated namespace: `brands/{brand_id}/`
- RAG indices partitioned by brand_id
- Separate Reddit credentials per brand
- Audit logs include brand_id on every operation
- No shared state between brand executions

---

## 4. Implementation Phases

### Phase 1: Foundation Setup (Week 1-2)

#### Tasks & Deliverables

| Task | Description | Effort | Output |
|------|-------------|--------|--------|
| Reddit API Setup | Configure auth, test endpoints | Small | Working API client |
| Brand Pack Schema | Design JSON/YAML structure | Small | Schema v1.0 |
| RAG Pipeline | Vector DB setup, indexing | Medium | Indexing script |
| Discovery Queries | Reddit search templates | Small | Query patterns |
| Response Prompts | Initial prompt engineering | Medium | Prompt templates |

#### Technical Decisions
- [ ] Vector DB selection (Pinecone vs Weaviate vs Qdrant)
- [ ] Embedding model (OpenAI vs Cohere vs open-source)
- [ ] LLM provider (OpenAI vs Anthropic vs Google)
- [ ] Infrastructure (AWS vs GCP vs Vercel)

### Phase 2: MVP Build (Week 3-4)

#### Core Development

| Component | Tasks | Dependencies |
|-----------|-------|--------------|
| Orchestrator | Main loop, state management | All Phase 1 |
| Evaluator | Rubric implementation, scoring | Response prompts |
| Review UI | Simple web interface | None |
| Logging | Structured logs, storage | Infrastructure |
| Brand Setup | Goodpods configuration | All components |

#### Integration Points
- Reddit API ↔ Orchestrator
- RAG System ↔ Orchestrator
- Evaluator ↔ Human Review UI
- All Components → Logging System

### Phase 3: Pilot & Iteration (Week 5-6)

#### Pilot Execution
1. **Soft Launch:** 3-5 replies/day
2. **Monitoring:** Track all metrics
3. **Feedback Loop:** Daily reviews
4. **Tuning:** Adjust prompts and thresholds
5. **Scale Up:** Gradually increase volume

#### Success Metrics
- 50 total replies attempted
- <20% rejection rate
- >5% CTR achieved
- Zero platform violations
- <5 min average review time

---

## 5. Technical Specifications

### Minimal Interfaces

```python
# Reddit Adapter Interface
class RedditAdapter:
    def discover_posts(self, query: str, subreddits: List[str], 
                      limit: int = 20) -> List[RedditPost]
    def post_reply(self, post_id: str, content: str) -> ReplyResult
    def get_metrics(self, reply_id: str) -> RedditMetrics
    def check_karma_requirements(self, subreddit: str) -> bool

# RAG Interface  
class BrandRAG:
    def index_documents(self, brand_id: str, documents: List[Document]) -> None
    def search(self, query: str, brand_id: str, k: int = 5) -> List[chunk]
    def validate_claim(self, claim: str, brand_id: str) -> bool

# Evaluator Interface
class ReplyEvaluator:
    def score(self, draft: str, context: Dict) -> EvalResult
    def should_auto_post(self, result: EvalResult) -> bool
    def get_feedback(self, result: EvalResult) -> str

# Orchestrator Interface
class GrowthOrchestrator:
    def run_discovery_cycle(self, brand_id: str) -> List[Opportunity]
    def process_opportunity(self, opp: Opportunity) -> ProcessResult
    def handle_review_decision(self, draft_id: str, approved: bool) -> None
```

### Configuration Schema

```yaml
# config.yaml
system:
  max_replies_per_day: 10
  discovery_interval_minutes: 30
  review_timeout_hours: 24
  
reddit:
  user_agent: "GrowthAgent/1.0"
  rate_limit_per_minute: 30
  min_karma_required: 100
  account_age_days: 90

evaluation:
  auto_post_threshold: 35
  human_review_threshold: 25
  reject_threshold: 25
  
logging:
  level: INFO
  retention_days: 90
  
llm:
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 200
```

### Error Handling Strategy
- **Graceful Degradation:** Continue operation on non-critical failures
- **Exponential Backoff:** For API rate limits
- **Dead Letter Queue:** For failed processing attempts
- **Health Checks:** Monitor component availability
- **Alert Thresholds:** Notify on critical errors

---

## 6. Brand Pack Configuration

### Goodpods Brand Pack v1.0

```yaml
brand_id: "goodpods"
brand_name: "Goodpods - Your Podcast Player"
company_description: |
  Goodpods is a social podcast player that helps you discover 
  amazing shows through friends and curated recommendations.
  
voice_guidelines: |
  - Helpful and enthusiastic about podcast discovery
  - Knowledgeable but not condescending
  - Focus on the listening experience, not just the app
  - Use "we" sparingly, prefer "you" focused language
  - Natural and conversational, like a fellow podcast lover
  
tone_attributes:
  - Friendly
  - Authentic
  - Passionate about podcasts
  - Community-oriented
  
allowed_claims:
  - "Free podcast player with social features"
  - "Discover podcasts through friends' recommendations"
  - "Available on iOS and Android"
  - "No ads in the app experience"
  - "Curated podcast collections"
  - "Easy import from other podcast apps"
  
forbidden_topics:
  - Direct competitor comparisons
  - Specific user numbers or growth metrics
  - Technical implementation details
  - Monetization or business model
  - Future features not yet released
  
response_templates:
  recommendation_request: |
    {acknowledgment} For {topic} podcasts, {personal_recommendation}. 
    {relevant_feature} {soft_cta}
    
example_responses:
  - |
    True crime is such a great genre! Based on what you're describing, 
    you might enjoy "Criminal" or "Someone Knows Something". If you're 
    looking for a way to organize your true crime podcasts and get 
    recommendations from other fans, Goodpods has curated collections 
    that might help: goodpods.app/discover
    
documents:
  - filename: "podcast_categories.md"
    description: "List of podcast categories and popular shows"
  - filename: "app_features.md"
    description: "Core features and benefits"
  - filename: "user_testimonials.md"
    description: "Real user feedback and use cases"
    
cta_links:
  primary: "https://goodpods.app/discover"
  tracking_base: "?utm_source=reddit&utm_medium=comment&utm_campaign=growth_agent"
  
subreddits:
  tier_1:
    - "r/podcasts"
    - "r/podcast"
    - "r/podcasting"
  tier_2:
    - "r/TrueCrimePodcasts"
    - "r/HistoryPodcasting"
    - "r/ComedyPodcasts"
  tier_3:
    - "r/PodcastAddict"
    - "r/AudioDrama"
    - "r/podcastsuggestions"
```

### Brand Pack Validation Rules
1. **Required Fields:** All top-level fields must be present
2. **Claim Validation:** Each claim must be factual and verifiable
3. **Link Validation:** All CTAs must use approved domain
4. **Document Check:** All referenced files must exist
5. **Tone Consistency:** Examples must match voice guidelines

### Brand Pack Management
- **Storage:** Isolated S3 bucket or GCS folder
- **Versioning:** Git-based version control
- **Updates:** Weekly review and refresh
- **Testing:** Validation suite before deployment
- **Backup:** Daily snapshots retained for 30 days

---

## 7. Reddit Integration Strategy

### Platform Compliance Framework

#### Reddit Rules Adherence
- **Account Requirements:** 90+ day age, 100+ karma
- **Posting Frequency:** Max 1 post per subreddit per day
- **Engagement Pattern:** Vary timing, natural activity
- **Content Policy:** No spam, authentic contribution
- **Disclosure:** Subtle but present when appropriate

#### Discovery Strategy

```python
# Primary Discovery Query
base_query = '(title:"looking for" OR title:"recommend" OR title:"suggestions" OR title:"need") AND (selftext:"podcast" OR title:"podcast")'

# Refined Patterns
intent_patterns = [
    "looking for .* podcast",
    "recommend .* podcast", 
    "any .* podcast suggestions",
    "need a podcast about",
    "best podcast for",
    "podcast recommendations for"
]

# Exclusion Patterns  
exclude_patterns = [
    "how to start a podcast",
    "podcast equipment",
    "podcast hosting",
    "promote my podcast"
]
```

### Subreddit Strategy

#### Tier 1: Primary Targets (High Intent)
- **r/podcasts** (500k members): General recommendations
- **r/podcast** (50k members): Discovery focused
- **r/podcasting** (150k members): Mixed audience

#### Tier 2: Genre Specific (Medium Volume)
- **r/TrueCrimePodcasts**: Genre enthusiasts
- **r/HistoryPodcasting**: Niche interests
- **r/ComedyPodcasts**: Entertainment seekers

#### Tier 3: Extended Reach (Lower Priority)
- Various genre-specific communities
- General interest subreddits with podcast discussions

### Anti-Detection Measures
1. **Account Warming:** Gradual activity increase
2. **Behavioral Variety:** Mix read/vote/comment
3. **Time Randomization:** ±15 min on all actions  
4. **Content Diversity:** Vary response structures
5. **Failure Handling:** Back off on rate limits

---

## 8. Prompting & Evaluation Framework

### Response Generation Strategy

#### System Prompt Template
```
You are a helpful podcast enthusiast who loves sharing recommendations.
You're responding to someone looking for podcast suggestions on Reddit.

Brand Context:
{brand_voice_guidelines}

User Request:
{reddit_post_title}
{reddit_post_body}

Relevant Information:
{rag_retrieved_content}

Guidelines:
1. Be genuinely helpful first - recommend 1-2 specific podcasts
2. Naturally mention how our app helps with discovery if relevant  
3. Keep response under 100 words
4. Sound like a real person, not a marketer
5. Only use claims from the allowed list
6. Include tracking link if appropriate

Generate a helpful response:
```

#### Response Structure Pattern
```
[Acknowledge Interest] + [Specific Recommendations] + 
[Relevant App Feature] + [Soft CTA]
```

#### Example Outputs
✅ **Good Response:**
> "Oh, true crime podcasts are my favorite! For something really gripping, try 'Bear Brook' - it's an incredible investigative series. 'Criminal' is also fantastic for shorter episodes. I actually organize all my true crime shows in collections on Goodpods, makes it easy to keep track of new episodes: goodpods.app/discover"

❌ **Bad Response:**
> "Hi! You should download Goodpods - it's the best podcast app with social features and no ads! We have millions of podcasts and you can follow your friends. Get it now at goodpods.app!"

### Evaluation Rubric

```python
class EvaluationCriteria:
    relevance_score: int       # 0-10: How well it matches request
    helpfulness_score: int     # 0-10: Genuine value provided
    naturalness_score: int     # 0-10: Sounds human, not robotic
    brand_safety_score: int    # 0-10: Follows guidelines
    cta_subtlety_score: int    # 0-10: Not pushy or salesy
    
    @property
    def total_score(self) -> int:
        return sum([
            self.relevance_score,
            self.helpfulness_score,
            self.naturalness_score,
            self.brand_safety_score,
            self.cta_subtlety_score
        ])

# Routing Thresholds
AUTO_POST_THRESHOLD = 40/50
HUMAN_REVIEW_THRESHOLD = 30/50  
REJECT_THRESHOLD = 30/50
```

### Evaluation Prompt
```
Score this Reddit comment response on these criteria (0-10 each):

1. RELEVANCE: Does it directly address what they asked for?
2. HELPFULNESS: Does it provide genuine value (specific podcasts)?
3. NATURALNESS: Does it sound like a real podcast fan?
4. BRAND SAFETY: Does it follow guidelines and avoid forbidden topics?
5. CTA SUBTLETY: Is the app mention natural and not salesy?

Response to evaluate:
{draft_response}

Original request:
{reddit_post}

Provide scores and brief reasoning for each.
```

### Human Review Interface

#### Review Dashboard Components
- **Queue View:** Pending drafts with context
- **Original Post:** Full Reddit thread display
- **Draft Response:** Proposed reply with scoring
- **Edit Capability:** Modify before approval
- **Quick Actions:** Approve/Reject/Skip buttons
- **Feedback Notes:** Optional reviewer comments

#### Review Workflow
1. Reviewer sees post context and draft
2. Can edit response if needed
3. Approves/rejects with optional note
4. System logs decision and feedback
5. Approved posts go live immediately
6. Rejections feed back to improvement

---

## 9. Metrics & Success Tracking

### Key Performance Indicators

#### Engagement Metrics
- **Reply Rate:** Approved replies / opportunities found
- **Approval Rate:** Human approvals / reviews
- **Response Time:** Discovery to posting
- **Engagement Score:** (Upvotes - Downvotes) / Views
- **CTR:** Clicks on CTA / Reply views

#### Quality Metrics  
- **Violation Rate:** Platform warnings / total posts
- **Edit Rate:** Edited replies / approved replies
- **Evaluation Accuracy:** Auto-post success rate
- **Sentiment Score:** Community response analysis

#### Business Metrics
- **Traffic Generated:** Unique visitors from Reddit
- **Conversion Rate:** Signups / Reddit visitors  
- **CAC:** Total cost / new users acquired
- **Attribution:** Multi-touch tracking

### Logging Schema

```json
{
  "event_id": "evt_1234567890",
  "timestamp": "2025-01-15T10:30:00Z",
  "brand_id": "goodpods",
  "campaign_id": "reddit_podcast_recs_mvp",
  
  "discovery": {
    "post_id": "t3_abc123",
    "subreddit": "r/podcasts",
    "post_url": "https://reddit.com/r/podcasts/...",
    "matched_pattern": "looking for true crime podcast",
    "post_score": 45,
    "comment_count": 12
  },
  
  "generation": {
    "draft_id": "draft_xyz789",
    "model": "gpt-4",
    "prompt_template": "v1.2",
    "rag_chunks_used": 3,
    "generation_time_ms": 1847
  },
  
  "evaluation": {
    "relevance": 8,
    "helpfulness": 9,
    "naturalness": 8,
    "brand_safety": 10,
    "cta_subtlety": 7,
    "total_score": 42,
    "routing_decision": "auto_post"
  },
  
  "action": {
    "type": "posted",
    "reply_id": "t1_def456",
    "reply_url": "https://reddit.com/r/podcasts/.../def456",
    "reviewer_id": null,
    "review_time_ms": null,
    "edits_made": false
  },
  
  "outcomes": {
    "clicks_1h": 2,
    "clicks_24h": 8,
    "upvotes_24h": 5,
    "downvotes_24h": 0,
    "replies_received": 1,
    "conversions": 1
  }
}
```

### Analytics Dashboard

#### Real-time Metrics (Updated hourly)
- Active drafts in queue
- Posts last 24h
- Current approval rate
- Live CTR tracking

#### Daily Reports
- Total opportunities found
- Posts attempted/approved
- Engagement summary
- Top performing content

#### Weekly Analysis
- Trend analysis
- Subreddit performance
- Prompt effectiveness
- ROI calculation

### Attribution Flow
1. **Link Generation:** Unique UTM per post
2. **Click Tracking:** Server-side redirect
3. **Session Creation:** Tag Reddit visitors
4. **Event Tracking:** Onboarding funnel
5. **LTV Analysis:** Cohort tracking

---

## 10. Risk Management

### Risk Matrix

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|-------------------|
| Reddit shadowban | Medium | High | Start slow, aged accounts, natural behavior |
| Hallucinated claims | Low | High | Strict RAG validation, claims allowlist |
| Brand voice drift | Medium | Medium | Regular audits, consistent templates |
| API rate limits | High | Low | Exponential backoff, queue management |
| Poor CTR | Medium | Medium | A/B testing, continuous optimization |
| Negative sentiment | Low | High | Quick response protocol, monitoring |
| Cost overrun | Low | Medium | Daily spend limits, alerting |

### Mitigation Protocols

#### Platform Compliance
1. **Account Health:** Daily karma/status checks
2. **Behavior Patterns:** Randomization algorithms
3. **Content Review:** Weekly audit sample
4. **Relationship Building:** Occasional non-promotional activity

#### Brand Safety  
1. **Claim Validation:** Pre-generation allowlist check
2. **Tone Monitoring:** Sample evaluation by humans
3. **Response Caching:** Prevent regeneration loops
4. **Escalation Path:** Alert on negative responses

#### Technical Reliability
1. **Circuit Breakers:** Prevent cascade failures
2. **Retry Logic:** Handle transient errors
3. **Fallback Models:** Backup LLM providers
4. **Data Backups:** Hourly snapshots

### Incident Response Plan

#### Severity Levels
- **P0:** Platform ban, data breach
- **P1:** Service down, mass failures
- **P2:** Degraded performance, high errors
- **P3:** Minor issues, optimization needs

#### Response Protocol
1. **Detect:** Automated alerting
2. **Assess:** Determine severity
3. **Communicate:** Notify stakeholders  
4. **Mitigate:** Execute runbook
5. **Review:** Post-mortem analysis

---

## 11. Quick Start Guide

### Prerequisites
- [ ] Reddit account (90+ days old, 100+ karma)
- [ ] API keys (Reddit, OpenAI/Anthropic, Vector DB)
- [ ] Cloud infrastructure access
- [ ] Basic Python/Node.js environment

### Day 1: Environment Setup
```bash
# Clone repository
git clone [repo-url]
cd goodpods-growth-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Test connections
python scripts/test_connections.py
```

### Day 2: Brand Pack Setup
```bash
# Validate brand pack
python scripts/validate_brand_pack.py brands/goodpods/

# Index documents for RAG
python scripts/index_documents.py --brand goodpods

# Test RAG retrieval
python scripts/test_rag.py --query "true crime podcasts"
```

### Day 3: First Discovery Run
```bash
# Run discovery in dry-run mode
python main.py --mode discover --dry-run

# Review found opportunities
python scripts/review_opportunities.py

# Generate test responses
python main.py --mode generate --limit 5
```

### Day 4: Launch Pilot
```bash
# Start orchestrator
python main.py --mode pilot --replies-per-day 3

# Monitor via dashboard
python dashboard/app.py

# Review and approve drafts
# Access http://localhost:8080/review
```

### Daily Operations Checklist
- [ ] Check account health
- [ ] Review overnight drafts
- [ ] Monitor engagement metrics
- [ ] Scan for negative responses
- [ ] Update opportunity queue
- [ ] Check error logs

### Weekly Maintenance
- [ ] Analyze performance metrics
- [ ] Update Brand Pack content
- [ ] Refine prompts based on feedback
- [ ] Review and categorize errors
- [ ] Plan optimization experiments

---

## 12. Appendices

### A. Vendor Comparison Matrix

| Service | Option 1 | Option 2 | Option 3 | Recommendation |
|---------|----------|----------|----------|----------------|
| **LLM Provider** | OpenAI GPT-4 | Anthropic Claude | Google Gemini | Anthropic (quality) |
| **Vector DB** | Pinecone | Weaviate | Qdrant | Pinecone (ease) |
| **Infrastructure** | AWS | GCP | Vercel | Vercel (simplicity) |
| **Monitoring** | Datadog | New Relic | Custom | Custom (cost) |
| **Queue System** | SQS | Redis | RabbitMQ | Redis (flexibility) |

### B. Cost Projections

#### Monthly Estimates (100 replies/day)
- **LLM Costs:** $300-500
- **Vector DB:** $50-100  
- **Infrastructure:** $100-200
- **Reddit API:** Free
- **Monitoring:** $50-100
- **Total:** $500-900/month

#### Cost Optimization Strategies
1. Cache common responses
2. Batch API calls
3. Use smaller models for evaluation
4. Optimize RAG chunk size
5. Schedule during off-peak hours

### C. Expansion Roadmap

#### Phase 4: Multi-Intent (Month 2)
- Add "podcast app comparison" intent
- Add "podcast discovery help" intent
- Refine routing logic

#### Phase 5: Platform Expansion (Month 3)
- Twitter/X integration
- Discord bot version
- LinkedIn presence

#### Phase 6: Advanced Features (Month 4+)
- Multi-brand concurrent processing
- A/B testing framework
- Automated optimization
- Sentiment-based routing
- Conversation threading

### D. Example Interactions

#### Success Case #1
**Post:** "Looking for history podcasts similar to Dan Carlin"  
**Response:** "If you love Dan Carlin's style, definitely check out 'Revolutions' by Mike Duncan - similar deep dives into historical events. 'Our Fake History' is another great one that examines historical myths. I keep all my history podcasts organized in Goodpods, makes it easy to track those long series: goodpods.app/discover"  
**Result:** 12 upvotes, 3 clicks, 1 signup

#### Success Case #2
**Post:** "Need podcast recs for my daily commute"  
**Response:** "For commutes, I love shows with 20-30 min episodes! 'Planet Money' and 'The Daily' are perfect for staying informed. '99% Invisible' is great for interesting stories about design. What's your commute length? Happy to suggest more specific ones!"  
**Result:** Engaged conversation, natural CTA opportunity in follow-up

### E. Troubleshooting Guide

#### Common Issues & Solutions

**Issue:** Low discovery rate  
**Solution:** Expand search patterns, add more subreddits

**Issue:** High rejection rate  
**Solution:** Review failed drafts, adjust prompts

**Issue:** Reddit rate limiting  
**Solution:** Reduce frequency, check rate limit headers

**Issue:** Poor CTR  
**Solution:** Make CTA more relevant, improve targeting

**Issue:** Negative responses  
**Solution:** Review tone, ensure genuine helpfulness

### F. Templates & Resources

#### Review Decision Template
```
Draft ID: {draft_id}
Decision: APPROVED / REJECTED / EDITED
Reason: {brief explanation}
Suggested Improvement: {if rejected}
```

#### Weekly Report Template  
```
Week of: {date}
Total Opportunities: {n}
Replies Posted: {n}
Average CTR: {n}%
Top Performing Subreddit: {name}
Key Learning: {insight}
Next Week Focus: {priority}
```

---

## Document Control

### Version History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-29 | AI Assistant | Initial comprehensive documentation |

### Review Schedule
- **Weekly:** Metrics and performance
- **Bi-weekly:** Prompt effectiveness
- **Monthly:** Full system review
- **Quarterly:** Strategic alignment

### Feedback & Updates
- Submit issues via GitHub
- Weekly team syncs for updates
- Document updates require approval
- All changes tracked in version control

---

## Contact & Support

**Project Owner:** [Your Name]  
**Technical Lead:** [Your Name]  
**Documentation Maintained By:** [Your Name]

For questions, updates, or access requests, please reach out via the project Slack channel or GitHub issues.

---

*This is a living document. Please ensure you're working with the latest version.*
