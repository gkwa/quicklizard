#!/usr/bin/env python3
"""
Ringgem setup script - Python replacement for shell commands
Requires Python 3.12+ (uses urllib.request instead of requests)
"""

import argparse
import logging
import os
import pathlib
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile


def setup_logging(verbosity):
    """Setup logging based on verbosity level."""
    levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    level = levels[min(verbosity, len(levels) - 1)]

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )


def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return the result."""
    logging.debug(f"Running command: {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, check=check, capture_output=True, text=True
        )
        if result.stdout:
            logging.info(result.stdout.strip())
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {cmd}")
        logging.error(f"Exit code: {e.returncode}")
        logging.error(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e


def download_file(url, destination):
    """Download a file from URL to destination."""
    try:
        logging.info(f"Downloading {url}")
        urllib.request.urlretrieve(url, destination)
        logging.debug(f"Successfully downloaded {destination}")
    except urllib.error.URLError as e:
        logging.error(f"Failed to download {url}: {e}")
        sys.exit(1)


def download_and_execute_script(url, script_name):
    """Download and execute a shell script."""
    try:
        logging.info(f"Downloading and executing {script_name}")
        with urllib.request.urlopen(url) as response:
            script_content = response.read().decode("utf-8")

        # Write to temporary file and execute
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as tmp:
            tmp.write(script_content)
            tmp_path = tmp.name

        os.chmod(tmp_path, 0o755)
        run_command(f"bash {tmp_path}")
        os.unlink(tmp_path)

    except urllib.error.URLError as e:
        logging.error(f"Failed to download {url}: {e}")
        sys.exit(1)


def main():
    """Main setup function."""
    logging.info("Starting Ringgem setup")

    # Change to /tmp directory
    tmp_dir = pathlib.Path("/tmp")
    os.chdir(tmp_dir)
    logging.debug(f"Working in: {tmp_dir}")

    # URLs
    urls = {
        "go_task_installer": "https://raw.githubusercontent.com/taylormonacelli/ringgem/master/install-go-task-on-linux.sh",
        "ringgem_zip": "https://github.com/taylormonacelli/ringgem/archive/refs/heads/master.zip",
        "zip_installer": "https://raw.githubusercontent.com/gkwa/ringgem/refs/heads/master/install-zip-on-linux.sh",
        "taskfile": "https://raw.githubusercontent.com/gkwa/ringgem/refs/heads/master/Taskfile.yaml",
    }

    # Step 1: Download and execute go-task installer
    logging.info("Installing go-task")
    download_and_execute_script(
        urls["go_task_installer"], "install-go-task-on-linux.sh"
    )

    # Step 2: Download ringgem.zip
    logging.info("Downloading ringgem.zip")
    download_file(urls["ringgem_zip"], "ringgem.zip")

    # Step 3: Download zip installer script
    logging.info("Downloading zip installer")
    download_file(urls["zip_installer"], "install-zip-on-linux.sh")

    # Step 4: Download Taskfile.yaml
    logging.info("Downloading Taskfile.yaml")
    download_file(urls["taskfile"], "Taskfile.yaml")

    # Step 5: Install zip using task
    logging.info("Installing zip")
    run_command("task install-zip-on-linux")

    # Step 6: Create ringgem directory and extract
    logging.info("Setting up ringgem directory")
    ringgem_dir = pathlib.Path.home() / ".local/share/ringgem"
    ringgem_dir.mkdir(parents=True, exist_ok=True)

    # Extract zip file
    logging.debug(f"Extracting ringgem.zip to {ringgem_dir}")
    with zipfile.ZipFile("ringgem.zip", "r") as zip_ref:
        zip_ref.extractall(ringgem_dir)

    # Step 7: List available tasks
    logging.info("Listing available tasks")
    ringgem_master_dir = ringgem_dir / "ringgem-master"
    run_command(f"task --dir={ringgem_master_dir} --list-all")

    # Step 8: Install testscript
    logging.info("Installing testscript")
    run_command(f"task --dir={ringgem_master_dir} install-testscript-on-linux")

    logging.info("Setup complete")
    logging.info(f"Ringgem installed in: {ringgem_dir}")
    logging.info(f"To use tasks, run: task --dir={ringgem_master_dir} <task-name>")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ringgem setup script")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (use -v, -vv, -vvv for more detail)",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Check Python version
    if sys.version_info < (3, 12):
        logging.error("This script requires Python 3.12 or higher")
        sys.exit(1)

    try:
        main()
    except KeyboardInterrupt:
        logging.warning("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)
