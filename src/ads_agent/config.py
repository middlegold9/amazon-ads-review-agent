"""配置：MCP 端点、审批开关、目标 ACOS、品类、飞书 Webhook。"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="ADS_")

    mcp_base_url: str = ""
    mcp_token: str = ""
    approve_writes: bool = False  # 自动执行（调价/否定词）总开关，默认仅建议
    target_acos: float = 0.25
    category: str = "default"
    feishu_webhook: str = ""
    llm_provider: str = "stub"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = "stub-model"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
