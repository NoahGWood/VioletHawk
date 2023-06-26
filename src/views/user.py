"""views/user.py

This file holds the views for CRUD operations on
Users
"""

import uuid
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from config import settings
from models.user import User, BlockedUser
from models.sub import Sub
from drivers.auth.utils import GetCookieUserAllowGuest, GetUser
from api.sub import read_sub, create_sub
from api.post import create_post, GetPostsOnSub, GetPost
#from sub import read_page, create_page
#from post import GetPostsOnPage, create_blog_post, GetBlogPost

router = APIRouter()
ROUTE = {
    "router":router,
    "prefix":"/user",
    "tags":["User"]
}

@router.get("/", response_class=RedirectResponse)
async def get_home(request:Request):
    return RedirectResponse("/")

@router.get("/{UUID}", response_class=HTMLResponse)
async def get_user(request:Request, UUID:str, user:User = Depends(GetCookieUserAllowGuest)):
    viewed = GetUser(UUID)
    print(viewed)
    if viewed:
        if user:
            if user.UUID in viewed.Blocked or viewed.UUID in user.Blocked:
                viewed = BlockedUser()
        if viewed.Private:
            viewed = BlockedUser()
    return settings.TEMPLATES.TemplateResponse("user.html", context={"request":request,"user":user,"viewed":viewed})