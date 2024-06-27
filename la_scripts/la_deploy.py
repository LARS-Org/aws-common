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


print("deploying...")
# ensure the CDK is installed and deploy the stack
_run_command("npm install -g aws-cdk", shell=True)
_run_command("cdk bootstrap", shell=True)
_run_command("cdk deploy", shell=True)
print("deployed!")