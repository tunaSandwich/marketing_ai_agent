"""Claude API client for generating responses."""

import time

from anthropic import Anthropic
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import GeneratedResponse
from ..utils.config import LLMConfig


class ClaudeClient:
    """Claude API client with retry logic and error handling."""

    def __init__(self, config: LLMConfig) -> None:
        """Initialize Claude client with configuration."""
        self._config = config
        self._client = Anthropic(api_key=config.api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_response(
        self,
        prompt: str,
        post_id: str,
        brand_id: str,
        response_id: str,
        prompt_template: str = "v1.0",
    ) -> GeneratedResponse:
        """Generate a response using Claude.

        Args:
            prompt: Formatted prompt for Claude
            post_id: Reddit post ID being responded to
            brand_id: Brand pack ID being used
            response_id: Unique response ID
            prompt_template: Version of prompt template used

        Returns:
            Generated response with metadata
        """
        start_time = time.time()

        try:
            logger.debug(f"Generating response for post {post_id} with brand {brand_id}")

            message = self._client.messages.create(
                model=self._config.model,
                max_tokens=self._config.max_tokens,
                temperature=self._config.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            generation_time_ms = int((time.time() - start_time) * 1000)

            # Extract text content from the response
            content = ""
            if message.content and len(message.content) > 0:
                content = (
                    message.content[0].text
                    if hasattr(message.content[0], "text")
                    else str(message.content[0])
                )

            response = GeneratedResponse(
                id=response_id,
                content=content.strip(),
                post_id=post_id,
                brand_id=brand_id,
                model_used=self._config.model,
                prompt_template=prompt_template,
                generation_time_ms=generation_time_ms,
            )

            logger.info(f"Generated response {response_id} in {generation_time_ms}ms")
            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def evaluate_response(
        self,
        response_content: str,
        original_post: str,
        evaluation_prompt: str,
    ) -> dict[str, int]:
        """Evaluate a response using Claude.

        Args:
            response_content: Response to evaluate
            original_post: Original Reddit post
            evaluation_prompt: Evaluation prompt template

        Returns:
            Dictionary with evaluation scores
        """
        try:
            message = self._client.messages.create(
                model=self._config.model,
                max_tokens=1000,
                temperature=0.1,  # Lower temperature for more consistent evaluation
                messages=[{"role": "user", "content": evaluation_prompt}],
            )

            # Extract text content
            content = ""
            if message.content and len(message.content) > 0:
                content = (
                    message.content[0].text
                    if hasattr(message.content[0], "text")
                    else str(message.content[0])
                )

            # Parse evaluation scores from response
            scores = self._parse_evaluation_scores(content)

            logger.debug(f"Evaluated response with scores: {scores}")
            return scores

        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            raise

    def _parse_evaluation_scores(self, evaluation_response: str) -> dict[str, int]:
        """Parse evaluation scores from Claude's response.

        Args:
            evaluation_response: Raw evaluation response from Claude

        Returns:
            Dictionary with parsed scores
        """
        import re

        # Default scores if parsing fails
        scores = {
            "relevance_score": 5,
            "helpfulness_score": 5,
            "naturalness_score": 5,
            "brand_safety_score": 5,
            "cta_subtlety_score": 5,
        }

        # Look for score patterns in the response
        score_patterns = {
            "relevance_score": r"relevance[:\s]*(\d+)",
            "helpfulness_score": r"helpfulness[:\s]*(\d+)",
            "naturalness_score": r"naturalness[:\s]*(\d+)",
            "brand_safety_score": r"brand[_\s]*safety[:\s]*(\d+)",
            "cta_subtlety_score": r"cta[_\s]*subtlety[:\s]*(\d+)",
        }

        for score_name, pattern in score_patterns.items():
            match = re.search(pattern, evaluation_response, re.IGNORECASE)
            if match:
                try:
                    score = int(match.group(1))
                    # Ensure score is within valid range
                    scores[score_name] = max(0, min(10, score))
                except ValueError:
                    logger.warning(f"Could not parse {score_name} from evaluation response")

        return scores

    def validate_claim(self, claim: str, brand_id: str, allowed_claims: list[str]) -> bool:
        """Validate if a claim is allowed for the brand.

        Args:
            claim: Claim to validate
            brand_id: Brand ID
            allowed_claims: List of allowed claims for the brand

        Returns:
            True if claim is allowed
        """
        # Simple substring matching for now
        # In a full implementation, this could use semantic similarity
        claim_lower = claim.lower()

        for allowed_claim in allowed_claims:
            if allowed_claim.lower() in claim_lower:
                return True

        logger.warning(f"Claim not in allowlist for brand {brand_id}: {claim}")
        return False

    def health_check(self) -> bool:
        """Check if Claude API is accessible.

        Returns:
            True if API is healthy
        """
        try:
            # Simple test message
            message = self._client.messages.create(
                model=self._config.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'OK' if you can hear me."}],
            )

            return message is not None

        except Exception as e:
            logger.error(f"Claude health check failed: {e}")
            return False
