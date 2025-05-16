import unittest

from splat.utils.command_runner.safe_run import is_command_whitelisted


class TestSubprocessHandler(unittest.TestCase):
    def test_is_command_whitelisted_with_valid_command_and_args(self) -> None:
        cmd = "/usr/local/bin/pipenv"  # Bypass type checking with Any
        args = ["install"]
        result = is_command_whitelisted(cmd, args)
        self.assertTrue(result)

    def test_is_command_whitelisted_with_invalid_command(self) -> None:
        cmd = "/invalid/command"
        args = ["install"]
        result = is_command_whitelisted(cmd, args)
        self.assertFalse(result)

    def test_is_command_whitelisted_with_invalid_args(self) -> None:
        cmd = "/usr/local/bin/pipenv"
        args = ["invalid", "arg"]
        result = is_command_whitelisted(cmd, args)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
