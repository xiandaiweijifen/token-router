from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import AllocRequest, AllocResponse, ErrorResponse, FreeRequest, FreeResponse
from app.token_allocator import (
    DuplicateRequestError,
    NotFoundError,
    OverloadedError,
    TokenAllocator,
)

router = APIRouter()


def get_allocator() -> TokenAllocator:
    """Dependency placeholder overridden in app.main."""
    raise RuntimeError("TokenAllocator dependency not wired")


@router.post(
    "/alloc",
    response_model=AllocResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_429_TOO_MANY_REQUESTS: {"model": ErrorResponse},
    },
)
async def alloc_tokens(
    payload: AllocRequest,
    allocator: TokenAllocator = Depends(get_allocator),
) -> AllocResponse:
    try:
        result = allocator.allocate(payload.request_id, payload.token_count)
        return AllocResponse(
            node_id=result.node_id,
            remaining_quota=result.remaining_quota,
        )
    except OverloadedError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="overloaded",
        ) from exc
    except DuplicateRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="duplicate_request",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/free",
    response_model=FreeResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
async def free_tokens(
    payload: FreeRequest,
    allocator: TokenAllocator = Depends(get_allocator),
) -> FreeResponse:
    try:
        record = allocator.free(payload.request_id)
        return FreeResponse(node_id=record.node_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="not_found",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
