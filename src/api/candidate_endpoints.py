from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import src.database.job_crud as job_crud
from src.services.postgres_handler import get_db
from src.services.mongo_handler import MongoHandler
from src.api.auth_endpoints import get_current_user, require_user_type
from src.schemas.auth_schema import UserType, UserResponse
from src.utils.text_extractor import TextExtractor
from src.utils.text_parser import TextParser
from src.utils.text_embedder import TextEmbedder
from src.database import candidate_crud
from src.core.custom_logger import CustomLogger
from src.schemas.mongo_schema import ResumeDocument
import src.schemas.candidate_schema as schemas
from src.services.search_handler import SearchHandler
from src.services.rank_handler import RankHandler
from datetime import datetime
import os
import tempfile
from typing import List, Optional

router = APIRouter(tags=["Candidate"])
logger = CustomLogger("CandidateEndpoints")
mongo_handler = MongoHandler(logger=logger)

@router.post("/upload_resume", response_model=schemas.CandidateProfileResponse)
@require_user_type([UserType.CANDIDATE])
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload and parse a resume file, storing raw text in MongoDB and parsed data in PostgreSQL."""
    logger.info(f"Resume upload attempt by user: {current_user.username}")

    # Validate file extension
    allowed_extensions = {'.pdf', '.docx'}
    file_ext = '.' + file.filename.split('.')[-1].lower()
    if file_ext not in allowed_extensions:
        logger.warning(f"Invalid file format: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )

    temp_file_path = None
    mongo_doc_id = None
    try:
        # --- NEW: Remove old MongoDB resume if exists ---
        existing_profile = candidate_crud.get_candidate_profile(db, current_user.id)
        if existing_profile and existing_profile.mongodb_id:
            try:
                mongo_handler.delete_one("raw_resumes", {"_id": ObjectId(existing_profile.mongodb_id)})
                logger.info(f"Deleted old MongoDB resume for user {current_user.username}")
            except Exception as cleanup_error:
                logger.error(f"Failed to delete old MongoDB resume: {cleanup_error}")

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)

        # Extract text from resume
        text_extractor = TextExtractor(logger=logger)
        extracted_text = text_extractor.extract_text(temp_file_path)

        # Store raw text in MongoDB
        resume_doc = ResumeDocument(
            user_id=current_user.id,
            raw_text=extracted_text,
            file_name=file.filename,
            file_type=file_ext,
            metadata={
                "original_filename": file.filename,
                "upload_timestamp": datetime.utcnow().isoformat()
            }
        )

        # Insert into MongoDB and get ID
        mongo_doc_id = mongo_handler.insert_one(
            collection="raw_resumes",
            document=resume_doc.dict()
        )

        # Parse resume text
        text_parser = TextParser(logger=logger)
        parsed_resume = text_parser.parse_text(extracted_text, parse_type="resume")
        if not parsed_resume:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to parse resume"
            )

        # Calculate total experience and generate embeddings
        total_experience = text_parser.calculate_total_experience(parsed_resume)

        # Generate embeddings for skills only
        text_embedder = TextEmbedder(logger=logger)
        skills_text = " ".join(parsed_resume.get("skills", {}).get("technical", []))
        resume_vector = text_embedder.embed_text(skills_text)

        # Save parsed data to PostgreSQL (overwrites if exists)
        candidate_profile = candidate_crud.create_candidate_profile(
            db=db,
            user_id=current_user.id,
            parsed_resume=parsed_resume,
            resume_vector=resume_vector,
            total_experience=total_experience,
            mongodb_id=str(mongo_doc_id)
        )

        logger.info(f"Successfully processed resume for user: {current_user.username}")
        return candidate_profile

    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        # Cleanup MongoDB document if needed
        if mongo_doc_id:
            try:
                mongo_handler.delete_one("raw_resumes", {"_id": mongo_doc_id})
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup MongoDB document: {cleanup_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process resume"
        )
    finally:
        # Cleanup temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.error(f"Failed to cleanup temporary file: {e}")

@router.get("/resume/{user_id}", response_model=schemas.CandidateProfileResponse)
@require_user_type([UserType.RECRUITER])
async def get_resume(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a candidate's resume data (parsed and raw)."""
    profile = candidate_crud.get_candidate_profile(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    # Fetch raw text from MongoDB if needed
    if profile.mongodb_id:
        raw_resume = mongo_handler.find_one(
            collection="raw_resumes",
            query={"_id": ObjectId(profile.mongodb_id)}
        )
        profile.raw_text = raw_resume.get("raw_text") if raw_resume else None
    
    return profile

@router.get("/resume", response_model=schemas.CandidateProfileResponse)
@require_user_type([UserType.CANDIDATE])
async def get_own_resume(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get the current candidate's resume data (parsed and raw).
    """
    profile = candidate_crud.get_candidate_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Fetch raw text from MongoDB if needed
    if profile.mongodb_id:
        raw_resume = mongo_handler.find_one(
            collection="raw_resumes",
            query={"_id": ObjectId(profile.mongodb_id)}
        )
        profile.raw_text = raw_resume.get("raw_text") if raw_resume else None

    return profile

@router.get("/search", response_model=List[schemas.CandidateSearchResponse])
@require_user_type([UserType.RECRUITER])
async def search_candidates(
    skills: Optional[str] = None,
    location: Optional[str] = None,
    experience: Optional[float] = None,
    min_score: float = 0.5,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Search candidates with optional criteria:
    - Skills (comma-separated)
    - Location (text-based matching)
    - Experience (in years)
    At least one search parameter must be provided.
    """
    if not any([skills, location, experience]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search parameter must be provided"
        )
    
    try:
        search_handler = SearchHandler(logger=logger)
        text_embedder = TextEmbedder(logger=logger)
        
        # Generate embeddings for skills if provided
        skills_vectors = None
        if skills:
            skill_list = [s.strip() for s in skills.split(',')]
            skills_vectors = text_embedder.embed_text_batch(skill_list)
        
        # Perform search with text-based location matching
        search_results = search_handler.search_candidates(
            db=db,
            skills_vectors=skills_vectors,
            location=location,  # Pass location string directly
            required_experience=experience,
            min_score=min_score,
            limit=limit
        ) or []
                
        # Generate search summary only if we have results
        if search_results:
            summary = search_handler.get_search_summary(search_results)
            logger.info(f"Search summary: {summary}")
        else:
            logger.info("No matching candidates found")
            return []
        
        # Process results
        candidates = []
        for result in search_results:
            candidate = result['candidate']
            scores = result['scores']
            
            if candidate.mongodb_id:
                try:
                    raw_resume = mongo_handler.find_one(
                        collection="raw_resumes",
                        query={"_id": ObjectId(candidate.mongodb_id)}
                    )
                    candidate.raw_text = raw_resume.get("raw_text") if raw_resume else None
                except Exception as e:
                    logger.error(f"Error fetching MongoDB document: {e}")
                    candidate.raw_text = None
            
            candidate.match_scores = scores
            candidates.append(candidate)
        
        return candidates
        
    except Exception as e:
        logger.error(f"Error searching candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search candidates"
        )

@router.get("/rank_candidates", response_model=List[schemas.CandidateRankResponse])
@require_user_type([UserType.RECRUITER])
async def rank_candidates(
    job_id: int,
    min_score: float = 0.5,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get ranked candidates for a specific job posting.
    Args:
        job_id: ID of the job posting
        min_score: Minimum match score (0-1)
        limit: Maximum number of results
    Returns:
        List of candidates ranked by match score
    """
    try:
        # Verify job exists and recruiter has access
        job = job_crud.get_job(db, job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Optional: Check if recruiter owns the job
        if job.recruiter_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view candidates for this job"
            )

        # Rank candidates
        rank_handler = RankHandler(logger=logger)
        ranked_results = rank_handler.rank_candidates_for_job(
            db=db,
            job_id=job_id,
            min_score=min_score,
            limit=limit
        )

        # Process results
        candidates = []
        for result in ranked_results:
            candidate = result['candidate']
            scores = result['scores']
            
            # Fetch raw resume text if needed
            if candidate.mongodb_id:
                try:
                    raw_resume = mongo_handler.find_one(
                        collection="raw_resumes",
                        query={"_id": ObjectId(candidate.mongodb_id)}
                    )
                    candidate.raw_text = raw_resume.get("raw_text") if raw_resume else None
                except Exception as e:
                    logger.error(f"Error fetching MongoDB document: {e}")
                    candidate.raw_text = None
            
            # Add match scores
            candidate.match_scores = schemas.RankScores(
                skills_score=scores.get('skills_score', 0.0),
                experience_score=scores.get('experience_score', 0.0),
                location_score=scores.get('location_score', 0.0),
                total_score=result['total_score']
            )
            candidates.append(candidate)
        
        if not candidates:
            logger.info(f"No matching candidates found for job {job_id}")
            return []
            
        logger.info(f"Found {len(candidates)} matching candidates for job {job_id}")
        return candidates

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ranking candidates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rank candidates"
        )