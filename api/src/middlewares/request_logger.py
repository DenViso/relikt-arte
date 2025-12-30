from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        return response
