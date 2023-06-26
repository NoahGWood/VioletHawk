from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from config import settings
from models.user import User
from drivers.auth import utils

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
@router.post("/", response_class=HTMLResponse)
async def home_page(request: Request, user:User = Depends(utils.GetCookieUserAllowGuest)):
    return settings.TEMPLATES.TemplateResponse("index.html", {"request":request, "user":user})



@router.get("/search", response_class=HTMLResponse)
@router.post("/search", response_class=HTMLResponse)
async def search_page(request: Request,
                      category:str=None,
                      keywords:str=None,
                      user:User = Depends(utils.GetCookieUserAllowGuest)):
    cypher = """CREATE FULLTEXT INDEX postKeywords
    IF NOT EXISTS
    FOR (n:Post) ON EACH [n.Title, n.Content, n.Keywords]
    """
    cypher = f"""CALL
    db.index.fulltext.queryNodes("postKeywords", "{keywords}")
    YIELD node
    RETURN node
    """
    with settings.DB.session() as session:
        res = session.run(query=cypher)
        out = res.data()

    return settings.TEMPLATES.TemplateResponse("search/results.html", context={"request":request, "user":user, "category":category, "keywords":keywords, "results":out})
