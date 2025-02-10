import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from server.routes import router
from server.database import engine
from server.models import Base

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.include_router(router)

app.mount("/", StaticFiles(directory="dist", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)