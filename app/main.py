from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, HTMLResponse
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.routes import store, auth, checkout, admin
from app.config import settings
from app.templates_env import templates
import app.models  # ensure all models are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _create_default_admin()
    yield


def _create_default_admin():
    from app.database import SessionLocal
    from app.models.user import User
    from app.auth import hash_password
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.is_admin == True).first()
        if not existing:
            admin_user = User(
                name="Admin",
                phone="0000000000",
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(store.router)
app.include_router(checkout.router)
app.include_router(admin.router)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.exception_handler(404)
def not_found(request: Request, exc):
    return templates.TemplateResponse(
        "store/404.html", {"request": request}, status_code=404
    )
