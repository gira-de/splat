import unittest
from typing import List

from splat.interface.APIClient import JSON
from splat.source_control.gitlab.ci_artifact_fetch import download_artifact, fetch_downstream_pipeline_id, fetch_job_id
from tests.mocks import MockFileSystem, MockLogger
from tests.mocks.mock_gitlab_api import MockGitLabAPI


class TestCIArtifactFetch(unittest.TestCase):
    def setUp(self) -> None:
        self.base_url = "http://gitlab.example.com"
        self.project_endpoint = f"{self.base_url}/projects/1"
        self.pipeline_id = "pipeline_1"
        self.fake_logger = MockLogger()

    def test_fetch_existing_downstream_pipeline_id_successfully(self) -> None:
        bridges_response: JSON = [
            {"downstream_pipeline": {"id": "1234"}},
            {"downstream_pipeline": None},
        ]
        fake_api = MockGitLabAPI(api_url=self.base_url, get_json_response=bridges_response)
        result = fetch_downstream_pipeline_id(
            fake_api, self.project_endpoint, self.pipeline_id, logger=self.fake_logger
        )
        self.assertEqual(result, "1234")
        self.assertTrue(any("Fetching downstream pipeline ID" in msg for msg in self.fake_logger.logged_messages))

    def test_fetch_downstream_pipeline_id_failure_logs_and_raises_error(self) -> None:
        bridges_response: JSON = [{"downstream_pipeline": None}]
        fake_api = MockGitLabAPI(api_url=self.base_url, get_json_response=bridges_response)
        with self.assertRaises(RuntimeError) as context:
            fetch_downstream_pipeline_id(fake_api, self.project_endpoint, self.pipeline_id, logger=self.fake_logger)
        self.assertIn("Could not retrieve downstream pipeline ID", str(context.exception))

    def test_fetch_job_id_found_on_first_page(self) -> None:
        jobs_response: List[JSON] = [
            [{"id": "job1", "name": "thejob"}, {"id": "job2", "name": "another"}],  # page 1
            [],
        ]
        job_name = "thejob"
        fake_api = MockGitLabAPI(api_url=self.base_url, get_json_response=jobs_response)
        result = fetch_job_id(fake_api, self.project_endpoint, self.pipeline_id, job_name, logger=self.fake_logger)
        self.assertEqual(result, "job1")
        self.assertTrue(any(f"Fetching job ID for {job_name}" in msg for msg in self.fake_logger.logged_messages))

    def test_fetch_job_id_found_on_third_page(self) -> None:
        jobs_response: List[JSON] = [
            [{"id": "job1", "name": "other"}],  # page 1
            [{"id": "job2", "name": "something"}],  # page 2
            [{"id": "job3", "name": "thejob"}, {"id": "job2", "name": "another"}],  # page 3
            [],
        ]
        job_name = "thejob"
        fake_api = MockGitLabAPI(api_url=self.base_url, get_json_response=jobs_response)
        result = fetch_job_id(fake_api, self.project_endpoint, self.pipeline_id, job_name, logger=self.fake_logger)
        self.assertEqual(result, "job3")

    def test_fetch_job_id_not_found_in_one_page(self) -> None:
        jobs_responses: List[JSON] = [
            [{"id": "job1", "name": "thejob"}, {"id": "job2", "name": "another"}],  # page1
            [],
        ]
        job_name = "notfound"
        fake_api = MockGitLabAPI(api_url=self.base_url, get_json_response=jobs_responses)
        with self.assertRaises(RuntimeError) as context:
            fetch_job_id(fake_api, self.project_endpoint, self.pipeline_id, job_name, logger=self.fake_logger)
        self.assertIn(f"Could not retrieve job ID for {job_name}", str(context.exception))

    def test_fetch_job_id_not_found_in_three_pages(self) -> None:
        jobs_responses: List[JSON] = [
            [{"id": "job1", "name": "other"}],  # page 1
            [{"id": "job2", "name": "something"}],  # page 2
            [{"id": "job3", "name": "thejob"}, {"id": "job2", "name": "another"}],  # page 3
            [],
        ]
        job_name = "notfound"
        fake_api = MockGitLabAPI(api_url=self.base_url, get_json_response=jobs_responses)
        with self.assertRaises(RuntimeError) as context:
            fetch_job_id(fake_api, self.project_endpoint, self.pipeline_id, job_name, logger=self.fake_logger)
        self.assertIn(f"Could not retrieve job ID for {job_name}", str(context.exception))

    def test_download_artifact_success(self) -> None:
        artifact_bytes = b"artifact content"
        fake_api = MockGitLabAPI(api_url=self.base_url, get_bytes_response=artifact_bytes)
        fake_fs = MockFileSystem()

        download_artifact(fake_api, self.project_endpoint, "job123", fake_fs, logger=self.fake_logger)
        artifact_file = "projects_summary.json"
        self.assertTrue(fake_fs.exists(artifact_file))
        self.assertEqual(fake_fs.read(artifact_file), artifact_bytes.decode())
        self.assertTrue(any("Artifact downloaded" in msg for msg in self.fake_logger.logged_messages))


if __name__ == "__main__":
    unittest.main()
