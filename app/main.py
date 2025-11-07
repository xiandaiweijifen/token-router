from fastapi import FastAPI

from app import routes
from app.token_allocator import TokenAllocator

app = FastAPI()
allocator = TokenAllocator(node_count=3, node_quota=300)


def allocator_dependency() -> TokenAllocator:
    return allocator


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(routes.router)
app.dependency_overrides[routes.get_allocator] = allocator_dependency
