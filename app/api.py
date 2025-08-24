from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.tasks import scrape_url
from app.redis_client import get_task_result
from app.domain_limiter import domain_limiter
import uvicorn

app = FastAPI(title="Web Scraper API", description="A FastAPI application for web scraping")

class TaskRequest(BaseModel):
    url: str

class TaskResponse(BaseModel):
    task_id: str

class NewsItem(BaseModel):
    entity_title: str
    entry_meta_date: str
    url: str

class TaskStatusResponse(BaseModel):
    status: str
    data: Optional[List[NewsItem]] = None
    error: Optional[str] = None

@app.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest):
    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    task = scrape_url.delay(request.url)
    return TaskResponse(task_id=task.id)

@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    result = get_task_result(task_id)

    if not result:
        return TaskStatusResponse(status="PENDING", data=None, error=None)

    elif result.get("status") == "SUCCESS":
        return TaskStatusResponse(status="SUCCESS", data=result.get("data"), error=None)

    return TaskStatusResponse(
        status=result.get("status", "PENDING"),
        data=result.get("data", None),
        error=result.get("error", None)
    )

@app.get("/stats/domain-limiter")
async def get_domain_limiter_stats():
    """Получить статистику по ограничениям доменов"""
    return {
        "domain_stats": domain_limiter.get_stats(),
        "config": {
            "max_concurrent_per_domain": domain_limiter.max_concurrent_per_domain
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


    
