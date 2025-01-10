from fastapi import FastAPI, Response
from pydantic import BaseModel
from starlette import status

from service.queue import InsertQueue

from db.utils.connector import AsyncDBConnector

from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://openrepowiki.xyz"
    "http://nextjs:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RepoInfo(BaseModel):
    owner: str
    repo: str

@app.get("/api/queue", status_code=status.HTTP_200_OK)
async def queue():
    connector = await AsyncDBConnector.init()
    insert_queue = InsertQueue.getInstance(connector)

    return {
        "current": insert_queue.processingItem,
        "queue": insert_queue.queue,
        "time": insert_queue.processingTime
    }


@app.post("/api/queue")
async def register(repo_info: RepoInfo, response: Response):
    connector = await AsyncDBConnector.init()
    insert_queue = InsertQueue.getInstance(connector)
    insert_resp = await insert_queue.add(repo_info)
    if insert_resp.success:
        response.status_code = status.HTTP_201_CREATED
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
    return insert_resp

@app.get("/")
async def root():
    return {"status": "ok"}