from configs.config import config
from fastapi import FastAPI

from routers import rag
from routers import config


app = FastAPI()
app.include_router(rag.router)
app.include_router(config.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", port=8080, reload=True)