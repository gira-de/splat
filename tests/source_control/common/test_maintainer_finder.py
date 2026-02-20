import unittest

from splat.source_control.common.maintainer_finder import (
    find_project_maintainer,
    parse_maintainer_from_topics,
)
from tests.mocks.mock_logger import MockLogger


class TestFindProjectMaintainer(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = MockLogger()
        self.project_name = "group/repo"

    def test_find_project_maintainer_returns_none_when_no_topics(self) -> None:
        maintainer = find_project_maintainer(self.project_name, [], self.logger)
        self.assertIsNone(maintainer)
        self.assertTrue(self.logger.has_logged(f"No project topics found for {self.project_name}"))

    def test_find_project_maintainer_returns_none_when_no_matching_topic(self) -> None:
        maintainer = find_project_maintainer(self.project_name, ["security", "backend"], self.logger)
        self.assertIsNone(maintainer)
        self.assertTrue(self.logger.has_logged(f"No maintainer topic found for {self.project_name}"))

    def test_find_project_maintainer_returns_maintainer_when_topic_matches(self) -> None:
        maintainer = find_project_maintainer(self.project_name, ["splat-maintainer:MaintainerUser"], self.logger)
        self.assertEqual(maintainer, "MaintainerUser")
        self.assertTrue(self.logger.has_logged(f"Found matching project topic for {self.project_name}: MaintainerUser"))


class TestParseMaintainerFromTopics(unittest.TestCase):
    def test_parse_maintainer_from_topics_prioritizes_primary_and_preserves_username_case(self) -> None:
        maintainer = parse_maintainer_from_topics(["maintainer:FallbackUser", "SPLAT-MAINTAINER-PrimaryUser"])
        self.assertEqual(maintainer, "PrimaryUser")

    def test_parse_maintainer_from_topics_uses_fallback_when_primary_is_missing(self) -> None:
        maintainer = parse_maintainer_from_topics(["Maintainer:FallbackUser"])
        self.assertEqual(maintainer, "FallbackUser")

    def test_parse_maintainer_from_topics_accepts_colon_primary_prefix_for_backward_compat(self) -> None:
        maintainer = parse_maintainer_from_topics(["SPLAT-MAINTAINER:CompatUser"])
        self.assertEqual(maintainer, "CompatUser")

    def test_parse_maintainer_from_topics_uses_hyphen_fallback_when_primary_is_missing(self) -> None:
        maintainer = parse_maintainer_from_topics(["MAINTAINER-FallbackUser"])
        self.assertEqual(maintainer, "FallbackUser")

    def test_parse_maintainer_from_topics_returns_none_when_no_valid_topic_exists(self) -> None:
        maintainer = parse_maintainer_from_topics(["", "   ", "topic:owner"])
        self.assertIsNone(maintainer)

    def test_parse_maintainer_from_topics_ignores_empty_prefixed_topics(self) -> None:
        maintainer = parse_maintainer_from_topics(["splat-maintainer-", "maintainer-"])
        self.assertIsNone(maintainer)

    def test_parse_maintainer_from_topics_uses_prefix_priority_order(self) -> None:
        maintainer = parse_maintainer_from_topics(
            ["splat-maintainer-PrimaryByTopicOrder", "splat-maintainer:PreferredByPrefixOrder"]
        )
        self.assertEqual(maintainer, "PreferredByPrefixOrder")

    def test_parse_maintainer_from_topics_preserves_maintainer_case(self) -> None:
        maintainer = parse_maintainer_from_topics(["SPLAT-MAINTAINER:Team.Owner+Sec@Example.com"])
        self.assertEqual(maintainer, "Team.Owner+Sec@Example.com")
