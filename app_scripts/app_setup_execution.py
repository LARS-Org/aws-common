"""
This script is used to automate the setup of the Python virtual environment, 
installation of Python requirements, and the application's deploy.
"""
import os
import sys
import importlib.util
from app_test import do_run_tests
from app_reset_venv import do_reset_venv
from app_install_reqs import do_install_req

# Set of possible menu options considering the synonyms
MENU_VENV_OPTIONS = {
    "--setup_venv",
    "--setup",
    "--reset_venv",
    "setup_venv",
    "setup",
    "reset_venv",
}
MENU_INSTALL_OPTIONS = {
    "--install_requirements",
    "--install",
    "--install_reqs",
    "install_requirements",
    "install",
    "install_reqs",
}
MENU_DEPLOY_OPTIONS = {
    "--deploy",
    "--deploy_stack",
    "--deploy_cdk",
    "--deploy_app",
    "deploy",
    "deploy_stack",
    "deploy_cdk",
    "deploy_app",
}
MENU_FAST_DEPLOY_OPTIONS = {"fast_deploy", "--fast_deploy"}
MENU_HELP_OPTIONS = {"--help", "-h", "help"}
MENU_TEST_OPTIONS = {"run_tests", "--run_tests", "test", "--test", "tests", "--tests"}
MENU_OPTIONS = (
    MENU_VENV_OPTIONS
    | MENU_INSTALL_OPTIONS
    | MENU_DEPLOY_OPTIONS
    | MENU_FAST_DEPLOY_OPTIONS
    | MENU_HELP_OPTIONS
    | MENU_TEST_OPTIONS
)

# getting the project root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, "..")

# finding the common directory
common_dir = os.path.join(root_dir, "app_common")

# Construct the path to the utils module
utils_script_path = os.path.join(common_dir, "app_utils.py")

# Load the module dynamically
# It is necessary to add the module to the sys.modules dictionary
# to avoid ModuleNotFoundError when importing it from the caller script.
spec = importlib.util.spec_from_file_location("app_utils_module", utils_script_path)
_UTILS_MODULE = importlib.util.module_from_spec(spec)
sys.modules["app_utils_module"] = _UTILS_MODULE
spec.loader.exec_module(_UTILS_MODULE)

def _do_log(obj, title=None, log_limit: int = 150):
    """
    Wrapper function to call the do_log function from the app_utils module.
    """
    _UTILS_MODULE.do_log(obj, title=title, log_limit=log_limit)


def _run_command(command, cwd=None, shell=False):
    """
    Wrapper function to call the run_command function from the app_utils module.
    """
    _UTILS_MODULE.run_command(command, cwd=cwd, shell=shell)

def deploy(execution_dir: str, script_dir: str):
    """
    Placeholder for the deploy functionality.
    :param execution_dir: The directory to execute the script in.
    :param script_dir: The directory containing the `app_install_reqs.py` script.
    """
    script_path = os.path.join(script_dir, "app_deploy.py")
    _do_log("*** Calling app_deploy.py script...")
    _run_command(f"python3.11 {script_path}", cwd=execution_dir, shell=True)
    _do_log("*** App Deploy is done!")
    
def main():
    """
    Main function to parse command-line arguments and call the appropriate function.
    """
    error_msg_args = "Usage: la_setup.py --<setup_venv|install_requirements|deploy|run_tests>"
    if len(sys.argv) != 4:
        _do_log(error_msg_args)
        sys.exit(1)

    action = sys.argv[1]
    # Get the current script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the caller script directory
    caller_dir = sys.argv[-1]

    # Map action to corresponding function
    if action in MENU_VENV_OPTIONS:
        do_reset_venv(_do_log, _run_command)
        # it will be commented while we don't solve the issue with the venv activation
        # install_requirements(execution_dir=caller_dir, script_dir=current_dir)
    elif action in MENU_INSTALL_OPTIONS:
        do_install_req(_do_log, _run_command)
    elif action in MENU_DEPLOY_OPTIONS:
        do_install_req(_do_log, _run_command)
        deploy(execution_dir=caller_dir, script_dir=current_dir)
    elif action in MENU_FAST_DEPLOY_OPTIONS:
        deploy(execution_dir=caller_dir, script_dir=current_dir)
    elif action in MENU_TEST_OPTIONS:
        do_run_tests(_do_log, _run_command)
    elif action in MENU_HELP_OPTIONS:
        _do_log(
            "Automate the setup of the Python virtual environment, installation of Python requirements, and the application's deploy."
        )
        _do_log(
            "Usage: python3.11 la_setup.py --<setup_venv|install_requirements|deploy>"
        )
        _do_log("Examples:")
        _do_log("python3.11 la_setup.py --setup_venv")
        _do_log("python3.11 la_setup.py --install_requirements")
        _do_log("python3.11 la_setup.py --deploy")
    else:
        _do_log(f"Unknown action: {action}")
        _do_log(error_msg_args)
        sys.exit(1)


if __name__ == "__main__":
    main()
