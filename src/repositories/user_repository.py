"""
User repository for user-related database operations.
Implements the Repository pattern for user data access.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .base import BaseRepository
from ..core.models import User, UserCreate, UserUpdate, UserInDB, UserRole


class UserRepository(BaseRepository[UserModel, UserCreate, UserUpdate]):
    """User repository for user data operations."""
    
    def get_by_username(self, username: str) -> Optional[UserModel]:
        """Get user by username."""
        return self.db.query(UserModel).filter(
            and_(
                UserModel.username == username.lower(),
                UserModel.is_active == True
            )
        ).first()
    
    def get_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email."""
        return self.db.query(UserModel).filter(
            and_(
                UserModel.email == email.lower(),
                UserModel.is_active == True
            )
        ).first()
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """Get all active users."""
        return self.db.query(UserModel).filter(
            UserModel.is_active == True
        ).offset(skip).limit(limit).all()
    
    def get_users_by_role(self, role: UserRole, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """Get users by role."""
        return self.db.query(UserModel).filter(
            and_(
                UserModel.role == role.value,
                UserModel.is_active == True
            )
        ).offset(skip).limit(limit).all()
    
    def is_username_taken(self, username: str) -> bool:
        """Check if username is already taken."""
        return self.db.query(UserModel).filter(
            UserModel.username == username.lower()
        ).first() is not None
    
    def is_email_taken(self, email: str) -> bool:
        """Check if email is already taken."""
        return self.db.query(UserModel).filter(
            UserModel.email == email.lower()
        ).first() is not None
    
    def deactivate_user(self, user_id: int) -> Optional[UserModel]:
        """Deactivate a user."""
        user = self.get(user_id)
        if user:
            user.is_active = False
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def activate_user(self, user_id: int) -> Optional[UserModel]:
        """Activate a user."""
        user = self.get(user_id)
        if user:
            user.is_active = True
            self.db.commit()
            self.db.refresh(user)
        return user
