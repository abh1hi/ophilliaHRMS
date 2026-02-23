from dataclasses import dataclass
from fastapi import Query


@dataclass
class PaginationParams:
    skip: int = Query(default=0, ge=0, description="Number of records to skip")
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of records to return")
