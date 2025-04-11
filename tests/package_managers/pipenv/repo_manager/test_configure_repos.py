from splat.package_managers.pipenv.repo_manager import PipenvRepoManager
from tests.package_managers.common.test_base_repo_manager import TestBasePipRepoManager


class TestConfigureRepositories(TestBasePipRepoManager):
    def setUp(self) -> None:
        super().setUp()
        self.manager = PipenvRepoManager(self.env_manager, self.mock_fs, self.mock_logger)
