from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GraphEvent(BaseModel):
    id: int | None = None
    event_type: str
    aggregate_type: str
    aggregate_id: str
    source: str | None = None
    idempotency_key: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class ProjectRequest(BaseModel):
    events: list[GraphEvent] = Field(default_factory=list)


class SyncRequest(BaseModel):
    batch_size: int | None = Field(default=None, ge=1, le=1000)


class ReplayRequest(BaseModel):
    replay_from_id: int | None = Field(default=None, ge=1)
    batch_size: int | None = Field(default=None, ge=1, le=1000)
    events: list[GraphEvent] = Field(default_factory=list)


class FacultyAuthorInput(BaseModel):
    person_source_key: str
    display_name: str = ""
    position: int = 0


class FacultyPersonInput(BaseModel):
    source_key: str
    full_name: str = ""
    primary_unit: str = ""
    publications_total: int = 0


class FacultyPublicationInput(BaseModel):
    source_publication_id: str
    title: str = ""
    year: int | None = None
    authors: list[FacultyAuthorInput] = Field(default_factory=list)


class FacultyImportRequest(BaseModel):
    persons: list[FacultyPersonInput] = Field(default_factory=list)
    publications: list[FacultyPublicationInput] = Field(default_factory=list)
