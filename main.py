from fastapi import FastAPI
from src.api.auth_endpoints import router as auth_router
from src.api.candidate_endpoints import router as candidate_router
from src.api.job_endpoints import router as job_router

app = FastAPI()

# Mount the router at /auth
app.include_router(auth_router, prefix="/auth")

# Mount the router at /job
app.include_router(job_router, prefix="/job")

# Mount the router at /candidate
app.include_router(candidate_router, prefix="/candidate")



