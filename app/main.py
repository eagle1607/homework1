from contextlib import asynccontextmanager #lưu cache session

from fastapi import FastAPI, Request

from app.config import Settings, get_settings
from app.database import Base, make_session_factory

from .middleware import AuthMiddleware
from .routers import auth, tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(app.state.engine)
    yield
    app.state.engine.dispose()

def create_app(settings: Settings):
    app = FastAPI(lifespan=lifespan)
    engine, session_factory = make_session_factory(settings.database_uri)
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.settings = settings
    app.add_middleware(AuthMiddleware)

    @app.get("/api/health")
    async def health(request: Request):
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(tickets.router)
    return app


app = create_app(get_settings())
