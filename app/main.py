import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.config.settings import settings
from app.database.connection import check_database_connection, init_db
from app.auth.routes import router as auth_router
from app.conversations.routes import router as conversations_router
from app.chat.routes import router as chat_router
from app.files.routes import router as files_router
from app.services.routes import router as settings_router
from app.auth.dependencies import get_current_user, get_current_user_optional

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("aura_ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for application startup and shutdown."""
    logger.info(f"Starting {settings.APP_NAME} in {settings.ENVIRONMENT} mode...")
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Database health check & migration/initialization
    db_connected = check_database_connection()
    if db_connected:
        try:
            init_db()
            logger.info("Database schemas initialized.")
        except Exception as e:
            logger.warning(f"Could not automatically initialize tables: {e}")
    else:
        logger.warning("Database connection failed on startup. Verify MySQL service.")

    yield
    
    logger.info(f"Shutting down {settings.APP_NAME}...")


# Initialize FastAPI instance
app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade AI Assistant Web Application powered by FastAPI & Python",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & Templates configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Include API Routers
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(chat_router)
app.include_router(files_router)
app.include_router(settings_router)


# Main Web Routes (Frontend Jinja2 rendering)
@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request, user=Depends(get_current_user_optional)):
    """Landing page or direct workspace redirect based on authentication state."""
    if user:
        return RedirectResponse(url="/chat", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user=Depends(get_current_user_optional)):
    """Render login page template."""
    if user:
        return RedirectResponse(url="/chat", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"app_name": settings.APP_NAME}
    )


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user=Depends(get_current_user_optional)):
    """Render registration page template."""
    if user:
        return RedirectResponse(url="/chat", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"app_name": settings.APP_NAME}
    )


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, user=Depends(get_current_user_optional)):
    """Main Chat Workspace - Protected Route."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={
            "app_name": settings.APP_NAME,
            "user": user
        }
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, user=Depends(get_current_user_optional)):
    """User Settings & Preferences - Protected Route."""
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "app_name": settings.APP_NAME,
            "user": user
        }
    )


@app.get("/logout")
async def logout_page():
    """Clear authentication cookie and redirect to login page."""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response


# System Health Check API
@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify server and database connectivity."""
    db_status = check_database_connection()
    return JSONResponse(
        content={
            "status": "healthy" if db_status else "degraded",
            "app": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
            "database_connected": db_status,
            "ai_provider": settings.AI_PROVIDER,
            "ai_model": settings.AI_MODEL
        }
    )
