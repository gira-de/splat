from pathlib import Path

from splat.config.config_loader import load_config
from splat.model import LocalProject
from splat.source_control.gitlab.ci_artifact_fetch import fetch_gitlab_ci_summary_artifact
from splat.utils.env_manager.os import OsEnvManager
from splat.utils.logger_config import logger
from splat.utils.logging_utils import generate_banner
from splat.utils.parseargs import parse_arguments
from splat.utils.project_processor.project_operations import get_logfile_url
from splat.utils.project_processor.remote_projects import process_project_with_id, process_remote_projects
from splat.utils.project_processor.single_project import process_local_project


def main() -> None:
    notification_sinks = None
    try:
        splat_banner = generate_banner("Splat")
        print(splat_banner)

        args = parse_arguments()
        if args.gitlab_ci_fetch_summary and args.access_token_name:
            fetch_gitlab_ci_summary_artifact(args.access_token_name, OsEnvManager())
        else:
            config = load_config()

            if args.local_projects is not None:
                for local_project in args.local_projects:
                    process_local_project(
                        project=LocalProject(
                            name_with_namespace=local_project.name, path=Path(local_project).resolve()
                        ),
                        config=config,
                    )
            elif args.project_id:
                process_project_with_id(args, config)
            else:
                process_remote_projects(args, config)
    except Exception as e:
        logger.update_context()
        logger.error(f"An error occurred: {e}")

        logfile_url = get_logfile_url()

        if notification_sinks and logfile_url:
            for sink in notification_sinks:
                sink.send_failure_notification(str(e), None, "Splat Execution", None, logfile_url)


if __name__ == "__main__":
    main()
