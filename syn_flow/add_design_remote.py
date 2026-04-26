#!/usr/bin/env python3
import paramiko
import sys
import json

def main(design_name, top_module, clock_name, clock_period=2.0):
    config = {
        'host': 'acf3030.ece.ust.hk',
        'username': 'xxx',
        'password': "24310725@Fwj",
    }

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=config['host'],
            username=config['username'],
            password=config['password']
        )
        print(f"Connected to {config['host']}")

        remote_config_path = "/home/xxx/Dr_RTL/syn_flow/design_all.json"

        # Read current config
        stdin, stdout, stderr = client.exec_command(f"cat {remote_config_path}")
        config_content = stdout.read().decode()
        stderr_out = stderr.read().decode()

        if stderr_out and "No such file" in stderr_out:
            # Create new config
            design_config = {}
        else:
            design_config = json.loads(config_content)

        # Add new design
        design_config[design_name] = {
            "top_module": top_module,
            "clock_name": clock_name,
            "clock_period": clock_period
        }

        # Write updated config
        new_config = json.dumps(design_config, indent=2)
        cmd = f"echo '{new_config}' > {remote_config_path}"
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.read()
        print(f"Added {design_name} to remote design config")

    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python add_design_remote.py <design_name> <top_module> <clock_name> [clock_period]")
        sys.exit(1)

    design_name = sys.argv[1]
    top_module = sys.argv[2]
    clock_name = sys.argv[3]
    clock_period = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0

    main(design_name, top_module, clock_name, clock_period)
