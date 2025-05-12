from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from src.models.candidate_model import CandidateProfile
from src.models.job_model import Job
from src.utils.text_embedder import TextEmbedder
from src.utils.text_parser import TextParser
from src.core.custom_logger import CustomLogger
import numpy as np

class RankHandler:
    """Handles resume ranking against job postings using vector similarity."""

    def __init__(self, logger: Optional[CustomLogger] = None):
        self.logger = logger or CustomLogger("RankHandler")
        self.text_embedder = TextEmbedder(logger=self.logger)
        self.text_parser = TextParser(logger=self.logger)
        # Weights for different matching criteria
        self.weights = {
            "skills": 0.4,
            "experience": 0.3,
            "title": 0.2,
            "location": 0.1
        }

    def calculate_skills_match(self, candidate_vector: List[float], job_vector: List[float]) -> float:
        """Calculate skills match using vector similarity."""
        try:
            if not candidate_vector or not job_vector:
                return 0
            
            dot_product = np.dot(candidate_vector, job_vector)
            norm1 = np.linalg.norm(candidate_vector)
            norm2 = np.linalg.norm(job_vector)
            
            if norm1 and norm2:
                similarity = float(dot_product / (norm1 * norm2))
                return max(0.0, min(1.0, similarity))
            return 0
            
        except Exception as e:
            self.logger.error(f"Error calculating skills match: {e}")
            return 0

    def calculate_experience_match(self, candidate_experience: float, required_experience: float) -> float:
        """Calculate experience match score."""
        try:
            if candidate_experience is None or required_experience is None:
                return 0

            difference_years = abs(candidate_experience - required_experience)
            
            if difference_years == 0:
                return 1.0
            elif difference_years <= 1:
                return 0.9
            elif difference_years <= 2:
                return 0.7
            elif difference_years <= 3:
                return 0.5
            elif difference_years <= 4:
                return 0.3
            else:
                return 0.1

        except Exception as e:
            self.logger.error(f"Error calculating experience match: {e}")
            return 0

    def rank_candidates_for_job(
        self,
        db: Session,
        job_id: int,
        min_score: float = 0.5,
        limit: int = 10
    ) -> List[Dict]:
        """Rank candidates for a specific job posting."""
        try:
            # Get job details
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                self.logger.error(f"Job {job_id} not found")
                return []

            # Get all candidates
            candidates = db.query(CandidateProfile).all()
            if not candidates:
                self.logger.info("No candidates found to rank")
                return []
                
            self.logger.debug(f"Found {len(candidates)} candidates to rank")

            ranked_results = []
            for candidate in candidates:
                total_score = 0
                scores = {
                    'skills_score': 0.0,
                    'experience_score': 0.0,
                    'location_score': 0.0
                }

                # Skills match
                if job.jd_vector and candidate.resume_vector:
                    skills_score = self.calculate_skills_match(
                        candidate.resume_vector,
                        job.jd_vector
                    )
                    scores['skills_score'] = skills_score
                    total_score += skills_score * self.weights['skills']

                # Experience match
                if job.required_experience and candidate.total_experience:
                    experience_score = self.calculate_experience_match(
                        candidate.total_experience,
                        job.required_experience
                    )
                    scores['experience_score'] = experience_score
                    total_score += experience_score * self.weights['experience']

                # Location match using text comparison
                candidate_location = candidate.parsed_resume.get("personal_info", {}).get("location")
                if job.location and candidate_location:
                    from src.services.search_handler import SearchHandler
                    search_handler = SearchHandler(logger=self.logger)
                    location_score = search_handler.calculate_location_match(
                        job.location,
                        candidate_location
                    )
                    scores['location_score'] = location_score
                    total_score += location_score * self.weights['location']

                # Only include candidates above minimum score
                if total_score >= min_score:
                    ranked_results.append({
                        'candidate': candidate,
                        'scores': scores,
                        'total_score': total_score
                    })

            # Sort by total score and limit results
            sorted_results = sorted(
                ranked_results,
                key=lambda x: x['total_score'],
                reverse=True
            )[:limit]

            # Format log message
            if sorted_results:
                top_score = f"{sorted_results[0]['total_score']:.2f}"
                self.logger.info(
                    f"Ranked {len(sorted_results)} candidates for job {job_id}\n"
                    f"Top score: {top_score}"
                )
            else:
                self.logger.info(f"No candidates matched minimum score for job {job_id}")

            return sorted_results

        except Exception as e:
            self.logger.error(f"Error ranking candidates: {e}")
            return []