from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import os
from dotenv import load_dotenv

from app.routers import classification, correction, dialogue, rag, agent, dashboard, buffer
from app.database import engine, Base
from app.models import test_models

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI任务自动化测试平台",
    description="用于测试分类、纠错、对话、RAG、Agent等AI任务的综合平台",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(classification.router, prefix="/api/classification", tags=["分类任务"])
app.include_router(correction.router, prefix="/api/correction", tags=["纠错任务"])
app.include_router(dialogue.router, prefix="/api/dialogue", tags=["对话任务"])
app.include_router(rag.router, prefix="/api/rag", tags=["RAG任务"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent任务"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["仪表板"])
app.include_router(buffer.router, prefix="/api/buffer", tags=["缓冲带MVP"])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """主页"""
    return templates.TemplateResponse(request=request, name="index.html", context={})

@app.get("/buffer", response_class=HTMLResponse)
async def buffer_app(request: Request):
    """缓冲带MVP页面"""
    return templates.TemplateResponse(request=request, name="buffer.html", context={})

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "AI任务自动化测试平台运行正常"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 12000)),
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )