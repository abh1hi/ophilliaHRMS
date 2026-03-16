from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

DataT = TypeVar('DataT')

class ErrorDetail(BaseModel):
    code: str
    message: str

class APIResponse(BaseModel, Generic[DataT]):
    success: bool
    data: Optional[DataT] = None
    meta: Optional[Any] = None
    error: Optional[ErrorDetail] = None

class PaginatedMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int

class PaginatedAPIResponse(BaseModel, Generic[DataT]):
    success: bool
    data: Optional[list[DataT]] = None
    meta: Optional[PaginatedMeta] = None
    error: Optional[ErrorDetail] = None
