from fastapi import APIRouter, Request, Depends
from fastapi import HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse

from config import settings
from models.user import User, UserRegister
from drivers.auth import utils
from drivers.auth import auth

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
async def get_login(request:Request, user:User = Depends(utils.GetCookieUserAllowGuest)):
    if user:
        return RedirectResponse("/")
    return settings.TEMPLATES.TemplateResponse("login.html",
                                               {"request":request,
                                                "user":user})

@router.post("/login")
async def post_login_page(request: Request,
                          email: str = Form(),
                          password: str = Form()):
    user = utils.AuthenticateUser(email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password."
        )
    token = utils.CreateAccessToken(data={"UUID":user.UUID, "IP":request.client.host})
    response = RedirectResponse("/")
    response.set_cookie(key="JWT", value=token, httponly=True, samesite="lax")
    return response

@router.get("/logout")
async def get_logout_page(request:Request):
    response = RedirectResponse("/")
    response.delete_cookie("JWT")
    return response

@router.post("/register")
async def post_register_page(request:Request,
                            screenName: str = Form(),
                            email: str = Form(),
                            password: str = Form(),
                            fname: str = Form(None),
                            mname: str = Form(None),
                            lname: str = Form(None),
                            phone: str = Form(None),
                            user:User = Depends(utils.GetCookieUserAllowGuest)):
    if user:
        return RedirectResponse("/")
    newUser = UserRegister(
        screenName=screenName,
        email=email,
        password=password,
        phone=phone,
        fname=fname,
        mname=mname,
        lname=lname
    )
    user = auth.register_user(newUser)
    token = utils.CreateAccessToken(data={"UUID":user.UUID, "IP":request.client.host})
    response = RedirectResponse("/")
    response.set_cookie(key="JWT",value=token, httponly=True, samesite="lax")
    return response #settings.TEMPLATES.TemplateResponse("register.html", {"request":request, "user":user})

@router.get("/register")
async def get_register_page(request:Request, user:User = Depends(utils.GetCookieUserAllowGuest)):
    if user:
        return RedirectResponse("/")
    return settings.TEMPLATES.TemplateResponse("register.html", {"request":request, "user":user})