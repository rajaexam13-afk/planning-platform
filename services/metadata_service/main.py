from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import Base, engine
from .routers import attributes, dimensions, hierarchies, members, upload


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Metadata Service", lifespan=lifespan)

app.include_router(dimensions.router)
app.include_router(attributes.router)
app.include_router(members.router)
app.include_router(hierarchies.router)
app.include_router(upload.router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
