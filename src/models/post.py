"""models/post.py

This model represents a post within the VioletHawk platform.
"""

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class Post(BaseModel):
    UUID: str
    Title: str
    Content: Optional[str] = None
    Published: Optional[bool] = False
    Tags: Optional[List[str]] = None

    # Linked Files
    Files: Optional[List[str]] = None

    # User Metadata
    Owner: Optional[str] = None  # Who owns the post

    # Datetime Metadata
    CreatedDate: Optional[datetime] = None
    ModifiedDate: Optional[datetime] = None

    # Metadata
    Keywords: Optional[List[str]] = None
    Votes: Optional[int] = 0

    # Temporary fields (not saved to DB)
    LIKED: Optional[bool] = None
    DISLIKED: Optional[bool] = None