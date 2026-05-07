#!/usr/bin/env python3
import paramiko
from scp import SCPClient
import time
import os, json
import sys

class RemoteSynthesisRunner:
    def __init__(self, host, username, password=None, key_file=None, proxy_host=None, proxy_port=None):
        """
        Initialize SSH connection to remote server
        
        Args:
            host: Remote server hostname
            username: SSH username
            password: SSH password (if using password auth)
            key_file: Path to SSH private key (if using key auth)
        """
        self.host = host
        self.username = username
        self.password = password
        self.key_file = key_file
        self.client = None
        
    def connect(self):
        """Establish SSH connection"""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        
        # Connect
        connect_kwargs = {
            'hostname': self.host,
            'username': self.username,
        }
        
        if self.key_file:
            connect_kwargs['key_filename'] = self.key_file
        elif self.password:
            connect_kwargs['password'] = self.password
        
        self.client.connect(**connect_kwargs)
        print(f"✓ Connected to {self.host}")
        
    def upload_files(self, local_path, remote_path):
        """
        Upload files to remote server
        
        Args:
            local_path: Local file or directory path
            remote_path: Remote destination path
        """
        print(f"Uploading {local_path} to {remote_path}...")
        
        with SCPClient(self.client.get_transport()) as scp:
            if os.path.isdir(local_path):
                scp.put(local_path, remote_path, recursive=True)
            else:
                scp.put(local_path, remote_path)
        
        print(f"✓ Upload complete")
        
    def run_remote_script(self, script_dir, script_path, args="", timeout=1800):
        """
        Run a Python script on remote server
        
        Args:
            script_path: Path to remote Python script
            args: Command-line arguments for the script
            timeout: Maximum time to wait (seconds)
            
        Returns:
            tuple: (return_code, stdout, stderr)
        """
        command = f"bash -c 'source ~/.bashrc && cd {script_dir} && python3 {script_path} {args}'"
        print(f"Running: {command}")
        
        stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
        
        # Stream output in real-time
        for line in iter(stdout.readline, ""):
            print(f"  {line.rstrip()}")
        
        return_code = stdout.channel.recv_exit_status()
        stderr_output = stderr.read().decode()
        
        if stderr_output:
            print(f"Stderr: {stderr_output}")
        
        return return_code, stderr_output
        
    def download_files(self, remote_path, local_path):
        """
        Download files from remote server
        
        Args:
            remote_path: Remote file or directory path
            local_path: Local destination path
        """
        print(f"Downloading {remote_path} to {local_path}...")
        
        # Create local directory if needed
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with SCPClient(self.client.get_transport()) as scp:
            scp.get(remote_path, local_path, recursive=True)
        
        print(f"✓ Download complete")
        
    def close(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
            print("✓ Connection closed")


def main(design_name, design_version):
    # Configuration
    config = {
        'host': 'xxx',
        'username': 'xxx',
        # 'key_file': os.path.expanduser('~/.ssh/id_rsa'),  # or use password
        'password': "xxx",  # Use with caution; consider using key_file instead
        'proxy_host': 'xxx',
        'proxy_port': 'xxx',
    }
    with open ("design_all.json", "r") as f:
        design_all = json.load(f)
    design_tpe = design_all[design_name][3]
    
    design = f"{design_name}.{design_version}"
    local_rtl_dir = f"./rtl/{design_name}.{design_version}.{design_tpe}"
    remote_work_dir = f"/home/xxx/Dr_RTL/syn_flow"
    remote_rtl_dir = f"{remote_work_dir}/rtl/"
    remote_script = f"{remote_work_dir}/run_design.py"
    
    
    # Initialize runner
    runner = RemoteSynthesisRunner(**config)
    
    try:
        # Step 1: Connect
        print("---- Start ----")
        runner.connect()
        
        # Step 2: Upload RTL files and design config
        runner.upload_files(local_rtl_dir, remote_rtl_dir)
        runner.upload_files("./design_all.json", f"{remote_work_dir}/design_all.json")

        # Step 3: Run remote synthesis script
        return_code, stderr = runner.run_remote_script(
            script_dir=remote_work_dir,
            script_path=remote_script,
            args=f"{design_name} {design_version}",
            timeout=3600  # 1 hour timeout
        )
        
        if return_code != 0:
            print(f"✗ Script failed with return code {return_code}")
            sys.exit(1)
        
        print(f"✓ Script completed successfully")
        
        # Step 4: Download results
        remote_results = f"{remote_work_dir}/output/{design}"
        local_results_dir = "./output"
        runner.download_files(remote_results, local_results_dir)
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    
    finally:
        # Step 6: Cleanup
        runner.close()



def print_usage():
    print("""Usage: python run_design.py <design_name> <design_version>
    Examples:
    python run_design.py tv80 v0           # Full flow
    """)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    design_name = sys.argv[1]
    design_version = sys.argv[2]
    main(design_name, design_version)
