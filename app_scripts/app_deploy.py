"""
Deployment script for the application.
"""


def do_deploy(do_log_func, run_cmd_func):
    """
    Deploy the application.
    """
    do_log_func("deploying...")
    # ensure the CDK is installed and deploy the stack
    run_cmd_func("npm install -g aws-cdk", shell=True)
    run_cmd_func("cdk bootstrap", shell=True)
    run_cmd_func("cdk deploy --require-approval never", shell=True)
    do_log_func("deployed!")
