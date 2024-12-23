#!/usr/bin/env python3
"""
Script to deploy all project modules in immediate subfolders.

For each immediate subfolder:
1. Activates the Python virtual environment at .venv/bin/activate
2. Runs python app_setup.py deploy
"""

import os
import shutil
import subprocess
import sys


def run_command(command, cwd=None, shell=False, env=None):
    """
    Run a shell command in the specified directory.

    Args:
        command: The command to run
        cwd: Working directory to run the command in
        shell: Whether to run command through shell
        env: Environment variables dict to use

    Returns:
        True if command succeeded, False otherwise
    """
    try:
        subprocess.run(
            command,
            shell=shell,
            cwd=cwd,
            env=env,
            check=True,
            capture_output=False,
            text=True,
            # ensure the command output is shown in the console
            stdout=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}' in {cwd}:\n{e}")
        return False


def deploy_module(module_path):
    """
    Deploy a single module by activating its venv and running app_setup.py deploy.

    Args:
        module_path: Path to the module directory

    Returns:
        True if deployment succeeded, False otherwise
    """
    # Check if app_setup.py exists
    setup_script = os.path.join(module_path, "app_setup.py")
    if not os.path.exists(setup_script):
        print(f"No app_setup.py found in {module_path}, skipping...")
        return False

    # Recreate the Python virtual environment using the app_setup.py script
    command = "python3.11 app_setup.py setup"
    if not run_command(command, cwd=module_path, shell=True):
        print(f"Failed to recreate virtual environment in {module_path}, skipping...")
        return False

    print(f"Recreated virtual environment in {module_path}")

    # the .venv directory is created by the app_setup.py script
    venv_path = os.path.join(module_path, ".venv")

    # Get the activate script path
    if sys.platform == "win32":
        activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
    else:
        activate_script = os.path.join(venv_path, "bin", "activate")

    # Create command that sources venv and runs deploy
    if sys.platform == "win32":
        command = f"{activate_script} && python app_setup.py deploy"
    else:
        command = (
            f"/bin/bash -c 'source \"{activate_script}\" && python app_setup.py deploy'"
        )

    # Ensure the right permissions to allow the activate script
    # execution by a external process
    os.chmod(activate_script, 0o755)

    # Run the environment activation command
    if not run_command(command, cwd=module_path, shell=True):
        print(f"Failed to deploy {module_path}, skipping...")
        return False
    # else: Everything right
    print(f"Deployed {module_path} successfully.")
    return True


def main():
    """Main function to deploy all modules."""
    print("Starting deployment of all modules...")

    # First ensure AWS SSO login is done
    if not run_command("aws sso login", shell=True):
        print("AWS SSO login failed, aborting deployment")
        sys.exit(1)

    # Check if there is a global python3.11 installation available
    if not shutil.which("python3.11"):
        print("Python 3.11 not found, skipping...")
        return False

    # Get the base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    print(f"Base directory: {base_dir}")

    # Get immediate subdirectories
    subdirs = [
        d
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
        and not d.startswith(".")
        and d not in ["aws-common"]
    ]

    if not subdirs:
        print("No subdirectories found to deploy")
        return

    print(f"Found {len(subdirs)} subdirectories to deploy")
    print("\nSubdirectories:")
    for subdir in subdirs:
        print(f"  {subdir}")

    # Deploy each module
    success_count = 0
    new_line_str = "\n" + "-" * 80
    for subdir in subdirs:
        module_path = os.path.join(base_dir, subdir)
        print(new_line_str)
        print(f"Deploying module in {module_path}...")
        print(new_line_str)
        if deploy_module(module_path):
            success_count += 1

    # Print summary
    print(
        f"\nDeployment complete: {success_count}/{len(subdirs)}"
        " modules deployed successfully"
    )
    if success_count != len(subdirs):
        sys.exit(1)


if __name__ == "__main__":
    main()
