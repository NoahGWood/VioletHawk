"""models/auth.py

This file contains the models necessary for implementing authentication.
"""
from typing import Optional, List
from pydantic import BaseModel

class Token(BaseModel):
    """Token represents a bearer token used to authenticate
    a user to the VioletHawk platform
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """TokeData contains information about the token that
    is used to authenticate a user to the VioletHawk platform.
    """
    UUID: Optional[str]=None
    IP: Optional[str]=None
    # Add other stuff for browser fingerprinting as we implement it