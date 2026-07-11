from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    app_name: str = "IntelGuard API"
    environment: str = "development"
    cors_origins: str = "http://localhost:8000,http://localhost:5173,http://localhost:3000"
    jwt_secret: str = Field(default="change-this-before-production")
    jwt_issuer: str = "intelguard"
    auth_disabled: bool = True

    neo4j_uri: str | None = None
    neo4j_username: str | None = None
    neo4j_password: str | None = None

    gemini_api_key: str | None = None

    fabric_gateway_url: str | None = None
    fabric_channel: str = "intelguard-channel"
    fabric_chaincode: str = "auditcc"
    fabric_function: str = "CreateAuditReceipt"
    fabric_msp_id: str = "SCRBMSP"

    data_dir: str = "./data"

    @property
    def cors_list(self) -> List[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

settings = Settings()
