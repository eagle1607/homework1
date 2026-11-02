import jwt
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

PUBLIC_PATHS = {"/api/health", "/register", "/login", "/docs", "/openapi.json", "/redoc"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        token = request.cookies.get("access_token")
        if token is None:
            return JSONResponse({"detail": "Not authenticated"}, status_code=401)

        try:
            payload = jwt.decode(token, request.app.state.settings.jwt_secret, algorithms=["HS256"])
        except jwt.PyJWTError:
            return JSONResponse({"detail": "Invalid or expired token"}, status_code=401)

        request.state.user_id = int(payload["sub"])
        return await call_next(request)
