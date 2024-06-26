from la_common.la_utils import run_command

print("deploying...")
# ensure the CDK is installed and deploy the stack
run_command("npm install -g aws-cdk", shell=True)
run_command("cdk bootstrap", shell=True)
run_command("cdk deploy", shell=True)
print("deployed!")