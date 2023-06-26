"""views/sub.py

This file holds the views for CRUD operations on
subreddits
"""

import uuid
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from config import settings
from models.user import User
from models.sub import Sub
from drivers.auth.utils import GetCookieUserAllowGuest
from api.sub import read_sub, create_sub
from api.post import create_post, GetPostsOnSub, GetPost
#from sub import read_page, create_page
#from post import GetPostsOnPage, create_blog_post, GetBlogPost

router = APIRouter()
ROUTE = {
    "router":router,
    "prefix":"/v",
    "tags":["Sub"]
}

@router.get("/{title}", response_class=HTMLResponse)
async def read_subreddit(request:Request,
                         title:str,
                         user:User = Depends(GetCookieUserAllowGuest)):
    sub = await read_sub(title)
    posts = GetPostsOnSub(title=title,likes=True,user=user)
    return settings.TEMPLATES.TemplateResponse("sub.html", context={"request":request,"user":user,"sub":sub,"posts":posts})

@router.post("/{subTitle}/new", response_class=HTMLResponse)
async def post_subreddit(request:Request,
                         subTitle:str,
                         file: Optional[List[UploadFile]] = File(),
                         title = Form(),
                         content = Form(""),
                         user:User = Depends(GetCookieUserAllowGuest)):
    print(file[0].filename)
    if not user:
        return RedirectResponse("/login",status_code=status.HTTP_401_UNAUTHORIZED)
    if file[0].filename:
        await create_post(title=title, content=content, published=True,
                          subTitle=subTitle, linkedFiles=file, user=user)
    else:
        await create_post(title=title, content=content, published=True,
                          subTitle=subTitle, user=user)
    sub = await(read_sub(subTitle))
    posts = GetPostsOnSub(title=title,likes=True,user=user)
    return settings.TEMPLATES.TemplateResponse("sub.html", context={"request":request,"user":user,"sub":sub,"posts":posts})

