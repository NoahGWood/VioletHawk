"""auth/utils.py

VioletHawk API Authentication Utilities

"""
import re
import secrets
import string
from jose import JWTError, jwt
from typing import Optional
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request

from config import settings
from models.user import User, UserInDB
from models.auth import TokenData

# Password Stuff

def CreateSalt(plen: int):
    """CreateSalt - Creates a salt for a password size.
        plen: int - Password Length

        Usage:
            salt, saltPos = CreateSalt(len(password))
    """
    salt = ''.join(secrets.choice(string.ascii_uppercase
                                  + string.ascii_lowercase)
                   for i in range(settings.SALT_SIZE))
    saltPos = secrets.randbelow(plen)
    return salt, saltPos

def SaltPassword(pword:str, salt:str, saltPos:int):
    """SaltPassword - Salts a password and returns the resulting string
        pword: str
        salt: str
        saltPos: int

        Usage:
            salted = SaltPassword(password, salt, saltPos)
            # Or
            salted = SaltPassword(password, CreateSalt(len(password)))
    """
    if len(pword) < saltPos:
        # Wrong password, dump this goober
        return False
    return pword[:saltPos] + salt + pword[saltPos:]

def CreatePasswordHash(pword: str):
    """CreatePasswordHash - Generates a hash of a password string.
        pword: str

        Usage:
            hash = CreatePasswordhash('password') 
    """
    return settings.PWD_CONTEXT.hash(pword)

def VerifyPassword(user:User, plain: str):
    """VerifyPassword - Verifies a plaintext password.
        user: User - use GetUser()
        plain: str - The plaintext password

        Usage:
            if(VerifyPassword(user, password)):
                # Authenticated successfully
    """
    salted = SaltPassword(plain, user.Salt, user.SaltPos)
    return settings.PWD_CONTEXT.verify(salted, user.HashedPassword)

def ValidatePasswordComplexity(pword: str):
    """ValidatePasswordComplexity
        pword: str

        Usage:
            if ValidatePasswordComplexity(password):
                # password is complex
    """
    if re.match(settings.PASSWORD_COMPLEXITY_PATTERN, pword):
        return True
    return False

def ValidateEmail(email: str):
    """ValidateEmail - Determines whether an email address is real or fake
        email: str

        Usage:
            if ValidateEmail(email):
                # Success!
    """
    if re.match(settings.EMAIL_VALIDATE_PATTERN, email):
        return True
    return False


def GetUser(uid: str):
    """GetUser - Retrieves a user by email.
        uid: user.UUID

        Usage:
            user = GetUser(uid)
            if user:
                # User found!
    """
    cypher_search = f"MATCH (user:User) WHERE user.UUID = '{uid}' RETURN user"
    with settings.DB.session() as session:
        user = session.run(query=cypher_search)
        data = user.data()
        if len(data) > 0:
            user_data = data[0]['user']
            print(user_data)
            return UserInDB(**user_data)
    return None

def GetUserByEmail(email: str):
    """GetUserByEmail - Retrieves a user by email.
        email: email

        Usage:
            user = GetUser(email)
            if user:
                # User found!
    """
    cypher_search = f"MATCH (user:User) WHERE user.Email = '{email}' RETURN user"
    with settings.DB.session() as session:
        user = session.run(query=cypher_search)
        data = user.data()
        if len(data) > 0:
            user_data = data[0]['user']
            return UserInDB(**user_data)
    return None

def BlockUser(currentId:str, blockId:str):
    """BlockUser - Blocks a user.
    currentId: User.UUID
    blockId: User.UUID
    """
    cypher = f"""MATCH (user:User)
    WHERE user.UUID = "{currentId}"
    MATCH (blocked:User)
    WHERE blocked.UUID = "{blockId}"
    SET user.Blocked += "{blockId}"
    CREATE (user)-[rel:BLOCKED]->(blocked)
    RETURN user
    """
    with settings.DB.session() as session:
        res = session.run(query=cypher)
        return res.data()[0]["user"]

def AuthenticateUser(email: str, pword: str):
    """AuthenticateUser - Authenticates a user and returns an instance of it.
        email: str
        pword: str

        Usage:
            user = AuthenticateUser('email@email.com', 'password')
            if user:
                # Authentication success!
    """
    user = GetUserByEmail(email)
    if user:
        return user if VerifyPassword(user, pword) else False
    return False


# Token/OAuth Stuff

def CreateAccessToken(data:dict, expires_delta: Optional[timedelta] = None):
    """CreateAccessToken - Creates an access token for OAuth2 flow
        data:dict
        expires_delta: Optional[timedelta] - Overrides server timeout

        Usage:
            access_token = CreateAccessToken(data={"UUID":user.UUID, "IP":"ip_address"})
    """
    to_encode = data.copy()
    expire = datetime.now(settings.TIMEZONE)
    if expires_delta:
        expire += expires_delta
    else:
        expire += timedelta(minutes=settings.TOKEN_LIFETIME_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def ReadToken(token: str):
    """ReadToken returns the token data.
    """
    cred_except = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Could not validate credentials.",
        headers = {"WWW-Authenticate", "Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        uid: str = payload.get('UUID')
        ip: str = payload.get("IP")
        if uid is None or ip is None:
            raise cred_except
        token_data = TokenData(UUID=uid,IP=ip)
    except JWTError as e:
        raise cred_except from e
    return token_data, cred_except

async def GetCurrentUser(token: str = Depends(settings.OAUTH2_SCHEME)):
    """GetCurrentUser - Used to decrypt & return auth tokens.
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    token_data, cred_except = ReadToken(token=token)
    user = GetUser(token_data.UUID)
    if user is None:
        raise cred_except
    return user

async def GetCurrentActiveUser(current: User = Depends(GetCurrentUser)):
    """GetCurrentActiveUser - Used to ensure user account has not been disabled or banned
    """
    if current.Disabled:
        raise HTTPException(status_code=400, detail="User Inactive.")
    if current.Banned:
        raise HTTPException(status_code=400, detail="User Banned.")
    return current

async def GetCurrentActiveUserAllowGuest(token: str = Depends(settings.OAUTH2_SCHEME)):
    """GetCurrentUserAllowGuest """
    if not token:
        return None
    token_data, _ = ReadToken(token=token)
    current = GetUser(token_data.UUID)
    if not current:
        return None
    if current.Disabled:
        raise HTTPException(status_code=400, detail="User Inactive.")
    if current.Banned:
        raise HTTPException(status_code=400, detail="User Banned.")
    return current

async def GetCurrentCookieUser(request: Request):
    """GetCurrentCookieUser - Used to authenticate users via cookie
    """
    if "JWT" in request.cookies:
        return await GetCurrentUser(token=request.cookies["JWT"])
    return None

async def GetCookieUserAllowGuest(request: Request):
    """GetCookieUserAllowGuest - Used to authenticate users via cookie
    while allowing guest access
    """

    if "JWT" in request.cookies:
        try:
            return await GetCurrentActiveUserAllowGuest(token=request.cookies["JWT"])
        except HTTPException as e:
            return None
    return None
