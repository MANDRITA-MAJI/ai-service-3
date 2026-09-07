from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services import embedding_service, speech_service
from app.routes import pipeline, triage


@asynccontextmanager
async def lifespan(app: FastAPI):
    # load heavy models ONCE at startup — never inside a route function,
    # or every request reloads the model from scratch
    embedding_service.load_model()
    speech_service.load_model()
    yield


app = FastAPI(title="Societal Innovation Portal - AI Service", lifespan=lifespan)

# if your Next.js backend calls this service server-side (API routes),
# CORS may not even be needed — this is only required if the browser
# calls this API directly. Tighten allow_origins before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline.router)
app.include_router(triage.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
