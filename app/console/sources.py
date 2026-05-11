from fastapi import APIRouter, HTTPException
from app.storage.blob import list_versions, read_blob_text, write_blob_text
from app.storage.cosmos import get_campaign, merge_campaign_fields

router = APIRouter(prefix="/api/console")


async def _artifact(artifact_id: str) -> dict:
    campaign = await get_campaign()
    for artifact in campaign.get("artifacts", []):
        if artifact.get("artifact_id") == artifact_id:
            return artifact
    raise HTTPException(status_code=404, detail="Artifact not found")


@router.get("/sources")
async def list_sources():
    return {"items": (await get_campaign()).get("artifacts", [])}


@router.get("/sources/{artifact_id}")
async def read_source(artifact_id: str):
    artifact = await _artifact(artifact_id)
    return {"artifact": artifact, "content": await read_blob_text(artifact["blob_path"])}


@router.patch("/sources/{artifact_id}")
async def patch_source(artifact_id: str, payload: dict):
    artifact = await _artifact(artifact_id)
    result = await write_blob_text(artifact["blob_path"], payload.get("content", ""))
    campaign = await get_campaign()
    for a in campaign.get("artifacts", []):
        if a.get("artifact_id") == artifact_id:
            a["current_version_id"] = result.get("version_id")
    await merge_campaign_fields({"artifacts": campaign.get("artifacts", [])})
    return {"ok": True, "artifact_id": artifact_id, "version_id": result.get("version_id")}


@router.get("/sources/{artifact_id}/history")
async def source_history(artifact_id: str):
    artifact = await _artifact(artifact_id)
    return {"items": await list_versions(artifact["blob_path"])}


@router.post("/sources/{artifact_id}/test")
async def test_source(artifact_id: str, payload: dict):
    artifact = await _artifact(artifact_id)
    content = await read_blob_text(artifact["blob_path"])
    return {"ok": True, "artifact_id": artifact_id, "channel": artifact.get("channel"), "preview": content[:2000], "recipient": payload.get("recipient", {})}
