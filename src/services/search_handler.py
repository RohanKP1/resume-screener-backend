from sqlalchemy.orm import Session
from typing import List, Dict, Optional, NamedTuple
import numpy as np
from src.models.candidate_model import CandidateProfile
from src.core.custom_logger import CustomLogger

class SearchScores(NamedTuple):
    """Contains individual and total scores for a candidate match"""
    skills_score: float
    location_score: float 
    experience_score: float
    total_score: float

class SearchHandler:
    """Handles complex candidate searches with multiple criteria"""

    def __init__(self, logger: Optional[CustomLogger] = None):
        self.logger = logger or CustomLogger("SearchHandler")
        # Updated weights
        self.weights = {
            'skills': 0.6,  # Increased importance of skills
            'location': 0.2,
            'experience': 0.2
        }

    def calculate_skills_similarity(self, query_vectors: List[List[float]], candidate_vector: List[float]) -> float:
        """Calculate average similarity across multiple skill vectors"""
        try:
            if not query_vectors or not candidate_vector:
                return 0
                
            similarities = []
            for vec in query_vectors:
                dot_product = np.dot(vec, candidate_vector)
                norm1 = np.linalg.norm(vec)
                norm2 = np.linalg.norm(candidate_vector)
                if norm1 and norm2:
                    similarities.append(float(dot_product / (norm1 * norm2)))
                    
            return max(similarities) if similarities else 0
            
        except Exception as e:
            self.logger.error(f"Error calculating skills similarity: {e}")
            return 0

    def calculate_location_match(self, query_location: str, candidate_location: str) -> float:
        """Calculate location match using text comparison with fuzzy matching"""
        try:
            if not query_location or not candidate_location:
                return 0

            # Convert to lowercase and split into parts
            query_parts = [q.strip().lower() for q in query_location.split(',')]
            candidate_parts = [c.strip().lower() for c in candidate_location.split(',')]

            max_similarities = []
            for query_part in query_parts:
                # Calculate similarity with each candidate part
                similarities = []
                for candidate_part in candidate_parts:
                    # Exact match
                    if query_part == candidate_part:
                        similarities.append(1.0)
                        continue
                    
                    # Substring match
                    if query_part in candidate_part or candidate_part in query_part:
                        similarities.append(0.9)
                        continue
                    
                    # Levenshtein-like similarity for similar spellings
                    similarity = 0
                    shorter, longer = sorted([query_part, candidate_part], key=len)
                    if len(longer) == 0:
                        similarities.append(0)
                        continue
                    
                    # Count matching characters
                    matches = sum(1 for a, b in zip(shorter, longer) if a == b)
                    similarity = matches / len(longer)
                    similarities.append(similarity)
                
                max_similarities.append(max(similarities) if similarities else 0)

            # Final score is average of best matches
            match_ratio = sum(max_similarities) / len(query_parts)
            
            self.logger.debug(
                f"Location match: {query_location} vs {candidate_location} "
                f"(score: {match_ratio:.2f})"
            )
            return match_ratio

        except Exception as e:
            self.logger.error(f"Error calculating location match: {e}")
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

    def search_candidates(
        self,
        db: Session,
        skills_vectors: Optional[List[List[float]]] = None,
        location: Optional[str] = None,  # Changed from location_vector to location
        required_experience: Optional[float] = None,
        min_score: float = 0.5,
        limit: int = 10
    ) -> List[Dict]:
        try:
            candidates = db.query(CandidateProfile).all()
            self.logger.debug(f"Found {len(candidates)} total candidates")
            results = []

            for candidate in candidates:
                skills_score = location_score = experience_score = None
                total_score = total_weight = 0

                # Calculate skills score if vectors provided
                if skills_vectors and candidate.resume_vector:
                    skills_score = self.calculate_skills_similarity(skills_vectors, candidate.resume_vector)
                    total_score += skills_score * self.weights['skills']
                    total_weight += self.weights['skills']
                    self.logger.debug(f"Skills score: {skills_score:.3f}")
                
                # Calculate location score if location provided
                if location and candidate.parsed_resume.get("personal_info", {}).get("location"):
                    location_score = self.calculate_location_match(
                        location,
                        candidate.parsed_resume["personal_info"]["location"]
                    )
                    total_score += location_score * self.weights['location']
                    total_weight += self.weights['location']
                    self.logger.debug(f"Location score: {location_score:.3f}")
                
                # Calculate experience score if required experience provided
                if required_experience and candidate.total_experience != "":
                    experience_score = self.calculate_experience_match(
                        candidate.total_experience,
                        required_experience
                    )
                    total_score += experience_score * self.weights['experience']
                    total_weight += self.weights['experience']
                    self.logger.debug(f"Experience score: {experience_score:.3f}")

                # Calculate final score
                if total_weight > 0:
                    final_score = total_score / total_weight
                    self.logger.debug(f"Final score: {final_score:.3f}")

                    if final_score >= min_score:
                        results.append({
                            'candidate': candidate,
                            'scores': SearchScores(
                                skills_score=skills_score or 0.0,
                                location_score=location_score or 0.0,
                                experience_score=experience_score or 0.0,
                                total_score=final_score
                            )
                        })

            # Sort and limit results
            sorted_results = sorted(
                results,
                key=lambda x: x['scores'].total_score,
                reverse=True
            )[:limit]

            # Prepare log message
            top_score = "N/A"
            if sorted_results:
                top_score = f"{sorted_results[0]['scores'].total_score:.3f}"

            self.logger.info(
                f"Search results:\n"
                f"- Total candidates: {len(candidates)}\n"
                f"- Matching candidates: {len(sorted_results)}\n"
                f"- Top score: {top_score}"
            )
            return sorted_results

        except Exception as e:
            self.logger.error(f"Error searching candidates: {e}")
            raise

    def get_search_summary(self, search_results: List[Dict]) -> Dict:
        """Generate summary statistics for search results"""
        try:
            if not search_results:
                self.logger.info("No search results found")
                return {
                    "count": 0,
                    "avg_score": 0.0,
                    "max_score": 0.0,
                    "min_score": 0.0,
                    "score_distribution": {
                        "excellent": 0,
                        "good": 0,
                        "fair": 0
                    }
                }

            scores = [r['scores'].total_score for r in search_results]
            summary = {
                "count": len(search_results),
                "avg_score": float(np.mean(scores)) if scores else 0.0,
                "max_score": float(np.max(scores)) if scores else 0.0,
                "min_score": float(np.min(scores)) if scores else 0.0,
                "score_distribution": {
                    "excellent": len([s for s in scores if s >= 0.8]),
                    "good": len([s for s in scores if 0.6 <= s < 0.8]),
                    "fair": len([s for s in scores if 0.5 <= s < 0.6])
                }
            }
            
            self.logger.debug(f"Search summary generated: {summary}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating search summary: {e}")
            return {"count": len(search_results) if search_results else 0}