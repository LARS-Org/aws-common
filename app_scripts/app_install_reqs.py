import os
import shutil
import subprocess
import sys


def _run_command(command, cwd=None, shell=False):
    """
    Run a shell command in the specified directory.

    :param command: The command to run.
    :param cwd: The directory to run the command in.
    :param shell: Whether to use a shell to run the command.
    """
    result = subprocess.run(command, shell=shell, cwd=cwd)
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

def install_essential_git_repositories(target=None):
    """
    Installs/upgrades essential modules dependencies directly from GitHub.
    # pip install git+https://github.com/LARS-Org/aws-common    
    """
    essential_git_repos = [
        "https://github.com/LARS-Org/aws-common",
    ]
    
    for repo in essential_git_repos:
        print(f"*** Installing/upgrading {repo} (will be quiet)...")
        cmd_list = ["pip", "install", "--upgrade", f"git+{repo}", "--quiet"]
        if target:
            cmd_list.append("--target")
            cmd_list.append(target)
        _run_command(cmd_list)

def install_requirements_recursively():
    """
    Recursively traverse the project directory and install all requirements.txt files.
    """
    pip_requirements_file_list = ["requirements.txt", "requirements-dev.txt"]
    
    for root, dirs, files in os.walk("."):
        # Skip certain directories
        if any(skip in root for skip in [
            ".aws-sam", ".venv", ".git", ".pytest", "lib/python", "tests/lib/python", 
            "experiments", "__pycache__", "node_modules", "cdk.out", "packages", 
            "lib/python3.11/site-packages", "venv",
        ]):
            continue
        
        print(f"*** Processing {root}...")
        
        # exclude the __init__.py files
        files = set(files) - {"__init__.py"}
        
        for pip_requirements_file in pip_requirements_file_list:
            if pip_requirements_file in files:
                pip_requirements_path = os.path.join(root, pip_requirements_file)
                print(f"Installing {pip_requirements_path} (will be quiet)...")
                _run_command(["pip", "install", "-r", pip_requirements_path, "--quiet"])

        # Special handling for AWS Lambda Functions
        if files and root.startswith(("lambda", "./lambda")):
            packages_dir =  os.path.join(root, "packages")
            # remove the packages directory if it exists
            if os.path.exists(packages_dir):
                shutil.rmtree(packages_dir)
            # create the packages directory
            os.makedirs(packages_dir)
            
            # install the git repositories in the packages directory
            install_essential_git_repositories(target=packages_dir)    
                
            if pip_requirements_file in files:
                print(f"Installing {pip_requirements_path} (will be quiet)...")
                # install the requirements in the packages directory
                _run_command(["pip", "install", "-r", pip_requirements_path, 
                              "--target", packages_dir, "--upgrade", "--quiet"])

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
    install_essential_git_repositories()
    install_requirements_recursively()
    install_other_packages()
    print("*** All done!!!")

if __name__ == "__main__":
    main()
