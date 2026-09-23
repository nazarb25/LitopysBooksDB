from fastapi import APIRouter


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return router
