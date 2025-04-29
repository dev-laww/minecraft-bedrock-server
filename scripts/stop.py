import logging
import platform
import subprocess
import time

from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="%H:%M:%S",
    handlers=[RichHandler()]
)
logger = logging.getLogger('minecraft-monitor')


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
    stop_server()


if __name__ == "__main__":
    main()
