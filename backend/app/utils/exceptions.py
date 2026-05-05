"""
utils/exceptions.py — Custom HTTP exception helpers.
"""
from fastapi import HTTPException, status


def not_found(resource: str = "Resource"):
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} not found."
    )


def forbidden():
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this resource."
    )


def bad_request(msg: str = "Bad request."):
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=msg
    )
