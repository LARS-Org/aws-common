def _install_requirements_recursively(directory_path, pip_requirements_file_list, do_log_func, run_cmd_func):
    """Install requirements recursively, starting with client project requirements."""
    import os
    
    # First, handle client project requirements
    client_root = os.path.abspath(os.getcwd())
    for req_file in pip_requirements_file_list:
        client_req_path = os.path.join(client_root, req_file)
        if os.path.exists(client_req_path):
            do_log_func(f"*** Installing client project's {req_file} (will be quiet)...")
            run_cmd_func(["pip", "install", "-r", client_req_path, "--quiet"])
    
    # Then proceed with recursive installation
    for root, dirs, files in os.walk(directory_path):
        for req_file in pip_requirements_file_list:
            req_path = os.path.join(root, req_file)
            if os.path.exists(req_path):
                do_log_func(f"*** Installing {req_file} from {root} (will be quiet)...")
                run_cmd_func(["pip", "install", "-r", req_path, "--quiet"])
