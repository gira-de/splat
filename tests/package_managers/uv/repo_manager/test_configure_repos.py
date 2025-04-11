from splat.package_managers.uv.repo_manager import UvRepoManager
from tests.package_managers.common.test_base_repo_manager import TestBasePipRepoManager


class TestConfigureRepositories(TestBasePipRepoManager):
    def setUp(self) -> None:
        super().setUp()
        self.repo_manager = UvRepoManager(self.env_manager, self.mock_fs, self.mock_logger)
