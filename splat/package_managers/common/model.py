from typing import Optional

from pydantic import BaseModel, Field


class PipAuditEntryDepsVulns(BaseModel):
    id: str
    description: str
    fix_versions: list[str]
    aliases: list[str]


class PipAuditEntryDeps(BaseModel):
    name: str
    version: Optional[str] = Field(default=None)
    vulns: list[PipAuditEntryDepsVulns] = Field(default_factory=list)
    skip_reason: Optional[str] = Field(default=None)


class PipAuditEntryFixes(BaseModel, extra="allow"):
    name: str
    new_version: Optional[str] = Field(default=None)
    skip_reason: Optional[str] = Field(default=None)


class PipAuditEntry(BaseModel):
    dependencies: list[PipAuditEntryDeps]
    fixes: list[PipAuditEntryFixes]
