# AWS CDK Common

`aws-cdk-common` is a shared package for common modules and constants for AWS Lambda applications based on AWS CDK. It provides essential tools and configurations for managing AWS resources efficiently.

## Python Environment

### Installing Poetry
[Poetry](https://python-poetry.org/) is a tool to manage Python projects in a deterministic way. Follow the instructions to set up your environment.

### Installing Required Modules
To install required modules, run:
```bash
poetry install --no-root
```

### Development Environment Setup
To install required modules for development, run:
```bash
poetry install --with dev --no-root
```

### Activating the Virtual Environment
To activate the virtual environment:
- **Linux/macOS**:
  ```bash
  source $(poetry env info --path)/bin/activate
  ```
- **Windows (PowerShell)**:
  ```powershell
  . $(poetry env info --path)/Scripts/activate
  ```

### Pre-commit Hooks
Install pre-commit hooks to ensure consistent code quality:
```bash
poetry run pre-commit install
```

### Code Formatting and Quality Checks
- Format code with **Black**:
  ```bash
  poetry run black .
  ```
- Sort imports with **isort**:
  ```bash
  poetry run isort .
  ```
- Check code quality with **Flake8**:
  ```bash
  poetry run flake8 .
  ```

## Tests

### Unit Tests
Run unit tests:
```bash
poetry run pytest tests/unit
```

### Integration Tests
Run integration tests:
```bash
poetry run pytest tests/integration
```

### All Tests
Run all tests:
```bash
poetry run pytest
```

## Deployment
To deploy the application, use:
```bash
python app_setup.py deploy
```
For a faster deployment without installations or tests, use:
```bash
python app_setup.py fast_deploy
```

## Setup
Ensure that the `aws-common` repository is cloned and updated as part of the setup process.
