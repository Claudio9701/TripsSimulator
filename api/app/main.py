import uvicorn
from fastapi import FastAPI

from routes import trips

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
    "https://mediamap-5fxkcjxk7-claudio97.vercel.app",
    "https:/*.vercel.app",
    "https://handmap.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(trips.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
