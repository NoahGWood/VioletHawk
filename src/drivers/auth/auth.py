"""auth/auth.py

VioletHawk API Authentication Routes
"""

import uuid
from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional

from config import settings
from drivers.auth import utils
from models.auth import Token, TokenData
from models.user import User, UserRegister
from datetime import datetime, timedelta

router = APIRouter()
ROUTE = {
    "router":router,
    "prefix":settings.AUTH_ENDPOINT,
    "tags":["Auth"]
}

# Registration Endpoint

@router.post("/register")
async def register_user(request:Request, user:UserRegister):
    if not settings.ENABLE_ACCOUNT_CREATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account registration disabled."
        )
    if not utils.ValidateEmail(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email {user.email} is not a valid email address.",
        )
    # Check password complexity
    if settings.FORCE_COMPLEX and not utils.ValidatePasswordComplexity(user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password {user.password} must have a minimum of 8 characters, 1 upper case, 1 lower case, 1 number, and 1 special char.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    # create a salt
    salt, saltPos = utils.CreateSalt(len(user.password))
    salted = utils.SaltPassword(user.password, salt, saltPos)
    # Hash the password
    phash = utils.CreatePasswordHash(salted)
    attributes = {
        "UUID":str(uuid.uuid4()),
        "ScreenName":user.screenName,
        "Email":user.email,
        "Phone":user.phone,
        "Admin":False,
        "Disabled":False,
        "Banned":False,
        "JoinDate":datetime.now(settings.TIMEZONE),
        "LastSeen":datetime.now(settings.TIMEZONE),
        "Logins":[request.client.host],
        "HashedPassword": phash,
        "Salt": salt,
        "SaltPos": saltPos
    }
    cypher = "CREATE (user:User $params) RETURN user"
    with settings.DB.session() as session:
        if utils.GetUser(user.UUID):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Operation not permitted, user with email: {user.email} already exists.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        # Otherwise, create a new user
        response = session.run(query=cypher, parameters={
            'params': attributes
        })
        user_data = response.data()[0]['user']

    return User(**user_data)

@router.post("/token", response_model=Token)
async def login_access_token(request:Request, form_data: OAuth2PasswordRequestForm = Depends(), expires: Optional[timedelta] = None):
    if not settings.ENABLE_BEARER_AUTH:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Token Authentication Has Been Disabled")

    user = utils.AuthenticateUser(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    if expires:
        token = utils.CreateAccessToken(
            data={"UUID": user.UUID, "IP":request.client.host}, expires_delta=expires)
    else:
        token = utils.CreateAccessToken(data={"UUID": user.UUID, "IP":request.client.host})
    return {"access_token": token, "token_type": "bearer"}