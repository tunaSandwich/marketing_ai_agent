"""Tests for brand pack loader."""

import pytest
import yaml

from src.brand.loader import BrandLoader


class TestBrandLoader:
    """Tests for BrandLoader class."""

    def test_load_brand_config_success(self, temp_brands_dir):
        """Test successfully loading a brand config."""
        loader = BrandLoader(temp_brands_dir)
        config = loader.load_brand_config("test_brand")

        assert config.brand_id == "test_brand"
        assert config.brand_name == "Test Brand"
        assert config.company_description == "A test brand"
        assert len(config.subreddits_tier1) == 1
        assert "podcasts" in config.subreddits_tier1

    def test_load_brand_config_not_found(self, temp_brands_dir):
        """Test loading a non-existent brand config."""
        loader = BrandLoader(temp_brands_dir)

        with pytest.raises(FileNotFoundError):
            loader.load_brand_config("nonexistent_brand")

    def test_load_brand_config_invalid_yaml(self, temp_brands_dir):
        """Test loading a brand config with invalid YAML."""
        # Create invalid YAML file
        invalid_brand_dir = temp_brands_dir / "invalid_brand"
        invalid_brand_dir.mkdir()

        config_path = invalid_brand_dir / "config.yaml"
        with config_path.open("w") as f:
            f.write("invalid: yaml: content: [")

        loader = BrandLoader(temp_brands_dir)

        with pytest.raises(yaml.YAMLError):
            loader.load_brand_config("invalid_brand")

    def test_list_available_brands(self, temp_brands_dir):
        """Test listing available brands."""
        loader = BrandLoader(temp_brands_dir)
        brands = loader.list_available_brands()

        assert "test_brand" in brands
        assert isinstance(brands, list)

    def test_list_available_brands_empty_dir(self, tmp_path):
        """Test listing brands in empty directory."""
        empty_dir = tmp_path / "empty_brands"
        empty_dir.mkdir()

        loader = BrandLoader(empty_dir)
        brands = loader.list_available_brands()

        assert brands == []

    def test_validate_brand_config_success(self, temp_brands_dir):
        """Test validating a valid brand config."""
        loader = BrandLoader(temp_brands_dir)
        is_valid = loader.validate_brand_config("test_brand")

        assert is_valid is True

    def test_validate_brand_config_missing(self, temp_brands_dir):
        """Test validating a missing brand config."""
        loader = BrandLoader(temp_brands_dir)
        is_valid = loader.validate_brand_config("nonexistent_brand")

        assert is_valid is False

    def test_get_knowledge_files(self, temp_brands_dir):
        """Test getting knowledge files for a brand."""
        loader = BrandLoader(temp_brands_dir)
        knowledge_files = loader.get_knowledge_files("test_brand")

        assert len(knowledge_files) == 1
        assert knowledge_files[0].name == "features.md"

    def test_get_knowledge_files_no_knowledge_dir(self, temp_brands_dir):
        """Test getting knowledge files when knowledge dir doesn't exist."""
        # Create brand without knowledge directory
        no_knowledge_dir = temp_brands_dir / "no_knowledge"
        no_knowledge_dir.mkdir()

        config_data = {
            "brand_name": "No Knowledge Brand",
            "company_description": "Test",
            "voice_guidelines": "Test",
            "tone_attributes": ["test"],
            "allowed_claims": ["test"],
            "forbidden_topics": ["test"],
            "primary_cta": "https://example.com",
            "tracking_params": "?test=test",
            "subreddits_tier1": ["test"],
            "subreddits_tier2": [],
            "subreddits_tier3": [],
        }

        config_path = no_knowledge_dir / "config.yaml"
        with config_path.open("w") as f:
            yaml.dump(config_data, f)

        loader = BrandLoader(temp_brands_dir)
        knowledge_files = loader.get_knowledge_files("no_knowledge")

        assert knowledge_files == []

    def test_load_knowledge_content(self, temp_brands_dir):
        """Test loading knowledge content for a brand."""
        loader = BrandLoader(temp_brands_dir)
        content = loader.load_knowledge_content("test_brand")

        assert "features.md" in content
        assert "Test Features" in content["features.md"]

    def test_create_brand_template(self, tmp_path):
        """Test creating a brand template."""
        brands_dir = tmp_path / "brands"
        loader = BrandLoader(brands_dir)

        loader.create_brand_template("new_brand")

        # Check that files were created
        brand_dir = brands_dir / "new_brand"
        assert brand_dir.exists()

        config_path = brand_dir / "config.yaml"
        assert config_path.exists()

        knowledge_dir = brand_dir / "knowledge"
        assert knowledge_dir.exists()

        sample_file = knowledge_dir / "features.md"
        assert sample_file.exists()

        # Check config content
        with config_path.open() as f:
            config_data = yaml.safe_load(f)

        assert config_data["brand_name"] == "New_Brand Brand"
        assert "friendly" in config_data["tone_attributes"]
