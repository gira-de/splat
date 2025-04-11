# Splat (Secure PLATform)

By Gira (https://github.com/gira-de/).

## Introduction to Splat

Splat is a bot packaged as a container image, designed to automate the process of updating vulnerable dependencies to secure versions. It finds the minimum update necessary to avoid breaking changes. Splat can automatically commit, push, and create merge requests. Additionally, it sends helpful notifications.

Splat currently focuses on automating the dependency update process. It is designed as a secure platform that can be extended to include additional security functionalities in the future, such as code analysis tools.

## Features

- **Dependency Vulnerability Scanning**: Scans supported lockfiles for vulnerabilities using auditing tool like `pip-audit` and `yarn audit`.
- **Targeted Updates**: Updates only vulnerable dependencies to the minimum secure version required, avoiding unnecessary upgrades. Major version updates are only done if necessary to fix a security vulnerability.
- **Package Manager Detection** Automatically identifies supported package managers like yarn, pipenv or poetry in the target repositories and processes related vulnerability checks and fixes.
- **Direct and Transitive Updates**: Can update both direct and transitive (aka indirect) dependencies. If the package manager supports it, it fixes security issues in transitive dependencies without updating the direct dependency.
- **Re-Scans for Remaining Vulnerabilities**: After updating all relevant dependencies, Splat performs a re-audit to check for any remaining vulnerabilities. These remaining issues, if any, are documented in the merge request. If the re-audit identifies unresolved vulnerabilities, the merge request is automatically created as a draft to prevent unintentional merges.
- **Merge/Pull Requests**: Pushes changes and creates a merge/pull request with a descriptive overview of the updates made and any issues encountered.
- **Notifications**: Sends clear and easily readable notifications for:
  - Merge request creations, updates: Splat notifies you when a merge request is created, updated, providing details about the changes and any issues encountered.
  - Dependency update process failures: If the dependency update process fails, Splat will notify you with detailed information to help you understand and resolve the problem.
- **Repository Discovery**: Automatically processes all accessible repositories using the provided access token. Custom filters can be applied via the [config file](CONFIGURATION.md).
- **Lockfile Discovery**: Processes all supported lockfiles within a repository, even in different directories.
- **Cross-Language Support**: Handles projects with multiple package managers, even for different languages (e.g., Python and JavaScript) within the same repository.
- **Commit Management**: Creates a commit for each vulnerability fixed with detailed information about the vulnerability.
- **Configuration**: Offers a flexible system with both global and project-specific configurations. The global configuration sets default behaviors for all projects, while each project can have its own splat.yaml file for specific overrides and customizations.
- **Pre-Commit Hooks**: Supports customizable pre-commit hooks configured in the [config file](CONFIGURATION.md). These hooks can run scripts or commands, such as format checkers or test runners, before commits are made.

### Supported Platforms

Splat comes with plugins for the following platforms:

- Package Managers:
  - `pipenv` (python)
  - `poetry` (python)
  - `yarn` (JavaScript)
  - `uv` (python)
- Source Control Platforms:
  - GitHub (both official and private instances)
  - GitLab (both official and private instances)
- Notifications:
  - Microsoft Teams

## Running splat

### Test-drive splat on a local repository

You can test-drive splat on a local `git` repository that you previously cloned.

That way, you can try out splat and see how it works. However, this will __not__:

- Push vulnerability fixes
- Create merge requests
- Send notifications

Instead, it will work on your local git repository so that you can inspect potential commits made by splat.

#### Create a splat configuration file

Ensure a `splat.yaml` configuration file is set up.

Here is a minimal example that you can tweak to your needs:

```yaml
general:
  logging:
    level: "INFO"
  git:
    clone_dir: "/splat/splat_repos/"
    branch_name: "splat"
  debug:
    skip_cleanup: False

package_managers:
  pipenv:
    enabled: true
  poetry:
    enabled: true
  yarn:
    enabled: true
  uv:
    enabled: true
```

#### Run splat

```bash
docker run \
  --pull=always \
  -it \
  -v <path-to-you-repository>:/home/splatuser/test-drive/ \
  -v $(pwd)/splat.yaml:/splat/splat.yaml \
  girade/splat:1 \
  splat \
  --project /home/splatuser/test-drive/
```


### Running splat on a schedule

For production use, it is recommended to create a separate repository dedicated to hosting your splat.yaml configuration file and the Pipeline schedule responsible for running Splat.

To run splat you first need to create a full `splat.yaml` configuration file and commit it to your repository. See [CONFIGURATION.md](CONFIGURATION.md).

To keep your sensitive information such as the access token out from your version control, you can use environment variables that are expanded when splat reads your configuration file.

#### Recommended Practice: Dedicated User Account
For better security and management, it is recommended to create a dedicated GitLab/GitHub user specifically for running Splat. This user should be granted an access token with the necessary scope and added to all the repositories that Splat will need to access. This approach ensures that access is controlled and isolated to this specific user, reducing the risk of unauthorized access.

Here is a minimal set of environment variables that your repo has:

|Variable|Description|
|--------|-----------|
|SPLAT_USER_ACCESS_TOKEN|This token is required by Splat to access all projects associated with the user. Depending on your platform, this should be a GitHub or GitLab user access token. Ensure the token has the appropriate scope (e.g., repo for GitHub or api for GitLab).
|SPLAT_TEAMS_WEBHOOK_URL|This URL is used for sending notifications to Microsoft Teams.|

(!) __Important:__ Please note that the environment variable names must match the names that you used in your config. You can use other names, and you can also use more environment variables in your `splat.yaml`.

#### Run on GitHub Actions
On the repository that hosts your `splat.yaml`, add a `.github/workflows/ci.yml` with the following content:

```yml
name: Splat Runner

on:
  workflow_dispatch:  # For manual execution
  schedule:
    - cron: "0 6 * * *"  # Every day at 6:00

jobs:
  splat:  # This Job fetches and prepares data for splat-core
    runs-on: ubuntu-latest
    container:
      image: girade/splat:1
      options: --user splatuser
    env:
      HOME: /splat  # Ensures Python resolves user-specific paths correctly within the container
      SPLAT_USER_ACCESS_TOKEN: ${{ secrets.SPLAT_USER_ACCESS_TOKEN }}
      SPLAT_TEAMS_WEBHOOK_URL: ${{ secrets.SPLAT_TEAMS_WEBHOOK_URL }}
    outputs:
      platform_projects: ${{ steps.runsplat.outputs.platform_projects }}
    steps:
      - uses: actions/checkout@v4
      - name: Run Splat
        id: runsplat
        run: |
          splat
          json=$(cat /splat/platform_projects.json | jq -c '.')
          echo "platform_projects=$json" >> $GITHUB_OUTPUT

  splat-core:  # This Job processes the projects data (platform_projects) output by the Splat job
    needs: splat
    runs-on: ubuntu-latest
    name: Process ${{ matrix.platform_projects.project_name }}
    container:
      image: girade/splat:1
      options: --user splatuser
    env:
      HOME: /splat  # Ensures Python resolves user-specific paths correctly within the container
      SPLAT_USER_ACCESS_TOKEN: ${{ secrets.SPLAT_USER_ACCESS_TOKEN }}
      SPLAT_TEAMS_WEBHOOK_URL: ${{ secrets.SPLAT_TEAMS_WEBHOOK_URL }}
    strategy:
      matrix:
        platform_projects: ${{ fromJson(needs.splat.outputs.platform_projects) }}
    steps:
      - uses: actions/checkout@v4
      - name: Run Splat
        run: |
          splat --platform-id ${{ matrix.platform_projects.platform_id }} --project-id ${{ matrix.platform_projects.project_id }}
```

#### Run on GitLab CI

On the repository that hosts your `splat.yaml`, add a `.gitlab-ci.yml` with the following content:

```yaml
splat: # Upstream pipeline responsible for creating downstream pipeline config file named child-pipeline.yml
  image:
    name: girade/splat:1
    pull_policy: always # Always pull the latest splat image so that we are using the most up-to-date version with all new features and security fixes
    docker:
      user: splatuser # Don't run the container as root
  script:
    - splat
  rules:
    - if: '$CI_PIPELINE_SOURCE == "web"'
      when: always # Run splat when you manually create a new pipeline
    - if: '$CI_PIPELINE_SOURCE == "schedule"'
      when: always # Run splat on a schedule
    - when: manual # Don't automatically run the pipeline for other reasons, such as pushing to the repository
  artifacts:
    paths:
      - splat.yaml
      - child-pipeline.yml

splat_core: # Downstream pipeline responsible for processing child pipeline jobs
  needs: [splat]
  trigger:
    include:
      - artifact: child-pipeline.yml
        job: splat
    strategy: depend
    forward:
      pipeline_variables: true # forwards CI/CD variables from the parent pipeline to the downstream pipeline (e.g. SPLAT_USER_ACCESS_TOKEN, SPLAT_TEAMS_WEBHOOK_URL).
  rules:
    - when: on_success
  variables:
    DEFAULT_SPLAT_IMAGE: girade/splat:1 # Default Docker image to use in the downstream pipeline
```


After that, go to your GitLab Web UI and create a scheduled pipeline for this repository. We recommend to run splat once per day.

To test splat immediately, you can manually run a new pipeline for this repository.
