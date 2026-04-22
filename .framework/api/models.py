"""Pydantic schemas for the framework API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# ---------- Config ----------

class ModelRate(BaseModel):
    tier: int
    input_per_mtok: float
    output_per_mtok: float
    cache_write_multiplier: float = 1.25
    cache_read_multiplier: float = 0.10
    batch_multiplier: float = 0.50


class Budgets(BaseModel):
    daily_warn_usd: float
    daily_hard_usd: float
    monthly_warn_usd: float
    monthly_hard_usd: float


class RatesConfig(BaseModel):
    models: dict[str, ModelRate]
    budgets: Budgets


class Director(BaseModel):
    id: str
    name: str
    alias: list[str] = Field(default_factory=list)
    role: str
    color: str


class Agent(BaseModel):
    id: str
    name: str
    role: str
    default_provider: str
    default_model: str
    escalation_models: list[str] = Field(default_factory=list)
    color: str
    responsibilities: list[str] = Field(default_factory=list)


class ActorsConfig(BaseModel):
    director: Director
    agents: list[Agent]
    comms: dict[str, Any]


# ---------- Pizarra ----------

class PizarraMessage(BaseModel):
    ts: datetime
    actor: str
    tag: str
    para: Optional[str] = None
    body: Optional[str] = None
    task_id: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict)


# ---------- Queue ----------

class Task(BaseModel):
    id: str
    title: str
    owner: str
    model_tier: Optional[int] = None
    model: Optional[str] = None
    status: Literal["pending", "in_progress", "completed", "blocked", "deleted"]
    phase: Optional[str] = None
    blocked_by: list[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    raw: dict[str, Any] = Field(default_factory=dict)


# ---------- Cost ----------

class CostEntry(BaseModel):
    ts: datetime
    actor: str
    model: str
    tier: int
    input_tokens: int = 0
    output_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float = 0.0
    task_id: Optional[str] = None


# ---------- Health ----------

class ContainerStatus(BaseModel):
    name: str
    status: str
    healthy: bool


class InfraHealth(BaseModel):
    docker_containers: list[ContainerStatus]
    docker_required_up: int
    docker_required_total: int
    ollama_reachable: bool
    ollama_models_loaded: list[str]
    ollama_models_missing: list[str]
    gpu_temp_c: Optional[float] = None


# ---------- Activity ----------

class AgentActivity(BaseModel):
    agent: str
    messages_last_hour: int
    messages_last_24h: int
    last_activity_ts: Optional[datetime] = None
    seconds_since_last: Optional[int] = None
    heartbeat_status: Literal["ok", "warn", "stale", "unknown"] = "unknown"


# ---------- Overview (top-level) ----------

class FrameworkOverview(BaseModel):
    generated_at: datetime
    director: Director
    agents: list[Agent]
    activity: list[AgentActivity]
    queue_summary: dict[str, int]
    open_blocks: int
    open_audit_requests: int
    open_findings: int
    cost_today_usd: float
    cost_month_usd: float
    infra_ok: bool


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    checks: dict[str, bool]
    generated_at: datetime
