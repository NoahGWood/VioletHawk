"""models/comment.py

This file contains the Comment model for the VioletHawk
Platform.
"""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from config import settings

class Comment(BaseModel):
    UUID: str
    Message: str
    Files: Optional[List[str]] = None
    Edited: Optional[bool] = False
    # Metadata
    Creator: Optional[str] = None
    Votes: Optional[int] = 0
    Created: Optional[datetime] = datetime.now(settings.TIMEZONE)

