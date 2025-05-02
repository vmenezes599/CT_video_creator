"""
ComfyUI Manager manages the lifecycle of the ComfyUI application.
"""

import subprocess
import time
from threading import Thread

import requests

from .environment_variables import CONFYUI_URL

COMFYUI_COMMAND = "python lib/ComfyUI/main.py"
HEARTBEAT_URL = CONFYUI_URL + "/prompt"

def main() -> None:
    """
    Main function to start the ComfyUI manager.
    """

    manager = ComfyUIManager(COMFYUI_COMMAND, HEARTBEAT_URL)
    manager.start_comfyui()
    manager.start_monitoring()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.shutdown()

class ComfyUIManager:
    """
    A manager class to handle the lifecycle of the ComfyUI application.
    It monitors the application's heartbeat and restarts it if it crashes.
    """

    def __init__(
        self,
        comfyui_command,
        heartbeat_url,
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
        self.heartbeat_url = heartbeat_url
        self.max_restarts = max_restarts
        self.restarts = -1
        self.check_interval = check_interval
        self.restart_delay = restart_delay
        self.process = None
        self.running = False

    def start_comfyui(self):
        """Start the ComfyUI application."""
        print("Starting ComfyUI...")
        self.process = subprocess.Popen(self.comfyui_command, shell=True)

        while self.check_heartbeat() is False:
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

    def check_heartbeat(self):
        """Check the heartbeat of the ComfyUI application."""
        try:
            response = requests.get(self.heartbeat_url, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def monitor_heartbeat(self):
        """Monitor the heartbeat of the ComfyUI application and restart if necessary."""
        while self.running:
            if not self.check_heartbeat():
                print("Heartbeat check failed. Restarting ComfyUI...")
                self.stop_comfyui()
                time.sleep(self.restart_delay)
                self.start_comfyui()
            if self.restarts >= self.max_restarts:
                print(f"Max restarts reached: {self.max_restarts}. Stopping monitoring...")
                break
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
    main()
