"""Brand pack loading and validation."""

from pathlib import Path

import yaml
from loguru import logger
from pydantic import ValidationError

from ..models import BrandConfig


class BrandLoader:
    """Loads and validates brand pack configurations."""

    def __init__(self, brands_dir: Path) -> None:
        """Initialize brand loader with brands directory."""
        self._brands_dir = brands_dir

    def load_brand_config(self, brand_id: str) -> BrandConfig:
        """Load brand configuration from YAML file.

        Args:
            brand_id: Brand identifier

        Returns:
            Validated brand configuration

        Raises:
            FileNotFoundError: If brand config file doesn't exist
            ValidationError: If config is invalid
        """
        config_path = self._brands_dir / brand_id / "config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Brand config not found: {config_path}")

        try:
            with config_path.open(encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # Ensure brand_id matches directory name
            config_data["brand_id"] = brand_id

            config = BrandConfig(**config_data)
            logger.info(f"Loaded brand config for {brand_id}")
            return config

        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML for brand {brand_id}: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Invalid brand config for {brand_id}: {e}")
            raise

    def list_available_brands(self) -> list[str]:
        """List all available brand IDs.

        Returns:
            List of available brand identifiers
        """
        if not self._brands_dir.exists():
            return []

        brands = []
        for brand_dir in self._brands_dir.iterdir():
            if brand_dir.is_dir() and (brand_dir / "config.yaml").exists():
                brands.append(brand_dir.name)

        return sorted(brands)

    def validate_brand_config(self, brand_id: str) -> bool:
        """Validate a brand configuration.

        Args:
            brand_id: Brand identifier to validate

        Returns:
            True if configuration is valid
        """
        try:
            config = self.load_brand_config(brand_id)
            return self._validate_brand_completeness(config)
        except (FileNotFoundError, ValidationError, yaml.YAMLError):
            return False

    def _validate_brand_completeness(self, config: BrandConfig) -> bool:
        """Validate that brand configuration is complete.

        Args:
            config: Brand configuration to validate

        Returns:
            True if configuration is complete and valid
        """
        # Check that required fields are not empty
        if not config.brand_name.strip():
            logger.error(f"Brand {config.brand_id} missing brand_name")
            return False

        if not config.voice_guidelines.strip():
            logger.error(f"Brand {config.brand_id} missing voice_guidelines")
            return False

        if not config.allowed_claims:
            logger.error(f"Brand {config.brand_id} missing allowed_claims")
            return False

        # Validate that knowledge directory exists
        knowledge_dir = self._brands_dir / config.brand_id / "knowledge"
        if not knowledge_dir.exists():
            logger.warning(f"Brand {config.brand_id} missing knowledge directory")

        # Check that subreddits are properly formatted
        all_subreddits = config.subreddits_tier1 + config.subreddits_tier2 + config.subreddits_tier3

        for subreddit in all_subreddits:
            if subreddit.startswith("r/"):
                logger.warning(f"Subreddit {subreddit} includes 'r/' prefix - should be removed")

        return True

    def get_knowledge_files(self, brand_id: str) -> list[Path]:
        """Get list of knowledge files for a brand.

        Args:
            brand_id: Brand identifier

        Returns:
            List of knowledge file paths
        """
        knowledge_dir = self._brands_dir / brand_id / "knowledge"

        if not knowledge_dir.exists():
            return []

        # Get all markdown and text files
        knowledge_files = []
        for ext in ["*.md", "*.txt", "*.yaml", "*.yml"]:
            knowledge_files.extend(knowledge_dir.glob(ext))

        return sorted(knowledge_files)

    def load_knowledge_content(self, brand_id: str) -> dict[str, str]:
        """Load all knowledge content for a brand.

        Args:
            brand_id: Brand identifier

        Returns:
            Dictionary mapping filename to content
        """
        knowledge_files = self.get_knowledge_files(brand_id)
        content = {}

        for file_path in knowledge_files:
            try:
                with file_path.open(encoding="utf-8") as f:
                    content[file_path.name] = f.read()
                logger.debug(f"Loaded knowledge file: {file_path.name}")
            except Exception as e:
                logger.warning(f"Error loading knowledge file {file_path}: {e}")

        logger.info(f"Loaded {len(content)} knowledge files for brand {brand_id}")
        return content

    def create_brand_template(self, brand_id: str) -> None:
        """Create a template brand configuration.

        Args:
            brand_id: New brand identifier
        """
        brand_dir = self._brands_dir / brand_id
        brand_dir.mkdir(parents=True, exist_ok=True)

        # Create knowledge directory
        knowledge_dir = brand_dir / "knowledge"
        knowledge_dir.mkdir(exist_ok=True)

        # Create template config
        template_config = {
            "brand_name": f"{brand_id.title()} Brand",
            "company_description": "Company description goes here",
            "voice_guidelines": "Voice and tone guidelines go here",
            "tone_attributes": ["friendly", "helpful", "authentic"],
            "allowed_claims": [
                "Free service",
                "Available on mobile",
            ],
            "forbidden_topics": [
                "Competitor comparisons",
                "Pricing information",
            ],
            "primary_cta": "https://example.com",
            "tracking_params": "?utm_source=reddit&utm_medium=comment",
            "subreddits_tier1": ["podcasts"],
            "subreddits_tier2": [],
            "subreddits_tier3": [],
        }

        config_path = brand_dir / "config.yaml"
        with config_path.open("w", encoding="utf-8") as f:
            yaml.dump(template_config, f, default_flow_style=False, sort_keys=False)

        # Create sample knowledge file
        sample_knowledge = brand_dir / "knowledge" / "features.md"
        with sample_knowledge.open("w", encoding="utf-8") as f:
            f.write(f"# {brand_id.title()} Features\n\n")
            f.write("Add your product features and knowledge here.\n")

        logger.info(f"Created brand template for {brand_id} at {brand_dir}")
    
    def load_knowledge(self, brand_id: str) -> dict[str, str]:
        """Convenience method for loading knowledge content.
        
        Args:
            brand_id: Brand identifier
            
        Returns:
            Dictionary mapping filename to content
        """
        return self.load_knowledge_content(brand_id)
