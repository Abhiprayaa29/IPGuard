from datetime import datetime
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, object]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str = Field(examples=["ipguard-api"])
    version: str = Field(examples=["1.0.0"])


class DatabaseHealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    database: str = Field(examples=["postgresql"])
    latency_ms: float = Field(examples=[1.24])


class SystemInfoResponse(BaseModel):
    name: str = Field(examples=["IPGuard"])
    version: str = Field(examples=["1.0.0"])
    environment: str = Field(examples=["development"])
    api_version: str = Field(examples=["v1"])
    database_engine: str = Field(examples=["postgresql"])


class AuditEventSummary(BaseModel):
    event_id: str
    chain_id: str
    sequence: int
    occurred_at: datetime
    actor_type: str
    event_type: str
    resource_type: str
    resource_id: str | None = None
    result: str
    event_hash: str


class SystemOverviewResponse(BaseModel):
    account_id: str
    authenticated: bool
    environment: str
    api_status: str
    database_status: str
    database_latency_ms: float | None = None
    registered_slots: int
    max_slots: int = 1
    current_device_id: str | None = None
    current_device_name: str | None = None
    current_device_status: str
    notes_count: int | None = None
    assets_count: int | None = None
    verified_assets_count: int | None = None
    warnings: list[str] = Field(default_factory=list)
    recent_events: list[AuditEventSummary] = Field(default_factory=list)
