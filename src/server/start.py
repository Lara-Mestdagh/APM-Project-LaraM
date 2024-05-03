import os
import subprocess
import sys
import gui_server

def install_packages():
    try:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        requirements_path = os.path.join(script_dir, "requirements.txt")
        with open(requirements_path, "r") as f:
            packages = f.read().splitlines()
            for package in packages:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except Exception as e:
        print(f"Error installing packages: {e}")

def run_server():
    print("requirements installed, running server...")
    gui_server.main()

if __name__ == "__main__":
    install_packages()
    run_server()