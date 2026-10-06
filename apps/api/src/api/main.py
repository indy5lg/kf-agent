from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from indy_db.engine import engine  # noqa: E402
from indy_db.models import Base  # noqa: E402

from api.routers.auth import router as auth_router  # noqa: E402
from api.routers.fake_storage import router as fake_storage_router  # noqa: E402
from api.routers.runs import router as runs_router  # noqa: E402
from api.routers.uploads import router as uploads_router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(uploads_router)
app.include_router(runs_router)
app.include_router(fake_storage_router)
