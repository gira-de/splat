import unittest

from splat.package_managers.common.pip_repo_auth import normalize_url


class TestNormalizeUrl(unittest.TestCase):
    def test_trailing_slash(self) -> None:
        url = "https://example.com/path/"
        self.assertEqual(normalize_url(url), "https://example.com/path")

    def test_no_trailing_slash(self) -> None:
        url = "https://example.com/path"
        self.assertEqual(normalize_url(url), "https://example.com/path")

    def test_multiple_trailing_slashes(self) -> None:
        url = "https://example.com/path///"
        self.assertEqual(normalize_url(url), "https://example.com/path")

    def test_no_path(self) -> None:
        url = "https://example.com"
        self.assertEqual(normalize_url(url), "https://example.com")

    def test_empty_path(self) -> None:
        url = "https://example.com/"
        self.assertEqual(normalize_url(url), "https://example.com")
