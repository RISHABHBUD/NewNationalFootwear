from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from app.templates_env import templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
def login(
    request: Request,
    phone: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.phone == phone).first()
    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Invalid phone or password"},
            status_code=400,
        )
    token = create_access_token({"sub": str(user.id)})
    response = RedirectResponse("/account" if not user.is_admin else "/admin", status_code=302)
    response.set_cookie("access_token", token, httponly=True, max_age=60 * 60 * 24 * 7)
    return response


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register")
def register(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(None),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.phone == phone).first()
    if existing:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Phone number already registered"},
            status_code=400,
        )
    user = User(
        name=name, phone=phone, email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    response = RedirectResponse("/", status_code=302)
    response.set_cookie("access_token", token, httponly=True, max_age=60 * 60 * 24 * 7)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("access_token")
    return response
