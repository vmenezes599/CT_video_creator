"""
ComfyUI Manager manages the lifecycle of the ComfyUI application.
"""

import argparse
import subprocess
import time
import os
import sys
from threading import Thread

from .comfyui_requests import ComfyUIRequests


def start_comfyui(comfyui_command: str) -> None:
    """
    Start the ComfyUI application and monitor its heartbeat.
    """
    manager = ComfyUIServerManager(comfyui_command)
    manager.start_comfyui()
    manager.start_monitoring()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.shutdown()


def main(*kargs) -> None:
    """
    Main function to start the ComfyUI manager.
    """
    parser = argparse.ArgumentParser(
        description="Manage the lifecycle of the ComfyUI application."
    )
    default_comfyui_path = ""
    parser.add_argument(
        "--comfyui-path",
        type=str,
        default=default_comfyui_path,
        help="ComfyUI path to the main.py file. Not including the file name.",
    )
    parser.add_argument(
        "--models-directory",
        type=str,
        default="models",
        help="ComfyUI models directory.",
    )
    parser.add_argument(
        "--output-directory",
        type=str,
        default="outputs",
        help="Stop the ComfyUI application if it is running.",
    )
    args = parser.parse_args(kargs)

    if args.comfyui_path == default_comfyui_path:
        comfyui_path = os.getenv("COMFYUI_PATH")
        if not comfyui_path:
            print(
                "use --comfyui-path option or set COMFYUI_PATH environment variable with ComfyUI path."
            )
            sys.exit(1)

    comfyui_command = f"python {args.comfyui_path}/main.py"

    if args.models_directory:
        if not os.path.exists(args.models_directory):
            print(f"Models directory {args.models_directory} does not exist.")
            sys.exit(1)
        comfyui_command += f" --models-directory {args.models_directory}"

    if args.output_directory:
        path = args.output_directory
        if not os.path.isabs(path):
            path = os.path.abspath(path)

        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        comfyui_command += f" --output-directory {path}"

    start_comfyui(comfyui_command)


class ComfyUIServerManager:
    """
    A manager class to handle the lifecycle of the ComfyUI application.
    It monitors the application's heartbeat and restarts it if it crashes.
    """

    def __init__(
        self,
        comfyui_command,
        max_restarts: int = 10,
        check_interval: int = 10,
        restart_delay: int = 5,
    ):
        """
        Initialize the ComfyUIManager.

        :param comfyui_command: Command to start the ComfyUI application.
        :param heartbeat_url: URL to check the application's heartbeat.
        :param check_interval: Interval (in seconds) to check the heartbeat.
        :param restart_delay: Delay (in seconds) before restarting the application.
        """
        self.comfyui_command = comfyui_command
        self.max_restarts = max_restarts
        self.restarts = -1
        self.check_interval = check_interval
        self.restart_delay = restart_delay
        self.process = None
        self.running = False

        self.requests = ComfyUIRequests()

    def start_comfyui(self):
        """Start the ComfyUI application."""
        print("Starting ComfyUI...")
        self.process = subprocess.Popen(self.comfyui_command, shell=True)

        while True:
            try:
                heartbeat = self.requests.comfyui_get_heartbeat()
                if heartbeat:
                    break
            except Exception:
                # print(f"ComfyUI initializing...")
                pass

            time.sleep(5)

        self.restarts += 1
        print("ComfyUI started...")
        self.running = True

    def stop_comfyui(self):
        """Stop the ComfyUI application."""
        if self.process:
            print("Stopping ComfyUI...")
            self.process.terminate()
            self.process.wait()
            self.process = None
        self.running = False

    def crash_comfyui(self):
        """Simulate a crash of the ComfyUI application."""
        if self.process:
            print("Stopping ComfyUI...")
            self.process.terminate()
            self.process.wait()
            self.process = None

    def monitor_heartbeat(self):
        """Monitor the heartbeat of the ComfyUI application and restart if necessary."""
        failed = False

        def restart_comfyui():
            print("Heartbeat check failed. Restarting ComfyUI...")
            self.stop_comfyui()
            time.sleep(self.restart_delay)
            self.start_comfyui()

        while self.running:
            try:
                if not self.requests.comfyui_get_heartbeat():
                    restart_comfyui()
                if self.restarts >= self.max_restarts:
                    print(
                        f"Max restarts reached: {self.max_restarts}. Stopping monitoring..."
                    )
                    break
            except Exception:
                if not failed:
                    failed = True
                    time.sleep(self.restart_delay * 6)
                else:
                    failed = False
                    restart_comfyui()

            time.sleep(self.check_interval)

    def start_monitoring(self):
        """Start monitoring the ComfyUI application in a separate thread."""
        print("Starting heartbeat monitoring...")
        monitoring_thread = Thread(target=self.monitor_heartbeat, daemon=True)
        monitoring_thread.start()

    def shutdown(self):
        """Shutdown the manager and stop the ComfyUI application."""
        print("Shutting down ComfyUIManager...")
        self.stop_comfyui()


# Example usage
if __name__ == "__main__":
    main(*sys.argv[1:])
