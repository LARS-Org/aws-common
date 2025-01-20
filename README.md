
# aws-cdk-common
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

`aws-cdk-common` is a shared package for common modules and constants for AWS Lambda applications based on AWS CDK.

## Python environment
### Installing Poetry
[Poetry](https://python-poetry.org/) is a tool to manage Python projects in a deterministic way.

#### Installing pipx
`pipx` installs and runs Python applications in an isolated environment. Follow the instructions listed in [pipx documentation](https://github.com/pypa/pipx) for your specific environment.

#### Installing Poetry

```bash
pipx install poetry
```

### Installing required modules
To install required modules, run:

```bash
poetry install --no-root
```
### Setting Up the Development Environment
To install required modules for development, run:
```bash
poetry install --with dev --no-root
```

### Activating the Virtual Environment
Starting with Poetry 2.x, the `poetry shell` command is no longer available. To activate the virtual environment:

1. Find the path to the Poetry-managed virtual environment:
   ```bash
   poetry env info --path
   ```

2. Activate the virtual environment:
   - **Linux/macOS**:
     ```bash
     source $(poetry env info --path)/bin/activate
     ```
   - **Windows (PowerShell)**:
     ```powershell
     . $(poetry env info --path)/Scripts/activate
     ```

Alternatively, you can directly execute commands in the Poetry-managed environment without activating the shell by prefixing commands with `poetry run`.

#### Pre-commit Hooks
We use `pre-commit` to ensure consistent code quality. Install the pre-commit hooks by running:
```bash
poetry run pre-commit install
```

#### Code Formatting and Quality Checks
- To format code with **Black**:
```bash
poetry run black .
```
- To sort imports with **isort**:
```bash
poetry run isort .
```
- To check code quality with **Flake8**:
```bash
poetry run flake8 .
```
These tools help maintain code quality and consistency across the project.

## Tests

### Unit tests
To run unit tests, after installing required modules for development, run:
```bash
poetry run pytest tests/unit
```

### Integration tests
To run integration tests, after installing required modules for development, run:
```bash
poetry run pytest tests/integration
```

### All tests
You can also run all tests (unit and integration) by running:
```bash
poetry run pytest
```
