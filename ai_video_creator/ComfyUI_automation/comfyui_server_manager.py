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


class _ComfyUIServerManagerSingleton:
    """
    Singleton wrapper for ComfyUIServerManager to ensure only one instance is created.
    """

    _instance = None
    running = False

    @staticmethod
    def initialize(comfyui_command):
        """
        Initialize the singleton instance of ComfyUIServerManager.
        """
        if _ComfyUIServerManagerSingleton._instance is None:
            _ComfyUIServerManagerSingleton._instance = ComfyUIServerManager(
                comfyui_command
            )

    @staticmethod
    def get_instance():
        """
        Get the singleton instance of ComfyUIServerManager.
        """
        if _ComfyUIServerManagerSingleton._instance is None:
            raise ValueError(
                "ComfyUIServerManager is not initialized. Call initialize() first."
            )
        return _ComfyUIServerManagerSingleton._instance

    @staticmethod
    def start_comfyui(comfyui_command):
        """
        Start the ComfyUI server using the singleton instance.
        """
        _ComfyUIServerManagerSingleton.initialize(comfyui_command)
        instance = _ComfyUIServerManagerSingleton.get_instance()
        instance.start_comfyui()
        instance.start_monitoring()
        _ComfyUIServerManagerSingleton.running = True

    @staticmethod
    def shutdown_comfyui():
        """
        Stop the ComfyUI server and clean up the singleton instance.
        """
        if _ComfyUIServerManagerSingleton._instance is not None:
            _ComfyUIServerManagerSingleton._instance.shutdown()
            _ComfyUIServerManagerSingleton._instance = None
            _ComfyUIServerManagerSingleton.running = False


def start_comfyui(comfyui_command: str) -> None:
    """
    Start the ComfyUI application and monitor its heartbeat.
    """
    _ComfyUIServerManagerSingleton.start_comfyui(comfyui_command=comfyui_command)

    try:
        while _ComfyUIServerManagerSingleton.running:
            time.sleep(3)
    except KeyboardInterrupt:
        _ComfyUIServerManagerSingleton.shutdown_comfyui()
    except Exception:
        sys.exit(1)


def stop_comfyui() -> None:
    """
    Stop the ComfyUI application.
    """
    _ComfyUIServerManagerSingleton.shutdown_comfyui()


def cli() -> str:
    """
    Command-line interface for the ComfyUI manager.
    """
    parser = argparse.ArgumentParser(
        description="Manage the lifecycle of the ComfyUI application."
    )
    parser.add_argument(
        "--comfyui-path",
        type=str,
        default=os.getenv("COMFYUI_PATH"),
        help="ComfyUI path to the main.py file. Not including the file name.",
    )
    parser.add_argument(
        "--base-directory",
        type=str,
        help="ComfyUI models directory.",
    )
    parser.add_argument(
        "--output-directory",
        type=str,
        default="outputs",
        help="Stop the ComfyUI application if it is running.",
    )
    args = parser.parse_args()

    if args.comfyui_path is None:
        print(
            "use --comfyui-path option or set COMFYUI_PATH environment variable with ComfyUI path."
        )
        sys.exit(1)

    comfyui_command = f"python {args.comfyui_path}/main.py"

    if args.base_directory:
        if not os.path.exists(args.base_directory):
            print(f"Models directory {args.base_directory} does not exist.")
            sys.exit(1)
        comfyui_command += f" --base-directory {args.base_directory}"

    if args.output_directory:
        path = args.output_directory
        if not os.path.isabs(path):
            path = os.path.abspath(path)

        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        comfyui_command += f" --output-directory {path}"

    return comfyui_command


def main() -> None:
    """
    Main function to start the ComfyUI manager.
    """
    comfyui_command = cli()

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
        consecutive_failures = 0

        def restart_comfyui():
            print("Heartbeat check failed after 3 attempts. Restarting ComfyUI...")
            self.stop_comfyui()
            time.sleep(self.restart_delay)
            self.start_comfyui()

        while self.running:
            try:
                if self.requests.comfyui_get_heartbeat():
                    consecutive_failures = 0  # Reset on success
                else:
                    consecutive_failures += 1
                    print(f"Heartbeat failure {consecutive_failures}/3")

                if consecutive_failures >= 3:
                    restart_comfyui()
                    consecutive_failures = 0
                    self.restarts += 1

                    if self.restarts >= self.max_restarts:
                        print(
                            f"Max restarts reached: {self.max_restarts}. Stopping monitoring..."
                        )
                        break

            except Exception as e:
                print(f"Exception during heartbeat check: {e}")
                consecutive_failures += 1

            time.sleep(2)  # 1 second between checks

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
    main()
