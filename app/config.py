import os
from functools import lru_cache
from pydantic import BaseModel
from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient


class Settings(BaseModel):
    campaign_id: str = os.getenv("CAMPAIGN_ID", "91b22035-842f-4290-8c31-9f0fa9f26de5")
    campaign_slug: str = os.getenv("CAMPAIGN_SLUG", "nabi")
    azure_subscription_id: str = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    azure_resource_group: str = os.getenv("AZURE_RESOURCE_GROUP", "rg-orbit-campaign-nabi")
    storage_account_name: str = os.getenv("STORAGE_ACCOUNT_NAME", "stcampnabi")
    storage_table_endpoint: str = os.getenv("STORAGE_TABLE_ENDPOINT", "https://stcampnabi.table.core.windows.net")
    storage_blob_endpoint: str = os.getenv("STORAGE_BLOB_ENDPOINT", "https://stcampnabi.blob.core.windows.net")
    artifacts_container: str = os.getenv("ARTIFACTS_CONTAINER", "artifacts")
    key_vault_name: str = os.getenv("KEY_VAULT_NAME", "kv-orbit-camp-nabi")
    cosmos_endpoint: str = os.getenv("COSMOS_ENDPOINT", "")
    cosmos_database: str = os.getenv("COSMOS_DATABASE", "OrbitLaunch")
    cosmos_campaigns_container: str = os.getenv("COSMOS_CAMPAIGNS_CONTAINER", "Campaigns")
    conversations_cosmos_endpoint: str = os.getenv("CONVERSATIONS_COSMOS_ENDPOINT", "")
    conversations_database: str = os.getenv("CONVERSATIONS_DATABASE", "ConversationsDB")
    conversations_agents_container: str = os.getenv("CONVERSATIONS_AGENTS_CONTAINER", "Agents")
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "https://nabi.campaigns.wakaorbit.com")
    orbit_brain_url: str = os.getenv("ORBIT_BRAIN_URL", "https://orbit-brain.wakaorbit.com")
    graph_tenant_id: str = os.getenv("GRAPH_TENANT_ID", "")
    shared_mailbox_address: str = os.getenv("SHARED_MAILBOX_ADDRESS", "campaign-nabi@wakacomvoice.onmicrosoft.com")
    agent_text_id: str = os.getenv("AGENT_TEXT_ID", "89ae8482-e36f-47b7-9145-f94511a8b520")
    region: str = os.getenv("AZURE_LOCATION", "francecentral")

    @property
    def key_vault_url(self) -> str:
        return f"https://{self.key_vault_name}.vault.azure.net"


@lru_cache
def get_settings() -> Settings:
    return Settings()


async def get_secret(name: str) -> str:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=get_settings().key_vault_url, credential=credential)
    try:
        secret = await client.get_secret(name)
        return secret.value or ""
    finally:
        await client.close()
        await credential.close()
