from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_database
from routes import auth_routes, expense_routes, category_routes, budget_routes

app = FastAPI(title="Expense Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()
    print("Database initialized successfully")

# Include routers
app.include_router(auth_routes.router, prefix="/api")
app.include_router(expense_routes.router, prefix="/api")
app.include_router(category_routes.router, prefix="/api")
app.include_router(budget_routes.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)