import json
import unittest

from splat.utils.aggregate_summaries import aggregate_summaries
from tests.mocks import MockFileSystem


class TestAggregateSummaries(unittest.TestCase):
    def setUp(self) -> None:
        self.fs = MockFileSystem()
        # Ensure the input directory exists but is empty
        self.fs.directories.add("input")

        self.fs.files["input/summary1.json"] = json.dumps([{"name": "Project1", "status": "success"}])
        self.fs.files["input/summary2.json"] = json.dumps([{"name": "Project2", "status": "failure"}])

    def test_aggregate_two_summaries(self) -> None:
        # Mock the input directory and output file
        input_dir = "input"
        output_file = "output/combined_summary.json"
        aggregate_summaries(input_dir, output_file, fs=self.fs)
        # Verify output directory creation
        self.assertIn("output", self.fs.directories)
        # Verify the combined summary file
        self.assertIn(output_file, self.fs.files)
        output_mock_file = self.fs.files[output_file]
        combined = json.loads(output_mock_file)

        self.assertEqual(
            combined,
            [
                {"name": "Project1", "status": "success"},
                {"name": "Project2", "status": "failure"},
            ],
        )

    def test_empty_input_directory(self) -> None:
        # Mock an empty input directory
        input_dir = "empty_input"
        output_file = "output/empty_summary.json"
        # Ensure the input directory exists but is empty
        self.fs.directories.add(input_dir)
        aggregate_summaries(input_dir, output_file, fs=self.fs)
        # Verify the output file is created but empty
        self.assertIn(output_file, self.fs.files)
        output_mock_file = self.fs.files[output_file]
        combined = json.loads(output_mock_file)
        self.assertEqual(combined, [])

    def test_nonexistent_input_directory(self) -> None:
        input_dir = "nonexistent_input"
        output_file = "output/combined_summary.json"
        with self.assertRaises(FileNotFoundError):
            aggregate_summaries(input_dir, output_file, fs=self.fs)

    def test_nonexistent_output_directory(self) -> None:
        input_dir = "input"
        output_file = "nonexistent_output/combined_summary.json"
        aggregate_summaries(input_dir, output_file, fs=self.fs)
        # Verify output directory created
        self.assertIn("nonexistent_output", self.fs.directories)
        self.assertIn(output_file, self.fs.files)


if __name__ == "__main__":
    unittest.main()
