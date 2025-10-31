"""Review queue for human approval of generated responses."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from loguru import logger

from src.models import DraftResponse, ReviewStatus


class ReviewQueue:
    """Manages queue of drafts awaiting human review."""
    
    def __init__(self, storage_dir: Path):
        """Initialize review queue.
        
        Args:
            storage_dir: Directory to store queue data
        """
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.pending_dir = storage_dir / "pending"
        self.approved_dir = storage_dir / "approved"
        self.posted_dir = storage_dir / "posted"
        self.rejected_dir = storage_dir / "rejected"
        
        for dir in [self.pending_dir, self.approved_dir, self.posted_dir, self.rejected_dir]:
            dir.mkdir(exist_ok=True)
    
    def add_draft(self, draft: DraftResponse) -> None:
        """Add a draft to the pending queue.
        
        Args:
            draft: Draft response to queue
        """
        file_path = self.pending_dir / f"{draft.draft_id}.json"
        
        with file_path.open('w') as f:
            json.dump(draft.model_dump(mode='json'), f, indent=2, default=str)
        
        logger.info(f"Added draft {draft.draft_id} to review queue")
    
    def get_pending(self, limit: int = 50) -> List[DraftResponse]:
        """Get pending drafts for review.
        
        Args:
            limit: Maximum number of drafts to return
            
        Returns:
            List of pending drafts
        """
        drafts = []
        
        for file_path in sorted(self.pending_dir.glob("*.json"))[:limit]:
            try:
                with file_path.open('r') as f:
                    data = json.load(f)
                    drafts.append(DraftResponse(**data))
            except Exception as e:
                logger.error(f"Error loading draft {file_path}: {e}")
        
        return drafts
    
    def approve_draft(
        self,
        draft_id: str,
        reviewer_notes: Optional[str] = None,
    ) -> Optional[DraftResponse]:
        """Approve a draft for posting.
        
        Args:
            draft_id: Draft ID to approve
            reviewer_notes: Optional notes from reviewer
            
        Returns:
            Approved draft or None if not found
        """
        source = self.pending_dir / f"{draft_id}.json"
        
        if not source.exists():
            logger.warning(f"Draft {draft_id} not found in pending queue")
            return None
        
        # Load and update draft
        with source.open('r') as f:
            data = json.load(f)
        
        draft = DraftResponse(**data)
        draft.status = ReviewStatus.APPROVED
        draft.reviewed_at = datetime.now()
        draft.reviewer_notes = reviewer_notes
        
        # Move to approved directory
        dest = self.approved_dir / f"{draft_id}.json"
        with dest.open('w') as f:
            json.dump(draft.model_dump(mode='json'), f, indent=2, default=str)
        
        source.unlink()
        
        logger.info(f"Approved draft {draft_id}")
        return draft
    
    def reject_draft(
        self,
        draft_id: str,
        reviewer_notes: Optional[str] = None,
    ) -> bool:
        """Reject a draft.
        
        Args:
            draft_id: Draft ID to reject
            reviewer_notes: Optional notes from reviewer
            
        Returns:
            True if rejected successfully
        """
        source = self.pending_dir / f"{draft_id}.json"
        
        if not source.exists():
            logger.warning(f"Draft {draft_id} not found")
            return False
        
        # Load and update draft
        with source.open('r') as f:
            data = json.load(f)
        
        draft = DraftResponse(**data)
        draft.status = ReviewStatus.REJECTED
        draft.reviewed_at = datetime.now()
        draft.reviewer_notes = reviewer_notes
        
        # Move to rejected directory
        dest = self.rejected_dir / f"{draft_id}.json"
        with dest.open('w') as f:
            json.dump(draft.model_dump(mode='json'), f, indent=2, default=str)
        
        source.unlink()
        
        logger.info(f"Rejected draft {draft_id}")
        return True
    
    def mark_posted(
        self,
        draft_id: str,
        comment_id: str,
    ) -> bool:
        """Mark a draft as successfully posted.
        
        Args:
            draft_id: Draft ID
            comment_id: Reddit comment ID
            
        Returns:
            True if marked successfully
        """
        source = self.approved_dir / f"{draft_id}.json"
        
        if not source.exists():
            logger.warning(f"Draft {draft_id} not found in approved queue")
            return False
        
        # Load and update draft
        with source.open('r') as f:
            data = json.load(f)
        
        draft = DraftResponse(**data)
        draft.status = ReviewStatus.POSTED
        draft.posted_comment_id = comment_id
        draft.posted_at = datetime.now()
        
        # Move to posted directory
        dest = self.posted_dir / f"{draft_id}.json"
        with dest.open('w') as f:
            json.dump(draft.model_dump(mode='json'), f, indent=2, default=str)
        
        source.unlink()
        
        logger.info(f"Marked draft {draft_id} as posted (comment {comment_id})")
        return True
    
    def get_approved(self, limit: int = 10) -> List[DraftResponse]:
        """Get approved drafts ready for posting.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of approved drafts
        """
        drafts = []
        
        for file_path in sorted(self.approved_dir.glob("*.json"))[:limit]:
            try:
                with file_path.open('r') as f:
                    data = json.load(f)
                    drafts.append(DraftResponse(**data))
            except Exception as e:
                logger.error(f"Error loading draft {file_path}: {e}")
        
        return drafts
    
    def get_stats(self) -> dict:
        """Get queue statistics.
        
        Returns:
            Dict with queue stats
        """
        return {
            "pending": len(list(self.pending_dir.glob("*.json"))),
            "approved": len(list(self.approved_dir.glob("*.json"))),
            "posted": len(list(self.posted_dir.glob("*.json"))),
            "rejected": len(list(self.rejected_dir.glob("*.json"))),
        }