from fastapi import FastAPI

from app import routes
from app.config import load_config
from app.token_allocator import TokenAllocator

app = FastAPI()
config = load_config()
allocator = TokenAllocator(node_count=config.node_count, node_quota=config.node_quota)


def allocator_dependency() -> TokenAllocator:
    return allocator


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(routes.router)
app.dependency_overrides[routes.get_allocator] = allocator_dependency
