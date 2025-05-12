from sqlalchemy import func
from sqlalchemy.orm import Session
import numpy as np
from typing import List
from src.models.candidate_model import CandidateProfile
from src.core.custom_logger import CustomLogger

logger = CustomLogger("CandidateCRUD")

def create_candidate_profile(
    db: Session, 
    user_id: int, 
    parsed_resume: dict, 
    resume_vector: list = None,
    location_vector: list = None,
    total_experience: float = 0.0,
    mongodb_id: str = None
):
    try:
        # Check if profile exists
        existing_profile = get_candidate_profile(db, user_id)
        if existing_profile:
            # Update existing profile
            existing_profile.parsed_resume = parsed_resume
            existing_profile.resume_vector = resume_vector
            existing_profile.total_experience = total_experience
            existing_profile.mongodb_id = mongodb_id
            db.commit()
            db.refresh(existing_profile)
            logger.info(f"Updated candidate profile for user {user_id}")
            return existing_profile
            
        # Create new profile
        db_profile = CandidateProfile(
            user_id=user_id,
            parsed_resume=parsed_resume,
            resume_vector=resume_vector,
            total_experience=total_experience,
            mongodb_id=mongodb_id
        )
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        logger.info(f"Created candidate profile for user {user_id}")
        return db_profile
    except Exception as e:
        logger.error(f"Error creating candidate profile: {e}")
        db.rollback()
        raise

def get_candidate_profile(db: Session, user_id: int):
    return db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()

def search_candidates_by_skills(
    db: Session,
    skills_vector: List[float],
    limit: int = 10,
    similarity_threshold: float = 0.7
) -> List[CandidateProfile]:
    """
    Search candidates using vector similarity.
    Returns candidates sorted by similarity score.
    """
    try:
        # Get all candidates with their vectors
        candidates = db.query(CandidateProfile).filter(
            CandidateProfile.resume_vector.isnot(None)
        ).all()

        # Calculate cosine similarity scores
        def cosine_similarity(vec1, vec2):
            if not vec1 or not vec2:
                return 0
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            return dot_product / (norm1 * norm2) if norm1 and norm2 else 0

        # Calculate similarities and filter/sort candidates
        candidates_with_scores = [
            (candidate, cosine_similarity(skills_vector, candidate.resume_vector))
            for candidate in candidates
        ]

        # Filter by threshold and sort by similarity
        filtered_candidates = [
            candidate for candidate, score in candidates_with_scores
            if score >= similarity_threshold
        ]
        
        sorted_candidates = sorted(
            filtered_candidates,
            key=lambda x: cosine_similarity(skills_vector, x.resume_vector),
            reverse=True
        )

        logger.info(f"Found {len(sorted_candidates)} matching candidates")
        return sorted_candidates[:limit]

    except Exception as e:
        logger.error(f"Error searching candidates: {e}")
        raise