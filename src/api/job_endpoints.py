from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.services.postgres_handler import get_db
from src.services.mongo_handler import MongoHandler
from src.api.auth_endpoints import get_current_user, require_user_type
from src.schemas.auth_schema import UserType, UserResponse
from src.utils.text_parser import TextParser
from src.utils.text_embedder import TextEmbedder
from src.database import job_crud
from src.core.custom_logger import CustomLogger
from src.schemas.mongo_schema import JobDocument
import src.schemas.job_schema as schemas
from datetime import datetime

router = APIRouter(tags=["Jobs"])
logger = CustomLogger("JobEndpoints")
mongo_handler = MongoHandler(logger=logger)

@router.post("/create_job", response_model=schemas.JobResponse)
@require_user_type([UserType.RECRUITER])
async def create_job(
    job: schemas.JobCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new job posting."""
    logger.info(f"Job creation attempt by recruiter: {current_user.username}")
    
    try:
        # Store raw JD in MongoDB
        job_doc = JobDocument(
            recruiter_id=current_user.id,
            raw_text=job.job_description,
            title=job.title,
            company=job.company,
            metadata={
                "location": job.location,
                "required_experience": job.required_experience,
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        mongo_doc_id = mongo_handler.insert_one(
            collection="raw_jobs",
            document=job_doc.dict()
        )
        
        # Parse job description
        text_parser = TextParser(logger=logger)
        parsed_jd = text_parser.parse_text(job.job_description, parse_type="job")
        if not parsed_jd:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to parse job description"
            )
        
        # Generate embeddings for job requirements
        text_embedder = TextEmbedder(logger=logger)
        skills_text = " ".join(parsed_jd.get("skills", {}).get("technical", []))
        jd_vector = text_embedder.embed_text(skills_text)
        
        # Save parsed data to PostgreSQL
        db_job = job_crud.create_job(
            db=db,
            recruiter_id=current_user.id,
            title=job.title,
            company=job.company,
            location=job.location,
            parsed_jd=parsed_jd,
            jd_vector=jd_vector,
            required_experience=job.required_experience,
            mongodb_id=str(mongo_doc_id)
        )
        
        logger.info(f"Successfully created job posting: {job.title}")
        return db_job
        
    except Exception as e:
        logger.error(f"Error creating job posting: {str(e)}")
        # Cleanup MongoDB document if needed
        if 'mongo_doc_id' in locals():
            try:
                mongo_handler.delete_one("raw_jobs", {"_id": mongo_doc_id})
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup MongoDB document: {cleanup_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job posting"
        )

@router.get("/jobs/{job_id}", response_model=schemas.JobResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a job posting by ID."""
    db_job = job_crud.get_job(db, job_id)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Fetch raw text from MongoDB if needed
    if db_job.mongodb_id:
        raw_job = mongo_handler.find_one(
            collection="raw_jobs",
            query={"_id": ObjectId(db_job.mongodb_id)}
        )
        db_job.raw_text = raw_job.get("raw_text") if raw_job else None
    
    return db_job