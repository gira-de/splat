import re
import unittest
from typing import cast
from unittest.mock import MagicMock, patch

from splat.config.model import FiltersConfig
from splat.model import RemoteProject
from splat.utils.project_processor.project_filter import filter_projects


class TestFilterProjects(unittest.TestCase):
    def setUp(self) -> None:
        self.projects = cast(
            list[RemoteProject],
            [
                MagicMock(spec=RemoteProject, name_with_namespace="group1/projectA"),
                MagicMock(spec=RemoteProject, name_with_namespace="group1/projectB"),
                MagicMock(spec=RemoteProject, name_with_namespace="group2/projectC"),
                MagicMock(spec=RemoteProject, name_with_namespace="group3/projectD"),
            ],
        )

    @patch("splat.utils.project_processor.project_filter.logger")
    def test_filter_projects_includes_correct_projects(self, _: MagicMock) -> None:
        filters = FiltersConfig(include=["group1/.*"], exclude=[])
        filtered_projects = filter_projects(self.projects, filters)
        self.assertEqual(
            [p.name_with_namespace for p in filtered_projects],
            ["group1/projectA", "group1/projectB"],
        )

    @patch("splat.utils.project_processor.project_filter.logger")
    def test_filter_projects_excludes_correct_projects(self, _: MagicMock) -> None:
        filters = FiltersConfig(include=[".*"], exclude=["group1/projectA"])
        filtered_projects = filter_projects(self.projects, filters)
        self.assertEqual(
            [p.name_with_namespace for p in filtered_projects],
            ["group1/projectB", "group2/projectC", "group3/projectD"],
        )

    @patch("splat.utils.project_processor.project_filter.logger")
    def test_filter_projects_includes_and_excludes_correct_projects(self, _: MagicMock) -> None:
        filters = FiltersConfig(include=["group1/.*"], exclude=["group1/projectA"])
        filtered_projects = filter_projects(self.projects, filters)
        self.assertEqual(
            [p.name_with_namespace for p in filtered_projects],
            ["group1/projectB"],
        )

    @patch("splat.utils.project_processor.project_filter.logger")
    def test_filter_projects_no_includes_or_excludes(self, _: MagicMock) -> None:
        filters = FiltersConfig(include=[], exclude=[])
        filtered_projects = filter_projects(self.projects, filters)
        self.assertEqual(
            [p.name_with_namespace for p in filtered_projects],
            [
                "group1/projectA",
                "group1/projectB",
                "group2/projectC",
                "group3/projectD",
            ],
        )

    def test_filter_projects_invalid_include_pattern_raises_error(self) -> None:
        filters = FiltersConfig(include=["group1/["], exclude=[])
        with self.assertRaises(re.error):
            filter_projects(self.projects, filters)

    def test_filter_projects_invalid_exclude_pattern_raises_error(self) -> None:
        filters = FiltersConfig(include=[".*"], exclude=["group1/["])
        with self.assertRaises(re.error):
            filter_projects(self.projects, filters)

    @patch("splat.utils.project_processor.project_filter.logger")
    def test_filter_projects_no_matching_include_patterns_return_empty_list(self, _: MagicMock) -> None:
        filters = FiltersConfig(include=["nonexistent/.*"], exclude=[])
        filtered_projects = filter_projects(self.projects, filters)
        self.assertEqual(filtered_projects, [])

    @patch("splat.utils.project_processor.project_filter.logger")
    def test_filter_projects_with_overlapping_include_and_exclude_patterns(self, _: MagicMock) -> None:
        filters = FiltersConfig(include=["group1/.*"], exclude=["group1/projectA"])
        filtered_projects = filter_projects(self.projects, filters)
        self.assertEqual(
            [p.name_with_namespace for p in filtered_projects],
            ["group1/projectB"],
        )

    @patch("splat.utils.project_processor.project_filter.logger")
    def test_filter_projects_case_sensitivity(self, _: MagicMock) -> None:
        filters = FiltersConfig(include=["group1/PROJECTA"], exclude=[])
        filtered_projects = filter_projects(self.projects, filters)
        self.assertEqual(filtered_projects, [])

    @patch("splat.utils.project_processor.project_filter.logger")
    def test_filter_projects_logs_correct_information(self, mock_logger: MagicMock) -> None:
        filters = FiltersConfig(include=["group1/.*"], exclude=["group1/projectA"])
        filter_projects(self.projects, filters)
        mock_logger.debug.assert_any_call(
            "All accessible projects: \n" "group1/projectA, group1/projectB, group2/projectC, group3/projectD"
        )
        mock_logger.debug.assert_any_call("Include patterns: ['group1/.*']")
        mock_logger.debug.assert_any_call("Exclude patterns: ['group1/projectA']")
        mock_logger.debug.assert_any_call("Included Projects: \ngroup1/projectA, group1/projectB")
        mock_logger.debug.assert_any_call("Excluded Projects: \ngroup1/projectA")
