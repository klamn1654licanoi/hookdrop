"""FastAPI application that receives and stores incoming webhook requests."""

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse

from hookdrop.storage import RequestStore

app = FastAPI(title="hookdrop", version="0.1.0")
store = RequestStore()


@app.api_route("/hook/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def receive_webhook(path: str, request: Request) -> JSONResponse:
    """Catch-all endpoint that records every incoming webhook."""
    body = await request.body()
    req = store.save(
        method=request.method,
        path=f"/{path}",
        headers=dict(request.headers),
        query_params=dict(request.query_params),
        body=body,
    )
    return JSONResponse(status_code=200, content={"id": req.id, "status": "received"})


@app.get("/inspect")
async def list_requests() -> JSONResponse:
    """Return all captured requests, newest first."""
    return JSONResponse(content=[r.to_dict() for r in store.all()])


@app.get("/inspect/{request_id}")
async def get_request(request_id: str) -> JSONResponse:
    """Return a single captured request by ID."""
    req = store.get(request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return JSONResponse(content=req.to_dict())


@app.delete("/inspect/{request_id}")
async def delete_request(request_id: str) -> JSONResponse:
    """Delete a single captured request by ID."""
    deleted = store.delete(request_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Request not found")
    return JSONResponse(content={"deleted": request_id})


@app.delete("/inspect")
async def clear_requests() -> JSONResponse:
    """Clear all captured requests."""
    count = store.clear()
    return JSONResponse(content={"cleared": count})
