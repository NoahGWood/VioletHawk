"""api/user.py

VioletHawk API User Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Request, Depends

from config import settings
from drivers.auth.utils import GetCurrentActiveUser, GetUser
from models.user import User
from api.file import create_file, delete_file
from datetime import datetime

router = APIRouter()
ROUTE = {
    "router":router,
    "prefix":"/user",
    "tags":["User"]
}

@router.put("/update", response_model=User)
@router.put("/update/{UUID}", response_model=User)
async def update_user(attributes: dict,
                      UUID:str=None,
                      user: User = Depends(GetCurrentActiveUser)):
    uId = user.UUID
    if UUID:
        if not user.Admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        uId = UUID
    cypher = f"""MATCH (user:User) WHERE user.UUID = "{uId}"
    SET user += $attributes
    RETURN user
    """
    with settings.DB.session() as session:
        res= session.run(query=cypher, parameters={"attributes":attributes})
        return User(**res[0]["user"])
    
@router.get("/delete")
@router.get("/delete/{UUID}")
async def delete_user(attributes: dict,
                      UUID:str=None,
                      user: User = Depends(GetCurrentActiveUser)):
    uId = user.UUID
    if UUID:
        if not user.Admin and not user.UUID == UUID:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        uId = UUID
    cypher = f"""MATCH (user:User) WHERE user.UUID = "{uId}"
    MATCH (comment:Comment) WHERE comment.Creator = "{uId}"
    MATCH (post:Post) WHERE post.Owner = "{uId}"
    MATCH (sub:Sub) WHERE sub.Owner = "{uId}"
    MATCH (file:File) WHERE file.Creator = "{uId}"
    DETACH DELETE user, comment, post
    RETURN file
    """
    with settings.DB.session() as session:
        res= session.run(query=cypher).data()
        for each in res:
            # Delete files
            delete_file(each["file"])

    return res or {
        "response": f"User was successfully deleted."
    }
    
