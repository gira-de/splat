import json
from pathlib import Path

from splat.utils.fs import FileSystemInterface, RealFileSystem


def aggregate_summaries(input_dir: str, output_file: str, fs: FileSystemInterface = RealFileSystem()) -> None:
    input_path = Path(input_dir)
    output_path = Path(output_file)

    # Check if input directory exists
    if not fs.exists(str(input_path)):
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist.")

    # Ensure the output directory exists
    fs.mkdir(str(output_path.parent), parents=True, exist_ok=True)
    all_summaries: list[str] = []

    # Iterate over all JSON files in the input directory
    for json_file in fs.glob(str(input_path), "*.json"):
        summaries = json.loads(fs.read(json_file))
        all_summaries.extend(summaries)

    # Write the combined summary to the output file
    fs.write(output_file, json.dumps(all_summaries, sort_keys=False, indent=2))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aggregate project summaries")
    parser.add_argument("--input-dir", type=str, required=True, help="Directory containing project summary JSON files")
    parser.add_argument("--output-file", type=str, required=True, help="Output file for combined summary")

    args = parser.parse_args()
    aggregate_summaries(args.input_dir, args.output_file)
