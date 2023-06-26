"""api/sub.py

This file handles CRUD functionality for Subreddits in the
VioletHawk platform
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile

# Import utilities for database access & Sub model
from config import settings
from drivers.auth.utils import GetCurrentActiveUser
from models.user import User
from models.sub import Sub
from api.file import create_file

# Setup API Router
router = APIRouter()
ROUTE = {
    "router": router,
    "prefix": "/v",
    "tags": ["Sub"]
}


def GetSub(title):
    cypher_search = f"MATCH (v:Sub) WHERE v.Title = '{title}' RETURN v"

    with settings.DB.session() as session:
        result = session.run(query=cypher_search).data()
        if result:
            return Sub(**result[0]["v"])


@router.post("/create", response_model=Sub)
async def create_sub(title: str, headline: str,
                      description: Optional[str] = None,
                      keywords: Optional[List[str]] = None,
                      private: Optional[bool] = False,
                      banner: Optional[UploadFile] = None,
                      user: User = Depends(GetCurrentActiveUser)
                      ):
    """create_sub - Creates a new sub"""
    # Check that Sub does not exist
    if GetSub(title=title):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Operation not permitted. Sub with title '{title}' already exists.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    date = str(datetime.now(settings.TIMEZONE))

    attributes = {
        "Title": title,
        "Headline": headline,
        "Creator": user.UUID,
        "Owner": user.UUID,
        "Private": private,
        "CreatedDate": date,
        "Subscribers":1,
    }
    if description:
        attributes["Description"] = description
    if banner:
        # Upload file
        bannerImage = await create_file(file=banner,description="Banner Image",
                    user=user)
        attributes["BannerImage"] = bannerImage.UUID
    if keywords:
        attributes["Keywords"] = keywords

    cypher = f"""MATCH (user:User) WHERE user.UUID = "{user.UUID}"
    CREATE (v:Sub $params)
    CREATE (user)-[relationship:OWNS]->(v)
    RETURN v"""

    with settings.DB.session() as session:
        res = session.run(query=cypher, parameters={"params": attributes})
        print(res)
        sub = res.data()[0]
        sub = sub["v"]
    print(sub)
    return Sub(**sub)

# Read Subs

@router.post("/read/", response_model=Sub)
async def read_sub(title):
    p = GetSub(title=title)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nothing found for v/{title}"
        )
    return p

# List Subs

@router.get("/list/subs", response_model=List[Sub])
async def list_subs(limit: int = 25):
    cypher = f"MATCH (v:Sub) return v LIMIT {limit}"
    out = []
    with settings.DB.session() as session:
        result = session.run(query=cypher)
        rel = result.data()
        print(rel[0]["v"])
        for sub in rel:
            out.append(Sub(**sub["v"]))
    return out

# Update Subs


@router.put("/update/{title}", response_model=Sub)
async def update_sub(title: str,
                      attributes: dict,
                      user: User = Depends(GetCurrentActiveUser)):
    time = str(datetime.now(settings.TIMEZONE))
    sub = GetSub(title)
    if sub and not sub.Owner == user.UUID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"You do not have write access to v/{title}.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    cypher = f"""MATCH (v:Sub) WHERE v.TITLE = "{title}"
    SET v += $attributes
    SET v.Modifier = "{user.UUID}"
    SET v.ModifiedDate = "{time}"
    RETURN v
    """
    for key in attributes.keys():
        if key in settings.BASE_PROPERTIES:
            del attributes[key]
    with settings.DB.session() as session:
        if not user.Admin:
            relate = session.run(query=f"""MATCH (user:User)-[relationship]->(v:Sub)
            WHERE user.UUID = "{user.UUID}" AND sub.Title = "{title}"
            RETURN relationship
            """).data()[0]
            if relate:
                if "OWNS" not in str(relate) and "CanModify" not in str(relate):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"You do not have write access to v/{title}.",
                        headers={"WWW-Authenticate": "Bearer"}
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"You do not have write access to v/{title}.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        update = session.run(query=cypher, parameters={
                             "attributes": attributes}).data()[0]
    return Sub(**update["v"])

# Delete Sub


@router.post("/delete/{title}")
async def delete_sub(title: str,
                      user: User = Depends(GetCurrentActiveUser)):
    sub = GetSub(title)
    if sub and not sub.Owner == user.UUID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"You do not have write access to v/{title}.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    cypher = f"""MATCH (v:Sub) WHERE v.Title = "{title}"
    DETACH DELETE sub
    """
    with settings.DB.session() as session:
        result = session.run(query=cypher)
        rel = result.data()
    # rel should be empty, if not this _should_ return an error message
    return rel or {
        "response": f"Sub {title} was successfully deleted."
    }