
# aws-cdk-common
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

`aws-cdk-common` is a shared package for common modules and constants for AWS Lambda applications based on AWS CDK.

## Python environment
### Installing Poetry
[Poetry](https://python-poetry.org/) is a tool to manage Python projects in a deterministic way.

#### Installing pipx
`pipx` installs and run Python applications in isolated environment. Follow the instructions listed in [pipx documentation](https://github.com/pypa/pipx) for your specific environment.

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
pipenv run isort .
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
poetry shell
pytest tests/unit
```

### Integration tests
To run unit tests, after installing required modules for development, run:
```bash
poetry shell
pytest tests/integration
```

### All tests
You can also run all tests (unit and integration) by running:
```bash
poetry shell
pytest 
```
