from __future__ import annotations

from azure.storage.blob.aio import BlobServiceClient
from azure.identity.aio import DefaultAzureCredential
from app.config import get_settings


_credential: DefaultAzureCredential | None = None
_client: BlobServiceClient | None = None


async def _blob_service() -> BlobServiceClient:
    global _credential, _client
    if _client is None:
        _credential = DefaultAzureCredential()
        _client = BlobServiceClient(account_url=get_settings().storage_blob_endpoint, credential=_credential)
    return _client


async def read_blob_text(path: str, container: str | None = None) -> str:
    svc = await _blob_service()
    blob = svc.get_blob_client(container=container or get_settings().artifacts_container, blob=path)
    stream = await blob.download_blob()
    return (await stream.readall()).decode("utf-8")


async def write_blob_text(path: str, content: str, container: str | None = None) -> dict:
    svc = await _blob_service()
    blob = svc.get_blob_client(container=container or get_settings().artifacts_container, blob=path)
    result = await blob.upload_blob(content.encode("utf-8"), overwrite=True)
    props = await blob.get_blob_properties()
    return {"etag": result.get("etag"), "version_id": props.get("version_id"), "path": path}


async def list_versions(path: str, container: str | None = None) -> list[dict]:
    svc = await _blob_service()
    items = []
    async for blob in svc.get_container_client(container or get_settings().artifacts_container).list_blobs(name_starts_with=path, include=["versions"]):
        if blob.name == path:
            items.append({"name": blob.name, "version_id": getattr(blob, "version_id", None), "last_modified": str(blob.last_modified)})
    return items
