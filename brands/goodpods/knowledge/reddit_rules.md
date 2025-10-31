# Reddit Anti-Spam Rules (Critical for Account Safety)

## Hard Rules (Break These = Ban)

### 1. 10% Self-Promotion Rule
- **Rule**: Max 10% of activity can be self-promotional
- **Implementation**: For every 1 Goodpods mention, make 9 non-promotional comments
- **Action**: Bot should also post helpful non-promotional responses

### 2. No Automated Activity
- **Rule**: Reddit prohibits bots without disclosure
- **Gray Area**: Human-approved responses are technically not "automated"
- **Safety**: Always have human review before posting

### 3. Authentic Participation Required
- **Rule**: Must be genuine community member, not just marketing
- **Implementation**: 
  - Vote on other posts
  - Comment on non-targeted threads occasionally
  - Read rules of each subreddit before posting

### 4. Subreddit-Specific Rules

#### r/podcasts Rules:
- No podcast promotion (we're recommending, not promoting podcasts)
- No spam or excessive self-promotion
- Be helpful and genuine
- Search before posting duplicate recommendations

#### r/TrueCrimePodcasts Rules:
- Stay on topic
- No self-promotion without mod approval
- Be respectful

## Detection Patterns to Avoid

### 🚫 Red Flags:
- Same link posted repeatedly
- Identical response patterns
- Posting within seconds of post creation
- Only commenting on brand-relevant topics
- No upvoting/downvoting activity
- Perfect grammar/structure every time

### ✅ Safe Patterns:
- Varied response times (wait 15min-2hours)
- Mixed activities (upvote, read, comment on other topics)
- Natural language variation
- Sometimes skip mentioning Goodpods entirely
- Occasional typos or casual errors
- Engage in follow-up discussions

## Implementation Requirements

### Account Warming (Before Going Live):
1. **Week 1**: Lurk, upvote posts, no commenting
2. **Week 2**: Comment on 5-10 non-target posts (general helpfulness)
3. **Week 3**: First promotional mention (1 in 10 comments)
4. **Week 4+**: Maintain 10% ratio

### Posting Cadence:
- **Max**: 3 responses per day
- **Spacing**: Minimum 2 hours between posts
- **Randomization**: ±30min on all timing
- **Peak times**: Avoid posting exactly on the hour

### Link Strategy:
- **Frequency**: Include Goodpods link in only 40% of responses
- **Variation**: Sometimes mention without linking
- **Natural**: "I use Goodpods" vs always including URL

### Response Variation:
- **Length**: Vary from 1 sentence to 6 sentences
- **Tone**: Use different personas
- **Mistakes**: Occasionally include typos, lowercase starts
- **Timing**: Some responses instant, some hours later

## Safety Checklist (Before Each Post)

- [ ] Account has posted 9 non-promotional comments recently
- [ ] Last Goodpods mention was >24 hours ago
- [ ] Response sounds genuinely human
- [ ] Timing is randomized (not on the hour)
- [ ] Not responding to own previous comments
- [ ] Subreddit rules checked and followed

## Emergency Protocols

### If You Get:

**Shadow Banned:**
- Stop all activity immediately
- Check: post to r/ShadowBan to confirm
- Wait 30 days before resuming
- Review all activity for rule violations

**Subreddit Banned:**
- Respect the ban, don't circumvent
- Review subreddit rules
- Contact mods if genuine mistake
- Move to different subreddits

**Warnings from Mods:**
- Stop immediately
- Apologize professionally  
- Reduce frequency
- Ensure 10% rule compliance

## Monitoring

Daily checks:
- Is account still able to post?
- Any comments removed by mods?
- Karma trending up or down?
- Any warning messages?
```

---

## 🏗️ Project Entry Points & Deployment

### Current Entry Points:
```
scripts/demo_discovery.py     # Demo mode (what you're running)
scripts/index_brand_knowledge.py  # One-time RAG indexing
