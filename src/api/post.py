"""onyx/blog/post.py

This file handles blog post functionality for files in the Onyx Salamander CMS
"""
import uuid
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
# Import utilities for database access & File model

from config import settings
from models.post import Post
from drivers.auth.utils import GetCurrentActiveUser, GetCurrentActiveUserAllowGuest, GetCookieUserAllowGuest
from models.user import User
from api.file import create_file

# Setup API Router
router = APIRouter()

ROUTE = {
    "router": router,
    "prefix": "/post",
    "tags": ["Post"]
}


def GetPostsOnSub(title: str, limit: int = 25, likes: bool = False, user: User = None):
    """Returns all posts attached to a sub
    """
    if likes and user:
        cypher = """MATCH (post:Post)-[r:ON]->(n {Title:$title})
        OPTIONAL  MATCH (user:User {UUID:$uid})-[l:LIKES]->(p {UUID: post.UUID})
        OPTIONAL  MATCH (user2:User {UUID:$uid})-[d:DISLIKES]->(p2 {UUID: post.UUID})
        RETURN post, l, d
        ORDER BY post.ModifiedDate DESC
        LIMIT $limit
        """
        print(cypher)
        posts = []
        with settings.DB.session() as session:
            res = session.run(query=cypher, parameters={"title": title,
                                                        "limit": limit,
                                                        "uid": user.UUID}).data()
            for each in res:
                p = Post(**each["post"])
                if each["l"]:
                    p.LIKED = True
                elif each["d"]:
                    p.DISLIKED = True
                posts.append(p)
        return posts
    else:
        cypher = """MATCH (post:Post)-[r:ON]->(n {Title: $title})
        RETURN post
        ORDER BY post.ModifiedDate DESC
        LIMIT $limit
        """
        posts = []
        with settings.DB.session() as session:
            res = session.run(query=cypher, parameters={
                              "title": title, "limit": limit}).data()
            for each in res:
                posts.append(Post(**each["post"]))
        return posts


def GetPost(UUID: Optional[str] = None,
            title: Optional[str] = None,
            user: Optional[User] = None):
    if UUID:
        cypher_search = f"MATCH (post:Post) WHERE post.UUID = '{UUID}' "
    elif title:
        cypher_search = f"MATCH (post:Post) WHERE post.Title = '{title}'"

    if not user:
        cypher_search += "AND post.Published = True"
    elif not user.Admin:
        cypher_search += f"AND post.Owner = '{user.UUID}'"

    cypher_search += " RETURN post"

    with settings.DB.session() as session:
        result = session.run(query=cypher_search).data()
        if result:
            return Post(**result[0]["post"])

# Create


@router.post("/create", response_model=Post)
async def create_post(title: str, content: str,
                      published: Optional[bool] = False,
                      subTitle: Optional[str] = None,
                      tags: Optional[List[str]] = None,
                      keywords: Optional[List[str]] = None,
                      # NOT USED:
                      _: Optional[List[str]] = None, 
                      # _ Added because /docs can't send proper request without it
                      # Removing gives the error: Did not find CR at end of boundary (59)
                      # IDFK what that even means ¯\_(ツ)_/¯
                      linkedFiles: Optional[List[UploadFile]] = None,
                      user: User = Depends(GetCurrentActiveUser)):
    date = str(datetime.now(settings.TIMEZONE))
    attributes = {
        "UUID": str(uuid.uuid4()),
        "Title": title,
        "Content": content,
        "Creator": user.UUID,
        "Modifier": user.UUID,
        "Owner": user.UUID,
        "CreatedDate": date,
        "ModifiedDate": date,
        "Votes": 0,
    }
    if published:
        attributes["Published"] = published
        attributes["PublishedDate"] = date
    if tags:
        attributes["Tags"] = tags
    if keywords:
        attributes["Keywords"] = keywords

    cypher_match = f"""MATCH (user:User)
    WHERE user.UUID = "{user.UUID}"
    """
    cypher_create = """CREATE (post:Post $params)
    CREATE (user)-[relationship:OWNS]->(post)
    CREATE (user)-[relationship2:AUTHOR]->(post)
    """
    if linkedFiles:
        files = []
        # Upload each file and attach to post
        i = 0
        for file in linkedFiles:
            f = await create_file(file, user=user)
            files.append(f.UUID)
            if f:
                cypher_match += f"""
                MATCH (file{i}:File)
                WHERE file{i}.UUID = "{f.UUID}"
                """
                cypher_create += f"""
                CREATE (post)-[linksTofile{i}:ATTACHES]->(file{i})
                """
                i += 1
        attributes["Files"] = files # So we don't HAVE to query relationships
    
    if subTitle:
        cypher_match += f"""MATCH (v:Sub)
        WHERE v.Title = "{subTitle}"
        """
        cypher_create += """CREATE (post)-[relationship3:ON]->(v)
        """

    cypher = cypher_match + cypher_create + " RETURN post "
    print(cypher)
    with settings.DB.session() as session:
        res = session.run(query=cypher, parameters={"params": attributes})
        post = Post(**res.data()[0]["post"])
    return post

# Read


@router.get("/read", response_model=Optional[Post])
async def read_post(UUID: Optional[str] = None,
                    title: Optional[str] = None,
                    user: User = Depends(GetCurrentActiveUserAllowGuest)):
    return GetPost(UUID=UUID, title=title, user=user)

# List


@router.get("/list", response_model=List[Post])
async def list_posts(limit: int = 25,
                     order_by: Optional[str] = None,
                     user: User = Depends(GetCurrentActiveUserAllowGuest)):
    if not user:
        cypher = f"MATCH (post:Post) WHERE post.Published = True RETURN post LIMIT {limit}"
    elif not user.Admin:
        cypher = f"""MATCH (post:Post) WHERE post.Published = True
        OR post.Owner = "{user.UUID}"
        OR post.Creator = "{user.UUID}"
        RETURN post
        LIMIT {limit}
        """
    elif user.Admin == True:
        cypher = "MATCH (post:Post) RETURN post LIMIT {limit}"

    if order_by:
        cypher += f" ORDER BY post.{order_by}"
    posts = []
    with settings.DB.session() as session:
        res = session.run(query=cypher).data()
        for each in res:
            post = Post(**each["post"])
            posts.append(post)
    return posts

# Update


@router.post("/update/{UUID}", response_model=Post)
async def update_post(UUID: str,
                      attributes: dict,
                      user: User = Depends(GetCurrentActiveUser)):
    date = str(datetime.now(settings.TIMEZONE))
    post = GetPost(UUID=UUID, user=user)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not have write read/write access to the post or it does not exist."
        )
    cypher = f"""MATCH (post:Post)
    WHERE post.UUID = "{UUID}"
    SET post += $attributes
    SET post.Modifier = "{user.UUID}"
    SET post.ModifiedDate = "{date}"
    """
    if "Published" in attributes.keys():
        if attributes["Published"]:
            cypher += """SET post.Published = True
            SET post.PublishedDate = "{date}"
            """
        else:
            cypher += "SET post.Published = False"
        del attributes["Published"]
    cypher += "RETURN post"
    for key in attributes.keys():
        if key in settings.BASE_PROPERTIES:
            del attributes[key]
    with settings.DB.session() as session:
        res = session.run(query=cypher, parameters={"attributes": attributes})
        updated = Post(**res.data()[0]["post"])
    return updated

# Delete


@router.post("/delete/{UUID}")
async def delete_post(UUID: str,
                      user: User = Depends(GetCurrentActiveUser)):
    post = GetPost(UUID=UUID, user=user)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not have write read/write access to the post, or it does not exist."
        )
    cypher = f"""MATCH (post:Post)
    WHERE post.UUID = "{UUID}"
    DETACH DELETE post
    """

    with settings.DB.session() as session:
        res = session.run(query=cypher).data()
    return res or {
        "response": f"Post {UUID} was successfully deleted."
    }


@router.post("/upvote/{UUID}", response_model=Post)
async def upvote_post(UUID: str,
                      user: User = Depends(GetCookieUserAllowGuest)):
    post = GetPost(UUID=UUID)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Post not found."
        )
    liked = False
    disliked = False
    with settings.DB.session() as session:
        l = session.run(query=f"""MATCH (u:User)-[rel]->(p:Post) WHERE
        u.UUID = "{user.UUID}" AND p.UUID = "{UUID}"
        RETURN rel""").data()
        print(l)
        for each in l:
            if "DISLIKES" in str(each):
                disliked = True
            if "LIKES" in str(each):
                liked = True
    if liked:
        cypher = f"""
        MATCH (user:User)-[likes:LIKES]->(post:Post) WHERE
        user.UUID = "{user.UUID}" AND post.UUID = "{UUID}"
        SET post.Votes = post.Votes - 1
        DETACH DELETE likes
        """
    if disliked:
        cypher = f"""MATCH (user:User)-[dislikes:DISLIKES]->(post:Post) WHERE
        user.UUID = "{user.UUID}" AND post.UUID = "{UUID}"
        CREATE (user)-[relationship:LIKES]->(post)
        SET post.Votes = post.Votes + 2
        DETACH DELETE dislikes
        """
    if not liked and not disliked:
        cypher = f"""
        MATCH (user:User) WHERE user.UUID = "{user.UUID}"
        MATCH (post:Post) WHERE post.UUID = "{UUID}"
        CREATE (user)-[relationship:LIKES]->(post)
        SET post.Votes = post.Votes + 1
        """
    cypher += " RETURN post"
    print(cypher)
    with settings.DB.session() as session:
        res = session.run(query=cypher).data()
        return Post(**res[0]["post"])


@router.post("/downvote/{UUID}", response_model=Post)
async def downvote_post(UUID: str,
                        user: User = Depends(GetCookieUserAllowGuest)):
    post = GetPost(UUID=UUID)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Post not found."
        )
    liked = False
    disliked = False
    with settings.DB.session() as session:
        l = session.run(query=f"""MATCH (u:User)-[rel]->(p:Post) WHERE
        u.UUID = "{user.UUID}" AND p.UUID = "{UUID}"
        RETURN rel""").data()
        print(l)
        for each in l:
            if "DISLIKES" in str(each):
                disliked = True
            if "LIKES" in str(each):
                liked = True
    if liked:
        cypher = f"""
        MATCH (user:User)-[likes:LIKES]->(post:Post) WHERE
        user.UUID = "{user.UUID}" AND post.UUID = "{UUID}"
        CREATE (user)-[relationship:DISLIKES]->(post)
        SET post.Votes = post.Votes - 2
        DETACH DELETE likes
        """
    if disliked:
        cypher = f"""MATCH (user:User)-[dislikes:DISLIKES]->(post:Post) WHERE
        user.UUID = "{user.UUID}" AND post.UUID = "{UUID}"
        SET post.Votes = post.Votes + 1
        DETACH DELETE dislikes
        """
    if not liked and not disliked:
        cypher = f"""
        MATCH (user:User) WHERE user.UUID = "{user.UUID}"
        MATCH (post:Post) WHERE post.UUID = "{UUID}"
        CREATE (user)-[relationship:DISLIKES]->(post)
        SET post.Votes = post.Votes - 1
        """
    cypher += " RETURN post"
    print(cypher)
    with settings.DB.session() as session:
        res = session.run(query=cypher).data()
        return Post(**res[0]["post"])
