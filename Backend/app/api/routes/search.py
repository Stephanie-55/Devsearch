from fastapi import APIRouter, Query, Depends
from fastapi.responses import StreamingResponse
from app.services.search import SearchService
from app.services.auth import get_current_user
import json
import asyncio

router = APIRouter(prefix="/search", tags=["Search"])

# ---------------------------------------------------
# Normal search (existing endpoint)
# ---------------------------------------------------
@router.get("/")
def search(
    q: str = Query(...),
    k: int = 5,
    keywords: str | None = Query(default=None, description="Comma separated keywords"),
    current_user: dict = Depends(get_current_user)
):
    service = SearchService(user_id=current_user["id"])
    kw_list = [x.strip() for x in keywords.split(",")] if keywords else None
    return service.search(q, k, keywords=kw_list)


# ---------------------------------------------------
# Streaming search endpoint
# ---------------------------------------------------
@router.get("/stream")
async def search_stream(
    q: str = Query(...),
    k: int = 5,
    keywords: str | None = Query(default=None),
    current_user: dict = Depends(get_current_user)
):
    service = SearchService(user_id=current_user["id"])
    kw_list = [x.strip() for x in keywords.split(",")] if keywords else None

    async def event_generator():
        for result in service.stream_search(q, k, keywords=kw_list):
            yield f"data: {json.dumps(result)}\n\n"
            await asyncio.sleep(0.05)
        yield "event: end\ndata: done\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )