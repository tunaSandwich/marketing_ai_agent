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

        # Parse what user already mentioned to avoid duplicates
        mentioned_podcasts = []
        post_text = (post.title + " " + post.content).lower()
        
        # Common podcast names to check for duplicates
        known_podcasts = ["serial", "criminal", "bear brook", "this american life", 
                          "radiolab", "99% invisible", "hidden brain", "science vs",
                          "casefile", "my favorite murder", "reply all", "planet money",
                          "freakonomics", "stuff you should know", "conan o'brien needs a friend",
                          "joe rogan", "ted talks", "the daily", "up first", "npr news now"]
        
        for podcast in known_podcasts:
            if podcast in post_text:
                mentioned_podcasts.append(podcast)

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

        # Simplified personas focused on extreme brevity
        personas = [
            {
                "name": "brief",
                "intro": "you give very short podcast recommendations",
                "style": "super brief, 1-2 podcasts max, no fluff, all lowercase",
                "examples": [
                    "try criminal for short episodes, bear brook for deep dives",
                    "in the dark season 2 is incredible",
                    "criminal and teacher's pet are both great"
                ]
            },
            {
                "name": "direct", 
                "intro": "you recommend podcasts directly",
                "style": "straight to the point, 1-2 names only, lowercase",
                "examples": [
                    "criminal and bear brook",
                    "try your own backyard",
                    "casefile for international true crime"
                ]
            },
            {
                "name": "minimal",
                "intro": "you give minimal recommendations",
                "style": "ultra minimal, just names and brief reason",
                "examples": [
                    "bear brook - cold case deep dive",
                    "criminal - short true crime stories",
                    "in the dark season 2"
                ]
            }
        ]

        # Check if we should skip brand mentions (warming mode)
        skip_brand = context.get("skip_brand", False)
        
        # For warming mode, never mention brands
        if skip_brand or context.get("mode") == "helpful":
            include_cta = False
        else:
            # 70% chance to include brand naturally for promotional
            include_cta = random.random() < 0.7
        
        # Include RAG context if available
        knowledge_section = ""
        if rag_content.strip():
            knowledge_section = f"\nKnowledge: {rag_content}"
        
        # Add context section if user mentioned specific podcasts
        context_section = ""
        if mentioned_podcasts:
            context_section = f"\nIMPORTANT: User already mentioned: {', '.join(mentioned_podcasts)} - recommend DIFFERENT podcasts!\n"
        
        # Add brand guidance for promotional mode
        brand_section = ""
        if include_cta and brand_config.brand_name:
            brand_section = f"\nMention {brand_config.brand_name} personally (like 'i use {brand_config.brand_name}...')"
        
        prompt = f"""STRICT RULES:
1. Maximum 150 characters TOTAL (this is about 25-30 words)
2. Recommend exactly 1-2 podcasts, NO MORE
3. No introductions, no "oh man", no "i love", just recommendations
4. All lowercase, no exclamation points
5. Be complete but brief
6. DO NOT include character counts, metadata, or formatting markers

GOOD EXAMPLES (under 150 chars):
- "try criminal for short episodes, bear brook for deep dives" (60 chars)
- "in the dark season 2 is incredible" (36 chars)
- "criminal and teacher's pet are both great" (43 chars)

CRITICAL: Your response should ONLY contain the actual comment text.
DO NOT add "(X chars)" or any other metadata.

BAD EXAMPLES (too long):
- Any response over 150 characters
- Recommending more than 2 podcasts
- Adding personal stories or context

REDDIT POST:
Title: {post.title}
Content: {post.content}
{context_section}{knowledge_section}

Write ONE sentence, 1-2 podcast recommendations, under 150 chars{brand_section}:"""

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
5. CTA SUBTLETY: If {brand_config.brand_name} is mentioned, does it feel natural or forced?

Original Post:
Title: {original_post.title}
Content: {original_post.content}

Response:
{response_content}

Brand Guidelines for {brand_config.brand_name}:
{chr(10).join(f"- {claim}" for claim in brand_config.allowed_claims[:3])}

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
