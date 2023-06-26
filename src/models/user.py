"""models/user.py

This file contains the models needed for User interaction
"""
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from config import settings

class User(BaseModel):
    """User class contains the structure of users within the graph database.
    """
    UUID: str
    ScreenName: str
    Email: str
    Phone: Optional[str] = None
    BannerImage:  Optional[str] = None
    ProfileImage: Optional[str] = None

    Blocked: Optional[List[str]] = None
    Admin: Optional[bool] = False
    Private: Optional[bool] = False
    Disabled: Optional[bool] = False
    Banned: Optional[bool] = False

    # Metadata
    JoinDate: Optional[datetime] = datetime.now(settings.TIMEZONE)
    LastSeen: Optional[datetime] = None
    Logins: Optional[List[str]] = None

class BlockedUser(User):
    UUID = "null"
    ScreenName = "Blocked"
    Email = "Blocked"
    Phone = "Blocked"
    BannerImage = "Blocked"
    ProfileImage = "Blocked"
    Blocked = ""


class UserRegister(BaseModel):
    """User class for enabling registration forms.
    """
    screenName: str
    email: str
    password: str
    phone: Optional[str] = None

class UserInDB(User):
    """UserInDB class, used to hide password hash and other private info
    that shouldn't be sent back with request.
    """
    HashedPassword: str
    Salt: str
    SaltPos: int
