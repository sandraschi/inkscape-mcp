"""Logging routes — compliant with WEBAPP_LOGS_PAGE.md v1.0."""

from fastapi import APIRouter, Query, Request
from fastapi.responses import PlainTextResponse, Response

router = APIRouter(tags=["Logging"])


@router.get("/api/logs")
async def get_logs(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    level: str | None = Query(None),
    kind: str | None = Query(None),
    search: str | None = Query(None),
    sort: str = Query("desc", regex="^(asc|desc)$"),
    after_id: str | None = Query(None),
):
    log = getattr(request.app.state, "activity_log", None)
    if log is None:
        return {"entries": [], "total": 0, "limit": limit, "offset": offset, "max_entries": 0, "sort": sort}
    return log.query(limit=limit, offset=offset, level=level, kind=kind, search=search, sort=sort, after_id=after_id)


@router.get("/api/logs/stats")
async def logs_stats(request: Request):
    log = getattr(request.app.state, "activity_log", None)
    if log is None:
        return {"total": 0, "max_entries": 0, "levels": {}, "kinds": {}}
    return log.stats()


@router.get("/api/logs/export")
async def logs_export(
    request: Request,
    format: str = Query("json", regex="^(json|csv)$"),
    level: str | None = Query(None),
    kind: str | None = Query(None),
    search: str | None = Query(None),
):
    log = getattr(request.app.state, "activity_log", None)
    if log is None:
        return PlainTextResponse("[]", media_type="application/json")
    content = log.export(format=format, level=level, kind=kind, search=search)
    media = "text/csv" if format == "csv" else "application/json"
    filename = f"logs.{format}"
    return Response(content=content, media_type=media, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.delete("/api/logs")
async def clear_logs(request: Request):
    log = getattr(request.app.state, "activity_log", None)
    if log:
        log.clear()
    return {"success": True, "message": "Logs cleared."}
