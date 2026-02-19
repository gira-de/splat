import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from splat.config.model import PMConfig
from splat.model import (
    AuditReport,
    Dependency,
    DependencyType,
    Lockfile,
    Project,
    RuntimeContext,
    Severity,
    VulnerabilityDetail,
)
from tests.mocks import MockCommandRunner, MockEnvManager, MockFileSystem, MockLogger


class BasePackageManagerTest(unittest.TestCase):
    """Base test class for package manager tests to share setup and utility methods."""

    def setUp(self) -> None:
        self.mock_logger = MockLogger()
        self.mock_command_runner = MockCommandRunner(self.mock_logger)
        self.mock_fs = MockFileSystem()
        self.mock_env_manager = MockEnvManager()
        self.mock_ctx = RuntimeContext(
            logger=self.mock_logger,
            fs=self.mock_fs,
            command_runner=self.mock_command_runner,
            env_manager=self.mock_env_manager,
        )
        self.project = Project(name_with_namespace="project1")
        self.project.path = Path("/mock/path")
        self.mock_config = MagicMock(spec=PMConfig)

        self.lockfile = Lockfile(
            path=Path("/path/to/project/example.lock"),
            relative_path=Path("/example.lock"),
        )

        self.direct_dep = Dependency(
            name="package1", version="1.0.0", type=DependencyType.DIRECT, is_dev=False, parent_deps=[]
        )

        self.audit_report = AuditReport(
            dep=self.direct_dep,
            severity=Severity.UNKNOWN,
            fixed_version="2.0.0",
            vuln_details=[
                VulnerabilityDetail(
                    id="VULN-2",
                    description="Test vulnerability",
                    recommendation=[""],
                    aliases=["CVE-1234"],
                )
            ],
            lockfile=self.lockfile,
        )

        self.mock_pip_audit_out_no_vulns = json.dumps(
            {"fixes": [], "dependencies": [{"name": "package1", "version": "1.0.0", "vulns": []}]}
        )
        self.mock_pip_audit_out_with_vulns = json.dumps(
            {
                "fixes": [{"name": "package1", "new_version": "2.0.0"}],
                "dependencies": [
                    {
                        "name": "package1",
                        "version": "1.0.0",
                        "vulns": [
                            {
                                "id": "VULN-2",
                                "description": "Test vulnerability",
                                "fix_versions": [""],
                                "aliases": ["CVE-1234"],
                            }
                        ],
                    }
                ],
            }
        )
