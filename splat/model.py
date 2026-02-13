from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import NamedTuple

from splat.interface.logger import LoggerInterface
from splat.utils.command_runner.interface import CommandRunner
from splat.utils.env_manager.interface import EnvManager
from splat.utils.fs import FileSystemInterface


@dataclass(frozen=True)
class RuntimeContext:
    logger: LoggerInterface
    fs: FileSystemInterface
    command_runner: CommandRunner
    env_manager: EnvManager


@dataclass
class Project:
    name_with_namespace: str
    path: Path = field(default=Path("/uncloned"), init=False)


@dataclass
class RemoteProject(Project):
    id: int
    web_url: str
    clone_url: str
    default_branch: str


@dataclass
class LocalProject(Project):
    path: Path


@dataclass
class ProjectAuditFixResult:
    severity_score: Severity
    commit_messages: list[str]
    remaining_vulns: list[AuditReport]
    status_report: StatusReport


class Severity(Enum):
    UNKNOWN = 0
    LOW = 1
    MODERATE = 2
    HIGH = 3
    CRITICAL = 4


class StatusReport(Enum):
    CLEAN = "clean"
    ERROR = "error"
    MR_PENDING = "merge_pending"
    VULNS_LEFT = "vulnerabilities_left"
    MANUAL_CHANGES = "manual_changes"  # NON_SPLAT_COMMITS


@dataclass
class ProjectSummary:
    project_name: str
    time_stamp: str
    project_url: str
    status_report: str | None
    severity_score: str | None
    mr_url: str | None
    logfile_url: str | None


class Lockfile(NamedTuple):
    path: Path
    relative_path: Path


class VulnerabilityDetail(NamedTuple):
    id: str
    description: str
    recommendation: list[str]
    aliases: list[str]


class DependencyType(Enum):
    DIRECT = auto()
    TRANSITIVE = auto()
    BOTH = auto()


@dataclass
class Dependency:
    name: str
    type: DependencyType
    version: str | None = field(default=None)
    is_dev: bool = field(default=False)
    parent_deps: list[Dependency] | None = field(default_factory=list)


@dataclass
class AuditReport:
    dep: Dependency
    fixed_version: str | None
    vuln_details: list[VulnerabilityDetail]
    lockfile: Lockfile
    severity: Severity = field(default=Severity.UNKNOWN)
    fix_skip_reason: str | None = field(default=None)


class MergeRequest(NamedTuple):
    title: str
    url: str
    project_url: str
    project_name: str
    operation: str
