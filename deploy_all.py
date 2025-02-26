"""
Script to deploy all project modules in immediate subfolders.

For each immediate subfolder:
1. Activates the Python virtual environment at venv/bin/activate
2. Runs python app_setup.py deploy
"""

import os
import shutil
import subprocess
import sys
import time
from functools import wraps


def retry_on_failure(max_attempts=3, delay=5):
    """
    Decorator that retries a function on failure.

    Args:
        max_attempts: Maximum number of attempts to retry
        delay: Delay in seconds between retries

    Returns:
        Decorator function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        print(f"Failed after {max_attempts} attempts")
                        return False
                    print(f"Attempt {attempts} failed: {str(e)}")
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
            return False

        return wrapper

    return decorator


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


@retry_on_failure(max_attempts=3, delay=5)
def deploy_module(module_path):
    """
    Deploy a single module by activating its venv and running app_setup.py deploy.
    Before deployment, updates the git repository by fetching and pulling the
    main branch.

    Args:
        module_path: Path to the module directory

    Returns:
        True if deployment succeeded, False otherwise
    """
    # First update the git repository
    print(f"Updating git repository in {module_path}...")

    # Checkout the main branch
    if not run_command(["git", "checkout", "main"], cwd=module_path):
        print(f"Failed to checkout main branch in {module_path}, skipping...")
        return False

    # Fetch all remote branches
    if not run_command(["git", "fetch"], cwd=module_path):
        print(f"Failed to fetch git repository in {module_path}, skipping...")
        return False

    # Pull the main branch
    if not run_command(["git", "pull"], cwd=module_path):
        print(f"Failed to pull main branch in {module_path}, skipping...")
        return False

    print(f"Git repository updated successfully in {module_path}")

    # Check if app_setup.py exists
    setup_script = os.path.join(module_path, "app_setup.py")
    if not os.path.exists(setup_script):
        print(f"No app_setup.py found in {module_path}, skipping...")
        return False

    # Recreate the Python virtual environment using the app_setup.py script
    command = "python3.11 app_setup.py setup --ignore_central_venv"
    if not run_command(command, cwd=module_path, shell=True):
        print(f"Failed to recreate virtual environment in {module_path}, skipping...")
        return False

    print(f"Recreated virtual environment in {module_path}")

    # the venv directory is created by the app_setup.py script
    venv_path = os.path.join(module_path, "venv")

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
    """Main function to deploy all stacks."""
    # control the execution time
    start_time = time.time()

    print("Starting deployment of all stacks...")

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
        print("No projects found to deploy")
        return

    print(f"Found {len(subdirs)} stacks to deploy:")
    for subdir in subdirs:
        print(f"  {subdir}")

    # Deploy each module
    success_count = 0
    new_line_str = "-" * 80
    print()  # a blank line before the first module
    for subdir in subdirs:
        module_path = os.path.join(base_dir, subdir)
        print(new_line_str)
        print(f"DEPLOYING STACK IN: {module_path}")
        print(new_line_str)
        try:
            if deploy_module(module_path):
                success_count += 1
        except Exception as e:
            print(f"Failed to deploy {module_path}: {e}")
            # skip to the next module
            continue

    # Print summary
    print(
        f"\nDeployment complete: {success_count}/{len(subdirs)}"
        " stacks deployed successfully"
    )

    # Print execution time
    print(f"\nTotal execution time: {time.time() - start_time:.2f} seconds")

    if success_count != len(subdirs):
        sys.exit(1)


if __name__ == "__main__":
    main()
