from fastapi import APIRouter

from app.api.v1 import students, classes, guardians

api_router = APIRouter()

api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(classes.router, prefix="/classes", tags=["classes"])
api_router.include_router(guardians.router, prefix="/guardians", tags=["guardians"])
