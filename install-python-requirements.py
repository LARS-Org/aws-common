import os
import subprocess
import sys
import shutil

def _run_command(command, shell=False):
    """
    Run a shell command.
    
    :param command: The command to run.
    :param shell: Whether to use a shell to run the command.
    """
    result = subprocess.run(command, shell=shell)
    if result.returncode != 0:
        sys.exit(result.returncode)

def purge_pip_cache():
    """
    Purge the pip cache to avoid potential installation issues.
    """
    _run_command(["python3.11", "-m", "pip", "cache", "purge"])
    print("*** Purged pip cache.")

def remove_pip_selfcheck():
    """
    Remove the pip selfcheck directory.
    """
    selfcheck_dir = os.path.expanduser("~/.cache/pip/selfcheck/")
    if os.path.exists(selfcheck_dir):
        shutil.rmtree(selfcheck_dir)
    print("*** Removed pip cache selfcheck directory.")

def upgrade_pip():
    """
    Upgrade pip to the latest version.
    """
    _run_command(["pip", "install", "--upgrade", "pip", "--quiet"])
    print("*** Upgraded pip.")

def install_essential_packages():
    """
    Install essential pip packages required by the project.
    """
    essential_packages = [
        "h5py",
        "typing-extensions",
        "wheel",
        "setuptools",
        "aws-sam-cli"
    ]
    
    for package in essential_packages:
        print(f"*** Installing/upgrading {package} (will be quiet)...")
        _run_command(["pip", "install", "--upgrade", package, "--quiet"])

def install_requirements_recursively():
    """
    Recursively traverse the project directory and install all requirements.txt files.
    """
    pip_requirements_file = "requirements.txt"
    
    for root, dirs, files in os.walk("."):
        # Skip certain directories
        if any(skip in root for skip in [
            ".aws-sam", ".venv", ".git", ".pytest", "lib/python", "tests/lib/python", "experiments"
        ]):
            continue
        
        if pip_requirements_file in files:
            pip_requirements_path = os.path.join(root, pip_requirements_file)
            print(f"Installing {pip_requirements_path} (will be quiet)...")
            _run_command(["pip", "install", "-r", pip_requirements_path, "--quiet"])

            # Special handling for AWS Lambda Functions
            if root.startswith(("lambda", "./lambda")):
                _run_command(["pip", "install", "-r", pip_requirements_path, 
                              "--target", os.path.join(root, "packages"), "--upgrade", "--quiet"])

            # Special handling for AWS Lambda Layers
            if root.startswith(("layers", "./layers")):
                _run_command(["pip", "install", "-r", pip_requirements_path, 
                              "--target", os.path.join(root, "lib/python3.11/site-packages"), "--upgrade", "--quiet"])

def install_other_packages():
    """
    Install other pip packages required by the project.
    """
    other_packages = [
        "pylint",
        "black",
        "isort"
    ]
    
    for package in other_packages:
        print(f"*** Installing/upgrading {package} (will be quiet)...")
        _run_command(["pip", "install", "--upgrade", package, "--quiet"])

def main():
    purge_pip_cache()
    remove_pip_selfcheck()
    upgrade_pip()
    install_essential_packages()
    install_requirements_recursively()
    install_other_packages()
    print("*** All done!!!")

if __name__ == "__main__":
    main()
