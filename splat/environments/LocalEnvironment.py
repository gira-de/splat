from splat.interface.ExecutionEnvironmentInterface import ExecutionEnvironmentInterface
from splat.model import ProjectSummary
from splat.utils.logger_config import logger, logger_manager
from splat.utils.plugin_initializer.notification_init import initialize_notification_sinks
from splat.utils.plugin_initializer.package_managers_init import initialize_package_managers
from splat.utils.project_processor.project_filter import filter_projects
from splat.utils.project_processor.project_operations import export_json_summary
from splat.utils.project_processor.single_project import clone_and_process_project


# Local Environment Implementation
class LocalEnvironment(ExecutionEnvironmentInterface):
    def execute(self) -> None:
        """Fetch and process projects locally."""

        package_managers = initialize_package_managers(self.config.package_managers)
        notification_sinks = initialize_notification_sinks(self.config.notifications)
        logger.info("Executing Splat in Local environment...")
        project_summaries: list[ProjectSummary] = []

        for platform in self.git_platforms:
            logger.update_context(platform.type)
            # Fetch and filter projects directly
            projects = platform.fetch_projects()
            filtered_projects = filter_projects(projects, platform.config.filters)
            for project in filtered_projects:
                p_summary = clone_and_process_project(
                    project, package_managers, platform, notification_sinks, self.config
                )
                project_summaries.append(p_summary)
                logger_manager.update_logger_level(self.config.general.logging.level)
                logger.update_context()
        export_json_summary(project_summaries)
