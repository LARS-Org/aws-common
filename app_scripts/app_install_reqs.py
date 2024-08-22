"""
This module is used to install all the project requirements.
"""

import os
import shutil


def _purge_pip_cache(do_log_func, run_cmd_func):
    """
    Purge the pip cache to avoid potential installation issues.
    """
    run_cmd_func(["python3.11", "-m", "pip", "cache", "purge"])
    do_log_func("*** Purged pip cache.")


def _remove_pip_selfcheck(do_log_func):
    """
    Remove the pip selfcheck directory.
    """
    selfcheck_dir = os.path.expanduser("~/.cache/pip/selfcheck/")
    if os.path.exists(selfcheck_dir):
        shutil.rmtree(selfcheck_dir)
    do_log_func("*** Removed pip cache selfcheck directory.")


def _upgrade_pip(do_log_func, run_cmd_func):
    """
    Upgrade pip to the latest version.
    """
    run_cmd_func(["pip", "install", "--upgrade", "pip", "--quiet"])
    do_log_func("*** Upgraded pip.")


def _install_essential_git_repositories(do_log_func, run_cmd_func, target=None):
    """
    Installs/upgrades essential modules dependencies directly from GitHub.
    # pip install git+https://github.com/LARS-Org/aws-common
    """
    essential_git_repos = [
        "https://github.com/LARS-Org/aws-common",
    ]

    for repo in essential_git_repos:
        do_log_func(f"*** Installing/upgrading {repo} (will be quiet)...")
        cmd_list = ["pip", "install", "--upgrade", f"git+{repo}", "--quiet"]
        if target:
            cmd_list.append("--target")
            cmd_list.append(target)
        run_cmd_func(cmd_list)


def _install_requirements_recursively(do_log_func, run_cmd_func):
    """
    Recursively traverse the project directory and install all requirements.txt files.
    """
    pip_requirements_file_list = ["requirements.txt", "requirements-dev.txt"]

    for root, dirs, files in os.walk("."):
        # Skip certain directories
        if any(
            skip in root
            for skip in [
                ".aws-sam",
                ".venv",
                ".git",
                ".pytest",
                "lib/python",
                "tests/lib/python",
                "experiments",
                "__pycache__",
                "node_modules",
                "cdk.out",
                "packages",
                "lib/python3.11/site-packages",
                "venv",
            ]
        ):
            continue

        do_log_func(f"*** Processing {root}...")

        # exclude the __init__.py files
        files = set(files) - {"__init__.py"}

        for pip_requirements_file in pip_requirements_file_list:
            if pip_requirements_file in files:
                pip_requirements_path = os.path.join(root, pip_requirements_file)
                do_log_func(f"Installing {pip_requirements_path} (will be quiet)...")
                run_cmd_func(["pip", "install", "-r", pip_requirements_path, "--quiet"])

        # Special handling for AWS Lambda Functions
        if files and root.startswith(("lambda", "./lambda")):
            packages_dir = os.path.join(root, "packages")
            # remove the packages directory if it exists
            if os.path.exists(packages_dir):
                shutil.rmtree(packages_dir)
            # create the packages directory
            os.makedirs(packages_dir)

            # install the git repositories in the packages directory
            _install_essential_git_repositories(
                do_log_func, run_cmd_func, target=packages_dir
            )

            if pip_requirements_file in files:
                do_log_func(f"Installing {pip_requirements_path} (will be quiet)...")
                # install the requirements in the packages directory
                run_cmd_func(
                    [
                        "pip",
                        "install",
                        "-r",
                        pip_requirements_path,
                        "--target",
                        packages_dir,
                        "--upgrade",
                        "--quiet",
                    ]
                )

        # Special handling for AWS Lambda Layers
        if root.startswith(("layers", "./layers")):
            run_cmd_func(
                [
                    "pip",
                    "install",
                    "-r",
                    pip_requirements_path,
                    "--target",
                    os.path.join(root, "lib/python3.11/site-packages"),
                    "--upgrade",
                    "--quiet",
                ]
            )


def _install_other_packages(do_log_func, run_cmd_func):
    """
    Install other pip packages required by the project.
    """
    other_packages = ["pylint", "black", "isort"]

    for package in other_packages:
        do_log_func(f"*** Installing/upgrading {package} (will be quiet)...")
        run_cmd_func(["pip", "install", "--upgrade", package, "--quiet"])


def do_install_req(do_log_func, run_cmd_func):
    """
    Main function to install all project requirements.
    """
    _purge_pip_cache(do_log_func, run_cmd_func)
    _remove_pip_selfcheck(do_log_func)
    _upgrade_pip(do_log_func, run_cmd_func)
    _install_essential_git_repositories(do_log_func, run_cmd_func)
    _install_requirements_recursively(do_log_func, run_cmd_func)
    _install_other_packages(do_log_func, run_cmd_func)
    do_log_func("*** All done!!!")
