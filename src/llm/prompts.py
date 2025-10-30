"""Prompt templates for LLM interactions."""

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

        prompt = f"""You are a helpful podcast enthusiast who loves sharing recommendations.
You're responding to someone looking for podcast suggestions on Reddit.

Brand Context:
{brand_config.voice_guidelines}

Company: {brand_config.brand_name}
Description: {brand_config.company_description}

Allowed Claims (only use these if relevant):
{chr(10).join(f"- {claim}" for claim in brand_config.allowed_claims)}

User Request:
Title: {post.title}
Content: {post.content}
Subreddit: r/{post.subreddit}

{f"Relevant Information: {rag_content}" if rag_content else ""}

Guidelines:
1. Be genuinely helpful first - recommend 1-2 specific podcasts that match their request
2. Keep your response under 100 words
3. Sound like a real podcast fan, not a marketer
4. Only mention the app/service if it naturally fits the conversation
5. Include the tracking link if you mention the service: \
   {brand_config.primary_cta}{brand_config.tracking_params}
6. Don't be pushy or overly promotional
7. Focus on being helpful and authentic

Generate a helpful, natural response:"""

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
        prompt = f"""Score this Reddit comment response on these criteria (0-10 each):

1. RELEVANCE: Does it directly address what they asked for?
2. HELPFULNESS: Does it provide genuine value (specific podcast recommendations)?
3. NATURALNESS: Does it sound like a real podcast fan, not a robot or marketer?
4. BRAND SAFETY: Does it follow guidelines and avoid forbidden topics?
5. CTA SUBTLETY: Is any app/service mention natural and not pushy?

Brand Guidelines:
{brand_config.voice_guidelines}

Forbidden Topics:
{chr(10).join(f"- {topic}" for topic in brand_config.forbidden_topics)}

Original Request:
Title: {original_post.title}
Content: {original_post.content}
Subreddit: r/{original_post.subreddit}

Response to Evaluate:
{response_content}

Provide scores (0-10) and brief reasoning for each criterion:
Relevance: [score] - [reason]
Helpfulness: [score] - [reason] 
Naturalness: [score] - [reason]
Brand Safety: [score] - [reason]
CTA Subtlety: [score] - [reason]"""

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
