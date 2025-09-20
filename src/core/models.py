"""
Domain models for Mini RAG application.
Defines the core business entities and data transfer objects.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator


class UserRole(str, Enum):
    """User roles in the system."""
    USER = "user"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user model."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: Optional[str] = Field(None, description="User email")
    full_name: Optional[str] = Field(None, description="Full name")
    is_active: bool = Field(default=True, description="Whether user is active")


class UserCreate(UserBase):
    """User creation model."""
    password: str = Field(..., min_length=6, description="Password")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Username must contain only alphanumeric characters")
        return v.lower()


class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """User model as stored in database."""
    id: int
    hashed_password: str
    role: UserRole
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class User(UserBase):
    """User model for API responses."""
    id: Optional[int] = None
    role: str = Field(default="admin", description="User role")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """User login model."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class Token(BaseModel):
    """Token response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None


class DocumentChunk(BaseModel):
    """Document chunk model."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    source: str
    page_number: Optional[int] = None
    chunk_index: int


class Document(BaseModel):
    """Document model."""
    id: str
    filename: str
    content: str
    chunks: List[DocumentChunk]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class QuestionRequest(BaseModel):
    """Question request model."""
    query: str = Field(..., min_length=1, max_length=1000, description="Question to ask")
    top_k: Optional[int] = Field(default=None, ge=1, le=20, description="Number of relevant chunks to retrieve")
    stream: bool = Field(default=False, description="Whether to stream the response")


class QuestionResponse(BaseModel):
    """Question response model."""
    answer: str = Field(..., description="Generated answer")
    sources: List[Dict[str, Any]] = Field(..., description="Source documents and chunks")
    model_used: str = Field(..., description="Model used for generation")
    processing_time: float = Field(..., description="Processing time in seconds")


class ModelInfo(BaseModel):
    """Model information model."""
    name: str
    size: str
    family: str
    parameter_size: str
    quantization_level: str


class ModelsResponse(BaseModel):
    """Models response model."""
    available_models: List[ModelInfo]
    current_model: str
    embedding_model: str


class ModelChangeRequest(BaseModel):
    """Model change request model."""
    model_name: str = Field(..., description="Name of the model to switch to")


class ModelChangeResponse(BaseModel):
    """Model change response model."""
    message: str
    previous_model: str
    current_model: str


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    mode: str
    ollama: str
    qdrant: str
    documents_indexed: int
    message: str


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Success response model."""
    message: str
    data: Optional[Dict[str, Any]] = None


class FileUploadResponse(BaseModel):
    """File upload response model."""
    message: str
    files_saved: List[str]
    total_files: int


class IndexResponse(BaseModel):
    """Index operation response model."""
    message: str
    indexed_count: int
    total_chunks: int
