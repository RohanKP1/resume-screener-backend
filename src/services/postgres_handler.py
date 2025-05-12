from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.core.config import Config
from src.core.custom_logger import CustomLogger
from contextlib import contextmanager

# Initialize logger
logger = CustomLogger("PostgresHandler")

# Create these variables but don't initialize the engine yet
Base = declarative_base()
engine = None
SessionLocal = None

def create_database():
    """Create database if it doesn't exist"""
    default_url = f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/postgres"
    
    try:
        # Connect to default postgres database
        temp_engine = create_engine(default_url)
        
        with temp_engine.connect() as conn:
            # Commit any existing transaction
            conn.execute(text("commit"))
            
            # Check if database exists
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": Config.POSTGRES_DB}
            ).scalar()
            
            if not exists:
                # Create database if it doesn't exist
                conn.execute(text("commit"))
                conn.execute(text(f"CREATE DATABASE {Config.POSTGRES_DB}"))
                logger.info(f"Created database {Config.POSTGRES_DB}")
    
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise
    finally:
        temp_engine.dispose()

def setup_db():
    """Initialize database connection and session factory"""
    global engine, SessionLocal
    
    if engine is None:
        try:
            # Ensure database exists
            create_database()
            
            # Get full database URL
            database_url = Config.get_postgres_url()
            logger.info(f"Initializing database connection to {database_url}")
            
            # Create engine and session factory
            engine = create_engine(database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            logger.info("Database connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            if engine:
                engine.dispose()
            raise

def get_db():
    """
    Get database session for FastAPI dependency injection.
    Returns the session object directly, not a context manager.
    """
    if SessionLocal is None:
        setup_db()
    
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        logger.error(f"Error getting database session: {e}")
        db.close()
        raise

@contextmanager
def db_session():
    """Context manager for database sessions (for internal use)"""
    if SessionLocal is None:
        setup_db()
        
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
