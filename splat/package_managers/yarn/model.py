from typing import Optional

from pydantic import BaseModel


class YarnAuditEntryResolution(BaseModel, extra="allow"):
    path: str


class YarnAuditEntryDataAdvisoryFindings(BaseModel, extra="allow"):
    version: str


class YarnAuditEntryDataAdvisory(BaseModel, extra="allow"):
    findings: list[YarnAuditEntryDataAdvisoryFindings]
    module_name: str
    github_advisory_id: str
    overview: str
    recommendation: str
    vulnerable_versions: str
    cves: list[str]
    patched_versions: str
    severity: Optional[str]


class YarnAuditEntryData(BaseModel):
    resolution: YarnAuditEntryResolution
    advisory: YarnAuditEntryDataAdvisory


class YarnAuditEntry(BaseModel):
    type: str = "AuditAdvisory"
    data: YarnAuditEntryData
