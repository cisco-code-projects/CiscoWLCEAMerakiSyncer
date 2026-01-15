from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Cisco WLC Settings
    wlc_host: str = Field(..., description="Hostname or IP of the Cisco 9800 WLC")
    wlc_username: str = Field(..., description="Username for SSH access to WLC")
    wlc_password: str = Field(..., description="Password for SSH access to WLC")
    wlc_port: int = Field(22, description="SSH port for WLC")
    
    # Meraki Settings
    meraki_api_key: str = Field(..., description="Meraki Dashboard API Key")
    meraki_org_id: str = Field(..., description="Meraki Organization ID")
    meraki_network_id: str = Field(..., description="Target Meraki Network ID to assign APs to")
    
    # App Settings
    sync_interval_seconds: int = Field(3600, description="Interval in seconds for synchronization (if running in loop)")
    dry_run: bool = Field(False, description="If True, will not perform write actions on Meraki")

    # Load from .env file if present
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

# Global settings instance
try:
    settings = Settings()
except Exception as e:
    # This will likely fail if env vars are missing during import, 
    # but we will handle it gracefully in main or let it crash early.
    # For now, we allow import time failure to signal missing config.
    pass
