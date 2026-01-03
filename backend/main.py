from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from fastapi.middleware.cors import CORSMiddleware
from api import auth, submission, groups, testcases, leaderboard, challenges, webhooks
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="DOJO Backend")


# Call this function right at the top, before anything else.


# --- CORRECTED CORS CONFIGURATION ---
origins = [
    "http://localhost",
    "http://localhost:3000", # Default for Create React App
    "http://localhost:3001", # Common alternative
    "http://localhost:5173", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods
    allow_headers=["*"], # Allow all headers
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    print("Unhandled exception:", traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# Register all routers
app.include_router(auth.router)
app.include_router(submission.router)
app.include_router(groups.router)
app.include_router(testcases.router)
app.include_router(leaderboard.router)
app.include_router(challenges.router)
app.include_router(webhooks.router)


@app.get("/")
def root():
    return {"message": "Welcome to the DOJO backend!"}