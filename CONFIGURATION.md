# Configuration File Reference

Before running splat, make sure to create a YAML file in the root of the splat project named 'splat.yaml'. This file should contain the necessary configurations for source control platforms, notifications, package managers, hooks, and other settings. Below is an example configuration file:

**Note:** Ensure that your access tokens for GitLab and GitHub have the appropriate scope (e.g., repo for GitHub, api for GitLab).

```yaml
general:
  logging:
    level: "INFO"  # Optional, default: INFO. Available: ERROR, WARNING, INFO, DEBUG (from less to more verbose)
  git:
    clone_dir: "/splat/splat_repos/"  # Optional, default: /splat/splat_repos/. Directory for cloning repositories
    branch_name: "splat"  # Optional, default: splat
  debug:
    skip_cleanup: False  # Optional, default: False. Whether to skip cleanup of cloned projects

source_control: # Required
  platforms:  # Configuration for source control platforms
    - type: github  # Required
      id: github-1  # Optional identifier for use with the --platform-id flag in splat commands
      name: GitHub.com  # Optional
      domain: "https://github.com"  # Required, just the base domain URL (not the API URL)
      access_token: ${GITHUB_ACCESS_TOKEN}  # Required, must be a GitHub-specific access token
      filters:  # Optional
        exclude: ["user/test.*", "user/dontcheckme.*"]  # Optional, default: []. Repositories to exclude
        include: ["user/test.*"]  # Optional, default: [all accessible projects]. Repositories to include

    - type: gitlab
      id: gitlab-1
      domain: my.gitlab.instance
      access_token: ${GITLAB_ACCESS_TOKEN}  # Required, must be a GitLab-specific access token
      filters:
        exclude: []
        include: []

notifications: # Optional
  sinks:
    - type: teams  # Required
      webhook_url: ${TEAMS_WEBHOOK_URL}  # Required
      merge_request:
        webhook_url: ${TEAMS_WEBHOOK_URL}  # Optional, uses general webhook if not specified
      update_failure:
        webhook_url: ${TEAMS_WEBHOOK_URL}  # Optional
      error:
        webhook_url: ${TEAMS_WEBHOOK_URL}  # Optional

hooks:  # Optional, uses the following Variables: `${SPLAT_MATCHED_FILES}`, `${SPLAT_MANIFEST_FILE}`, `${SPLAT_LOCK_FILE}`, `${SPLAT_PROJECT_ROOT}`, and `${SPLAT_PACKAGE_ROOT}` See Variables for Hooks section.
  pre_commit:  # Pre Commit Hooks are run before committing files that match the given pattern (supports glob and regex)
    "*.py":  # Pattern to match files (glob pattern)
      script:
        - "black ${SPLAT_MATCHED_FILES}"  # script to run before committing matched files
      cwd: "${SPLAT_PROJECT_ROOT/python-project}"  # Working directory for the script
      one_command_per_file: true  # Optional, default: false. If true, runs the command separately for each matched file

    "/*/yarn.lock$/":  # Regex pattern (starts and ends with /)
      script:
        - yarn format ${SPLAT_MATCHED_FILES}
        - yarn install
      cwd: "${SPLAT_PROJECT_ROOT}"


package_managers: # Optional
  # Configuration for package managers, all are enabled by default
  pipenv:
    enabled: false  # Optional, default: true.
    repositories:  # same as poetry
  poetry:
    enabled: false  # Optional, default: true.
    repositories:  # Optional: Configure custom package repositories for package management.
      my_custom_repo:  # # Each key in the repositories map represents a unique identifier for the repository.
      # The repository configuration supports the following fields:
        url: "https://custom-repo.com/simple/"  # (Required) The URL of the repository.
        credentials:  # (Optional) Authentication details.
          username: $MY_USERNAME  # Your username for repository authentication.
          password: $MY_PASSWORD  # Your password for repository authentication.
          token: $TOKEN  # An access token that can be used instead of username/password.

  yarn:
    enabled: false  # Optional, default: true.
    repositories:  # Optional: Configure custom package repositories for Yarn.
      "@scoped_repo":  # Scoped repository: key must start with '@' and be enclosed in double quotes.
        url: "https://custom-yarn-repo.com/"  # (Required) The URL of the Yarn repository.
        credentials:  # (Optional) Authentication details.
          username: $MY_USERNAME  # Your username for repository authentication.
          password: $MY_PASSWORD  # Your password for repository authentication.
          token: $TOKEN   # An access token that can be used instead of username/password.
      custom_repo:  # Non-scoped repository: use any arbitrary name without '@'.
        url: "https://non-scoped-yarn-repo.com/"  # (Required) The URL of the Yarn repository.
        credentials: # Same as scoped repository
  uv:
    enabled: false  # Optional, default: true.
    repositories:  # same as poetry

```

## Variables for Hooks

When configuring hooks, you can use several predefined variables in your scripts:

- `${SPLAT_MATCHED_FILES}`: This variable contains the list of files that matched the hook pattern. It is useful for running commands on these specific files.
- `${SPLAT_MANIFEST_FILE}`: The path to the project's manifest file (e.g., package.json for yarn or pyproject.toml for poetry).
- `${SPLAT_LOCK_FILE}`: The path to the lock file being processed (e.g., yarn.lock or Pipfile.lock).
- `${SPLAT_PROJECT_ROOT}`: The root directory of the project being processed.
- `${SPLAT_PACKAGE_ROOT}`: The root directory of the splat package.

## Project-Specific Configuration

Splat supports project-specific configurations, allowing you to override the global settings on a per-project basis. To use this feature, simply place a `splat.yaml` file in the root directory of the specific project. This local configuration lets you adjust settings for logging, Git, debug options, notification sinks, hooks, and package managers specifically for that project.

### Example Project-Specific Configuration

```yaml
general:
  logging:
    level: "ERROR"  # Override logging level for this project
  git:
    branch_name: "feature-branch"  # Override the branch name for this project
  debug:
    skip_cleanup: True  # Override debug options for this project

notifications:
  use_global_config: false  # Optional, default: True, Use only the local notification settings for this project
  sinks:
    - type: teams
      webhook_url: ${TEAMS_PROJECT_WEBHOOK_URL}

hooks:
  use_global_config: false  # Optional, default True, Disable global hooks and use only the local ones
  pre_commit:
    "*.py":
      script:
        - "flake8 ${SPLAT_MATCHED_FILES}"  # Run flake8 for Python files before committing
      cwd: "${SPLAT_PROJECT_ROOT}/src"

package_managers:
  pipenv:
    enabled: true  # Enable pipenv only for this project
    repositories:  # same as poetry
  yarn:
    enabled: false  # Disable yarn for this project
  poetry:
    enabled: true  # Enable poetry for this project.
    repositories:
      custom_repo:           # This local repository overrides or adds to the global configuration.
        url: "https://local-poetry-repo.com/simple/"
        credentials:
          token: ${POETRY_REPO_TOKEN}
  uv:
    enabled: true
    repositories:  # same as poetry
```

* Local repositories can override global repository settings or add new entries:
  * If a repository key exists in both the global and local configurations, the local value will override the global one.
  * New repository entries provided in the local config will be added with the global ones.

**Note:** For the `domain`, `access_token`, and all `webhook_url` fields, you can set these values either directly as strings or as the names of environment variables. If using environment variables, wrap the names in `${}`. For example: `domain: ${GITLAB_DOMAIN}`.
