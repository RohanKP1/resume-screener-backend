from sqlalchemy.orm import Session
from src.models.job_model import Job
from src.core.custom_logger import CustomLogger

logger = CustomLogger("JobCRUD")

def create_job(
    db: Session,
    recruiter_id: int,
    title: str,
    company: str,
    location: str,
    parsed_jd: dict,
    jd_vector: list,
    required_experience: int,
    mongodb_id: str
):
    try:
        db_job = Job(
            recruiter_id=recruiter_id,
            title=title,
            company=company,
            location=location,
            parsed_jd=parsed_jd,
            jd_vector=jd_vector,
            required_experience=required_experience,
            mongodb_id=mongodb_id
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        logger.info(f"Created job posting: {title} at {company}")
        return db_job
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        db.rollback()
        raise

def get_job(db: Session, job_id: int):
    return db.query(Job).filter(Job.id == job_id).first()

def get_recruiter_jobs(db: Session, recruiter_id: int, skip: int = 0, limit: int = 100):
    return db.query(Job)\
        .filter(Job.recruiter_id == recruiter_id)\
        .offset(skip)\
        .limit(limit)\
        .all()

def update_job(db: Session, job_id: int, **kwargs):
    try:
        db_job = get_job(db, job_id)
        if db_job:
            for key, value in kwargs.items():
                setattr(db_job, key, value)
            db.commit()
            db.refresh(db_job)
            logger.info(f"Updated job {job_id}")
            return db_job
    except Exception as e:
        logger.error(f"Error updating job: {e}")
        db.rollback()
        raise