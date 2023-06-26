"""models/page.py

This file contains the Page models for the Onyx Salamander CMS database.
"""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from config import settings

class Sub(BaseModel):
    """Sub represents a single sub-forum in the VioletHawk platform.
    """
    Title: str
    Headline: Optional[str] = None
    Description: Optional[str] = None
    About: Optional[str] = None
    Rules: Optional[str] = None
    BannerImage: Optional[str] = None

    Creator: Optional[str] = None
    Owner: Optional[str] = None
    Private: Optional[bool] = False

    # Metadata
    CreatedDate: Optional[datetime] = datetime.now(settings.TIMEZONE)
    Subscribers: Optional[int] = 0
    Keywords: Optional[List[str]] = None

