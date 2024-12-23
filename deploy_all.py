#!/usr/bin/env python3
"""
Script to deploy all project modules in immediate subfolders.

For each immediate subfolder:
1. Activates the Python virtual environment at .venv/bin/activate
2. Runs python app_setup.py deploy
"""

import os
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
        result = subprocess.run(
            command,
            shell=shell,
            cwd=cwd,
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}' in {cwd}:")
        print(e.stderr)
        return False


def deploy_module(module_path):
    """
    Deploy a single module by activating its venv and running app_setup.py deploy.

    Args:
        module_path: Path to the module directory
    
    Returns:
        True if deployment succeeded, False otherwise
    """
    print(f"\nDeploying module in {module_path}...")
    
    # Check if .venv exists
    venv_path = os.path.join(module_path, ".venv")
    if not os.path.exists(venv_path):
        print(f"No .venv found in {module_path}, skipping...")
        return False
        
    # Check if app_setup.py exists
    setup_script = os.path.join(module_path, "app_setup.py")
    if not os.path.exists(setup_script):
        print(f"No app_setup.py found in {module_path}, skipping...")
        return False

    # Get the activate script path
    if sys.platform == "win32":
        activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
    else:
        activate_script = os.path.join(venv_path, "bin", "activate")

    if not os.path.exists(activate_script):
        print(f"No activation script found at {activate_script}, skipping...")
        return False

    # Create command that sources venv and runs deploy
    if sys.platform == "win32":
        command = f'"{activate_script}" && python app_setup.py deploy'
    else:
        command = f'source "{activate_script}" && python app_setup.py deploy'

    # Run the deployment command
    return run_command(command, cwd=module_path, shell=True)


def main():
    """Main function to deploy all modules."""
    print("Starting deployment of all modules...")
    
    # First ensure AWS SSO login is done
    if not run_command("aws sso login", shell=True):
        print("AWS SSO login failed, aborting deployment")
        sys.exit(1)

    # Get current directory
    current_dir = os.getcwd()
    
    # Get immediate subdirectories
    subdirs = [
        d for d in os.listdir(current_dir)
        if os.path.isdir(os.path.join(current_dir, d)) and not d.startswith('.')
    ]

    if not subdirs:
        print("No subdirectories found to deploy")
        return

    # Deploy each module
    success_count = 0
    for subdir in subdirs:
        module_path = os.path.join(current_dir, subdir)
        if deploy_module(module_path):
            success_count += 1

    # Print summary
    print(f"\nDeployment complete: {success_count}/{len(subdirs)} modules deployed successfully")
    if success_count != len(subdirs):
        sys.exit(1)


if __name__ == "__main__":
    main()