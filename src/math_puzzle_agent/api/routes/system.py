from fastapi import APIRouter, Request, Response, status

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request, response: Response) -> dict[str, str]:
    if await request.app.state.database.ping():
        return {"status": "ready", "database": "available"}
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "not_ready", "database": "unavailable"}
