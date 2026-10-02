"""
POST /api/permissions (Stage 7): explain app permissions in plain language.

Request:  {"permissions": "<pasted list of permission names>"}
Response: {"permissions": [{"name", "platform", "title", "explanation", "risk_level"}]}

This uses a fixed lookup table, not Claude, so it costs nothing and isn't rate limited.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.permissions.explain import explain_permissions

router = APIRouter()


class PermissionsRequest(BaseModel):
    permissions: str


@router.post("/api/permissions")
def permissions(request: PermissionsRequest) -> dict:
    return {"permissions": explain_permissions(request.permissions)}
