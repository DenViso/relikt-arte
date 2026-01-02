from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import os
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from .middlewares.request_logger import RequestAuditMiddleware
from .core.config import settings
from .core.caching import init_caching
from .user.router import router as user_router
from .product.router import router as product_router
from .order.router import router as order_router
from .nova_post.router import router as nova_post_router
from .letter.router import router as letter_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_caching()
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version=str(settings.app_version),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. ProxyHeaders ПЕРШИМ - для правильної роботи з Railway
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# 2. CORS ДРУГИМ - ДО RequestAuditMiddleware
# Важливо: дозволяємо обидва протоколи для Railway
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://relikt.vercel.app",
    "https://relikt-arte.vercel.app",
    # Додаємо HTTP версію Railway для внутрішніх запитів
    "http://reliktarte-production.up.railway.app",
    "https://reliktarte-production.up.railway.app",
]

print(f"🔧 CORS Configuration:")
print(f"   Allowed Origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 3. Request Audit ТРЕТІМ
app.add_middleware(RequestAuditMiddleware)


# Include routers
routers: list[APIRouter] = [
    user_router,
    product_router,
    order_router,
    nova_post_router,
    letter_router,
]

for router in routers:
    app.include_router(router, prefix=f"/api/v{settings.app_version}")


# Mount static directory
static_path = Path(__file__).parent / "static"
if static_path.exists():
    try:
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        print(f"✅ Static files mounted at /static from {static_path}")
    except Exception as e:
        print(f"⚠️ Warning: Could not mount static directory: {e}")
else:
    print(f"⚠️ Static directory not found at {static_path}")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")