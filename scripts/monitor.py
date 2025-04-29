import logging
import os
import subprocess
import threading
import time
import platform

import readchar
from dotenv import load_dotenv
from mcstatus import BedrockServer
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel

load_dotenv()
SERVER_IP = os.getenv('SERVER_IP', '127.0.0.1')
SERVER_PORT = os.getenv('SERVER_PORT', '19132')
CHECK_INTERVAL = os.getenv('CHECK_INTERVAL', 1)
SERVER_TIMEOUT = os.getenv('SERVER_TIMEOUT', 60)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="%H:%M:%S",
    handlers=[RichHandler()]
)
logger = logging.getLogger('minecraft-monitor')
console = Console()

server = BedrockServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")


def listen_for_stop(stop_event: threading.Event):
    """
    Listen for the 'q' key to be pressed to trigger a manual stop.
    """
    while not stop_event.is_set():
        ch = readchar.readchar()

        if ch != 'q':
            continue

        logger.info("Manual shutdown requested.")
        stop_event.set()


def build_status_panel(online: int, maxp: int, latency: float, idle: int) -> Panel:
    """
    Build a Rich Panel with centered server status details.
    """
    content = (
        f"Server: {SERVER_IP}:{SERVER_PORT}\n"
        f"Players: {online}/{maxp}\n"
        f"Latency: {latency:.0f} ms\n"
        f"Idle Time: {idle} s"
    )
    return Panel(
        Align.center(content),
        title="[bold green]Minecraft Bedrock Monitor",
        expand=True
    )


def stop_server(shutdown: bool = True):
    logger.info("Stopping server...")
    subprocess.run(['docker', 'compose', 'stop'], check=True)

    logger.info("Waiting for server to stop...")
    while True:
        result = subprocess.run(
            ["docker", "container", "ps", "-q"],
            capture_output=True, text=True
        )
        if result.stdout.strip() == "":
            break
        time.sleep(1)

    logger.info("Server stopped.")

    if not shutdown:
        return

    logger.info("Shutting down the machine...")

    system = platform.system()

    if system == 'Windows':
        subprocess.run(['shutdown', '/s', '/t', '0'])
    elif system == 'Linux' or system == 'Darwin':
        subprocess.run(['shutdown', 'now'])
    else:
        logger.error(f"Unsupported OS: {system}")
        return


def main():
    time_since_last_player = 0

    stop_event = threading.Event()

    listener_thread = threading.Thread(target=listen_for_stop, args=(stop_event,), daemon=True)
    listener_thread.start()

    console.print(
        f"Monitoring Minecraft Bedrock server at [bold cyan]{SERVER_IP}:{SERVER_PORT}[/]",
        justify="center"
    )
    console.print(
        f"It will shutdown if empty for more than {SERVER_TIMEOUT} seconds, or when you press 'q'.",
        justify="center"
    )

    with Live(console=console, refresh_per_second=4) as live:
        while not stop_event.is_set():
            try:
                status = server.status()
            except Exception as e:
                logger.error(f"Failed to query server status: {e}")
                time.sleep(CHECK_INTERVAL)
                continue

            online = status.players.online
            maxp = status.players.max
            latency = status.latency

            live.update(build_status_panel(online, maxp, latency, time_since_last_player))

            if online == 0:
                time_since_last_player += CHECK_INTERVAL
            else:
                if time_since_last_player > 0:
                    logger.info("Player(s) joined, resetting idle timer.")
                time_since_last_player = 0

            if time_since_last_player >= SERVER_TIMEOUT:
                logger.warning("No players for too long, initiating shutdown...")
                stop_event.set()
                break

            time.sleep(CHECK_INTERVAL)

    stop_server()


if __name__ == "__main__":
    main()
