from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.app import router  

app = FastAPI(title="Expense Tracker API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api") 
