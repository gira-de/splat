import unittest

from splat.model import Dependency
from splat.package_managers.pipenv.pipenv_graph_parser import get_uppermost_parent_deps


class TestPipenvGraphParser(unittest.TestCase):
    def setUp(self) -> None:
        with open("tests/package_managers/pipenv/pipenv_graph_parser/mock_pipenv_graph_output.json") as f:
            self.mock_pipenv_graph_output = f.read()

    def test_get_uppermost_parent_deps_has_two_direct_parent_deps(self) -> None:
        dependency_name = "package3"
        direct_deps_names = {"package1", "package4"}

        expected_parents = {("package1"), ("package4")}

        actual_parents = get_uppermost_parent_deps(self.mock_pipenv_graph_output, dependency_name, direct_deps_names)

        self.assertEqual(
            sorted(actual_parents),
            sorted(expected_parents),
        )

    def test_get_uppermost_parent_deps_no_direct_deps(self) -> None:
        dependency_name = "package3"
        direct_deps_names: set[str] = set()

        # No direct dependencies, so no parents should be found
        expected_parents: list[Dependency] = []

        actual_parents = get_uppermost_parent_deps(self.mock_pipenv_graph_output, dependency_name, direct_deps_names)

        self.assertEqual(
            actual_parents,
            expected_parents,
        )

    def test_get_uppermost_parent_deps_circular_dependency(self) -> None:
        # In the mock data, created circular dependency scenario
        # Assuming packageC -> packageB -> packageA -> packageC (a loop)
        dependency_name = "packageC"
        direct_deps_names = {"packageA", "packageB"}

        with open("tests/package_managers/pipenv/pipenv_graph_parser/mock_circular_pipenv_graph_output.json") as f:
            mock_circular_pipenv_graph_output = f.read()

        # Expected outcome: Since packageC itself is direct it should return empty set
        expected_parents: list[Dependency] = []

        actual_parents = get_uppermost_parent_deps(
            mock_circular_pipenv_graph_output, dependency_name, direct_deps_names
        )

        self.assertListEqual(
            actual_parents,
            expected_parents,
        )
