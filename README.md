
# aws-common
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
## Python environment
### Installing Pipenv
Python environment is maintained with Pipenv. To install Pipenv, ensure you have Python and pip installed in your environment and run:
```bash
pip install pipenv [--user]
```

Use the `--user` option if you want Pipenv available only for your user.

Alternatively, on `apt`-based environments like Ubuntu, you can install Pipenv by running:
```bash
sudo apt install pipenv
```

For more details about Pipenv installation, see https://pipenv.pypa.io/en/latest/installation.html

### Installing PyEnv
Pipenv uses PyEnv to install the specific Python version required by `aws_common`. To install PyEnv, run:

```bash
curl https://pyenv.run | bash
```

After the install completes, configure your shell to find PyEnv. Assuming you are using bash, run:
```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
```

For more details about PyEnv installation, see https://github.com/pyenv/pyenv-installer

### Installing required modules
To install required modules, run:

```bash
pipenv install
```
### Setting Up the Development Environment
To install required modules for development, run:
```bash
pipenv install --dev
```
#### Pre-commit Hooks
We use `pre-commit` to ensure consistent code quality. Install the pre-commit hooks by running:
```bash
pipenv run pre-commit install
```
#### Code Formatting and Quality Checks
- To format code with **Black**:
```bash
pipenv run black .
```
- To sort imports with **isort**:
```bash
pipenv run isort .
```
- To check code quality with **Flake8**:
```bash
pipenv run flake8 .
```
These tools help maintain code quality and consistency across the project.
## Unit tests
To run unit tests, after installing required modules for development, run:
```bash
pipenv shell
pytest
```

