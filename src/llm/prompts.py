"""Prompt templates for LLM interactions."""

import random
from typing import Any

from ..models import BrandConfig, RedditPost


class PromptTemplate:
    """Template manager for LLM prompts."""

    @staticmethod
    def create_response_prompt(
        post: RedditPost,
        brand_config: BrandConfig,
        rag_content: str = "",
        context: dict[str, Any] | None = None,
    ) -> str:
        """Create a prompt for generating a response to a Reddit post.

        Args:
            post: Reddit post to respond to
            brand_config: Brand configuration
            rag_content: Retrieved content from RAG system
            context: Additional context information

        Returns:
            Formatted prompt for response generation
        """
        context = context or {}

        # Choose response length variation
        response_lengths = [
            "Keep it VERY brief (1-2 sentences). Be almost too casual.",  # 30%
            "Keep it VERY brief (1-2 sentences). Be almost too casual.",  # 30%
            "Keep it VERY brief (1-2 sentences). Be almost too casual.",  # 30%
            "Keep it concise (3-4 sentences). Direct and helpful.",        # 40%
            "Keep it concise (3-4 sentences). Direct and helpful.",        # 40%
            "Keep it concise (3-4 sentences). Direct and helpful.",        # 40%
            "Keep it concise (3-4 sentences). Direct and helpful.",        # 40%
            "You can be a bit more detailed (4-6 sentences).",            # 30%
            "You can be a bit more detailed (4-6 sentences).",            # 30%
            "You can be a bit more detailed (4-6 sentences).",            # 30%
        ]
        response_length = random.choice(response_lengths)

        # Choose a random persona for variety (simplified to avoid AI tells)
        personas = [
            # Direct Helper
            {
                "intro": "You're a helpful Reddit user who gives direct recommendations.",
                "style": """- Jump straight to recommendations, no story setup
- Be brief and direct
- Use fragments: "perfect for this", "exactly what you want"
- Skip fake framing like "funny story", "ended up", "honestly it's become"
- Personal context: 1 sentence MAX, only if directly relevant""",
                "example": """on the edge with andrew gold. interviews everyone from cult survivors to random people

somewhere in the skies if you like paranormal stuff"""
            },
            # Casual Helper
            {
                "intro": "You're a laid-back Reddit user who happens to know podcasts.",
                "style": """- Start casually: "yeah" "check out" "try" 
- Use fragments and incomplete thoughts
- Include "tbh" "super similar vibe" "scratches that itch"
- Be helpful but not overly structured
- Drop unnecessary modifiers""",
                "example": """yeah on the edge is perfect for this. gets wild guests

been binging it lately, super similar vibe to what you want"""
            },
            # Brief Connector
            {
                "intro": "You relate briefly and give recommendations.",
                "style": """- Start by relating briefly: "been looking for this too" "discovered this last month"
- Keep personal context to absolute minimum
- Focus on recommendations
- Use "scratches that itch" "exactly this" type language
- No elaborate backstories""",
                "example": """discovered on the edge last month and it's all i listen to now lol

exactly what you're looking for - interview format with crazy diverse people"""
            },
            # Ultra Brief
            {
                "intro": "You give ultra-brief, almost lazy recommendations.",
                "style": """- Get straight to the point
- Very short responses
- Skip most context
- Use minimal words: "perfect for this", "exactly this", "check out X"
- Almost too casual""",
                "example": """on the edge with andrew gold. exactly this.

somewhere in the skies for paranormal"""
            }
        ]

        persona = random.choice(personas)
        
        # Decide CTA inclusion (70% include naturally, 30% skip)
        include_cta = random.random() < 0.7
        cta_instruction = f"""- Occasionally mention {brand_config.brand_name} ONLY if it fits naturally
- Use link: {brand_config.primary_cta}{brand_config.tracking_params}
- Make it feel like a genuine tip, not a sales pitch
- Sometimes abbreviate or be casual about it ("on goodpods" instead of "on the Goodpods app")""" if include_cta else "- Don't mention any apps or services this time - just focus on great recommendations"

        # Include RAG context if available
        rag_section = ""
        if rag_content.strip():
            rag_section = f"""
RELEVANT KNOWLEDGE (use naturally when appropriate):
{rag_content}

IMPORTANT: Don't mention this is from knowledge base - present it as your personal experience or general knowledge."""

        prompt = f"""PERSONA: {persona['intro']}

STYLE GUIDELINES:
{persona['style']}

RESPONSE LENGTH: {response_length}

TONE MARKERS TO INCLUDE:
- Use 1-2 of these: tbh, honestly, ngl, imo, actually, literally, basically
- Sometimes start sentences with: and, but, or, so
- Include Reddit-speak when natural: YMMV, ELI5, TIL, IIRC
- Occasionally use "..." for trailing thoughts
- Sometimes use "lol" or "haha" if something's genuinely funny

BRAND CONTEXT (use only if super relevant):
Company: {brand_config.brand_name} - {brand_config.company_description}
{rag_section}

CTA APPROACH:
{cta_instruction}

REDDIT POST TO RESPOND TO:
Title: {post.title}
Content: {post.content}
Subreddit: r/{post.subreddit}

CRITICAL STYLE RULES:
1. Be DIRECT - jump straight to recommendations, skip story setup
2. Be BRIEF - shorter is more natural, don't over-explain
3. Be LOOSE - fragments, incomplete thoughts, casual structure
4. Skip fake framing like "funny story", "ended up", "honestly it's become"
5. Personal context: 1 sentence MAX, only if directly relevant
6. Don't over-describe: "interviews everyone" not "interviews everyone from X to Y to Z"
7. Use Reddit patterns: "perfect for this", "exactly what you want", "super similar vibe"
8. If you mention the app, make it feel like a genuine user tip

EXAMPLE OF GOOD TONE:
"{persona['example']}"

Now write a response that sounds like a real Reddit user. Be helpful but human:"""

        return prompt

    @staticmethod
    def create_evaluation_prompt(
        response_content: str,
        original_post: RedditPost,
        brand_config: BrandConfig,
    ) -> str:
        """Create a prompt for evaluating a generated response.

        Args:
            response_content: Response to evaluate
            original_post: Original Reddit post
            brand_config: Brand configuration

        Returns:
            Formatted evaluation prompt
        """
        prompt = f"""Score this Reddit comment on how human and helpful it sounds (0-10 each):

1. RELEVANCE: Does it actually answer what they asked?
2. HELPFULNESS: Are the recommendations specific and useful?
3. NATURALNESS: Does it sound like a real Reddit user or like ChatGPT?
4. BRAND SAFETY: Is it following guidelines without being corporate?
5. CTA SUBTLETY: If the app is mentioned, does it feel natural or forced?

Original Post:
Title: {original_post.title}
Content: {original_post.content}

Response:
{response_content}

Good responses sound like:
- "oh man if you loved Serial..." 
- "honestly been there..."
- "ngl this one saved my commute..."

Bad responses sound like:
- "I'd be happy to help you find..."
- "Here are some excellent recommendations..."
- "Thank you for your question..."

Score Format:
Relevance: [0-10] - [short reason]
Helpfulness: [0-10] - [short reason]
Naturalness: [0-10] - [short reason]
Brand Safety: [0-10] - [short reason]
CTA Subtlety: [0-10] - [short reason]"""

        return prompt

    @staticmethod
    def create_claim_validation_prompt(
        claim: str,
        brand_config: BrandConfig,
    ) -> str:
        """Create a prompt for validating claims against brand guidelines.

        Args:
            claim: Claim to validate
            brand_config: Brand configuration

        Returns:
            Formatted validation prompt
        """
        prompt = f"""Is this claim appropriate for {brand_config.brand_name}?

Claim to validate: "{claim}"

Allowed claims for this brand:
{chr(10).join(f"- {allowed_claim}" for allowed_claim in brand_config.allowed_claims)}

Forbidden topics:
{chr(10).join(f"- {topic}" for topic in brand_config.forbidden_topics)}

Rules:
1. The claim must be factually accurate
2. It must align with allowed claims or be very similar
3. It must not touch on forbidden topics
4. It should match the brand voice

Respond with: APPROVED or REJECTED
If REJECTED, explain why in one sentence."""

        return prompt

    @staticmethod
    def create_intent_classification_prompt(post: RedditPost) -> str:
        """Create a prompt for classifying post intent.

        Args:
            post: Reddit post to classify

        Returns:
            Formatted intent classification prompt
        """
        prompt = f"""Classify the intent of this Reddit post:

Title: {post.title}
Content: {post.content}
Subreddit: r/{post.subreddit}

Intent categories:
- recommendation_request: Looking for podcast suggestions
- comparison_request: Comparing different podcasts/apps
- technical_help: Asking about podcast technical issues
- promotion: Promoting their own podcast
- discussion: General podcast discussion
- off_topic: Not related to podcasts

Respond with just the category name that best matches."""

        return prompt

    @staticmethod
    def create_rag_query_prompt(post: RedditPost, context: dict[str, Any]) -> str:
        """Create a query for RAG retrieval based on post content.

        Args:
            post: Reddit post
            context: Additional context from analysis

        Returns:
            Query string for RAG retrieval
        """
        # Extract key terms from the post for RAG search
        topic = context.get("topic", "general")
        genre = context.get("genre", "")

        query_parts = [post.title, post.content]

        if topic != "general":
            query_parts.append(f"{topic} podcasts")

        if genre:
            query_parts.append(f"{genre} podcast recommendations")

        # Combine and clean up the query
        query = " ".join(query_parts)

        # Remove common stop words and Reddit-specific terms
        stop_words = ["looking", "for", "any", "some", "need", "want", "please", "help", "reddit"]
        query_words = [word for word in query.split() if word.lower() not in stop_words]

        return " ".join(query_words[:20])  # Limit query length