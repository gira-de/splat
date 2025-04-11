# Contributing to Splat

Thank you for considering contributing to Splat! Contributions are welcome and greatly appreciated. Please follow the guidelines below to set up your development environment and contribute effectively.

## Getting Started

### Fork the Repository

To contribute, first fork the repository to your own GitHub or GitLab account:

1. Navigate to the [Splat GitHub repository](https://github.com/gira-de/splat) # link goes here
2. Click on the "Fork" button.
3. Clone your forked repository to your local machine:

```bash
git clone git@github.com:<your-username>/splat.git
cd splat
```
4. Set up the upstream repository to keep your fork updated:
```bash
git remote add upstream git@github.com:gira-de/splat.git
```

## Development Setup

Splat runs within a Docker container, and environment variables need to be configured within this environment. The recommended approach for development is to use the Dev Containers extension from VSCode.

### Using Dev Containers Extension from VSCode

1. Install the Dev Containers extension in VSCode.
2. Open your project in VSCode.
3. Start Docker if not already.
4. Reopen in Container:
   - Press `Ctrl+Shift+P`, then select `Dev Containers: Reopen in Container`.
   - VSCode will prompt you to add Dev Container configuration files:
     - Select From 'Dockerfile': Use the existing Dockerfile.
     - Skip Select Features to add to the dev container.
   - VSCode will automatically build and start the Docker container with the development environment.
5. Set Up Environment Variables:
   - Create an environment file, for example, `.devcontainer/devcontainer.env`:

```env
GITLAB_INSTANCE_URL=https://gitlab.com
GITLAB_ACCESS_TOKEN=<your-gitlab-access-token>

GITHUB_INSTANCE_URL=https://github.com
GITHUB_ACCESS_TOKEN=<your-github-access-token>

TEAMS_WEBHOOK_URL_GENERAL=<your-teams-webhook-url>
```

**Note:** Ensure your access tokens for GitHub and GitLab have the appropriate scopes (repo for GitHub, api for GitLab).
If you don't yet have an access token for GitLab and/or GitHub, search for "how to create an access token" for your instance.

6. Load Environment Variables into the Container:
   - Modify the `devcontainer.json` file

```json
{
 "name": "Existing Dockerfile",
 "build": {
  "context": "..",
  "dockerfile": "../Dockerfile"
 },
 "runArgs": ["--env-file",".devcontainer/devcontainer.env"]
}
```

7. Rebuild the Container:
   - Rebuild the container to apply the environment configuration by pressing `Ctrl+Shift+P` and selecting `Dev Containers: Rebuild Container`.

8. Verify Environment Variables:
   - Open a terminal in VSCode (inside the container) and run `printenv` to verify the variables.

9. Setting up the virtual environment:

   ```bash
   poetry install
   ```

   If you run into trouble here, try to `rm -rf .venv/` and then re-try `poetry install`.

### Running Unit Tests

#### In VS Code

Use the Testing in VS Code, tests should be discovered automatically. You can also debug into
specific test cases here, which is very handy to analyse issues in very specific situations.

#### On Command Line

Run

```
poetry run python -m unittest discover -v -p 'test_*.py' -s tests
```

### Running and Testing Splat

With the environment set up, you can run, debug, and test Splat within the VSCode Dev Container:
```bash
splat
```
