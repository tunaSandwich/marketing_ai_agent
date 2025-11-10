"""Validate subjects and subreddit policies configs."""

from pathlib import Path

from loguru import logger

from src.reddit.policies import SubredditPolicyStore
from src.reddit.subjects import SubjectsStore


def main() -> None:
    repo_root = Path(__file__).parent.parent

    policies_path = repo_root / "configs" / "subreddit_policies.yaml"
    subjects_path = repo_root / "configs" / "subjects_to_subreddits.yaml"

    logger.info("Loading subreddit policies...")
    policies_store = SubredditPolicyStore(config_path=policies_path)
    policies = policies_store.load()
    logger.info(f"Policies loaded: {len(policies.subreddits)} subreddits (+ defaults)")

    logger.info("Loading subjects mapping...")
    subjects_store = SubjectsStore(config_path=subjects_path)
    subjects = subjects_store.load()
    logger.info(f"Subjects loaded: {len(subjects.subjects)} subject categories")

    # Sample lookups
    for subject in ["Quantum Physics", "Programming", "Podcasts (General Discovery)"]:
        subs = subjects_store.subreddits_for(subject)
        logger.info(f"Subject '{subject}' → {len(subs)} subreddits: {', '.join(subs[:8])}{'...' if len(subs) > 8 else ''}")

    # Sample policy check
    for sub in ["podcasts", "AskHistorians", "MachineLearning"]:
        p = policies_store.get(sub)
        logger.info(f"Policy r/{sub}: allow_links={p.allow_links}, promo_override={p.promo_ratio_override}, min_post_score={p.min_post_score}")

    logger.info("Validation complete.")


if __name__ == "__main__":
    main()


