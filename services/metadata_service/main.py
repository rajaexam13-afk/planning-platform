from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import Base, engine
from .routers import attributes, dimensions, members
from .routers import upload
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Metadata Service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dimensions.router)
app.include_router(attributes.router)
app.include_router(members.router)
app.include_router(upload.router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
