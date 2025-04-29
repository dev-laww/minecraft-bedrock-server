import argparse
import logging
import os
import socket
import subprocess
import threading
import time
from collections import deque

import readchar
from dotenv import load_dotenv
from mcstatus import BedrockServer
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel

from stop import stop_server
from utils import convert_to_seconds

load_dotenv()
SERVER_IP = os.getenv('SERVER_IP', '127.0.0.1')
SERVER_PORT = os.getenv('SERVER_PORT', '19132')
CHECK_INTERVAL = convert_to_seconds(os.getenv('CHECK_INTERVAL', '5s'))
timeout = os.getenv('SERVER_TIMEOUT', 'off')
SERVER_TIMEOUT = convert_to_seconds(timeout) if timeout != 'off' else 0

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    datefmt='%H:%M:%S',
    handlers=[RichHandler()]
)
logger = logging.getLogger('minecraft-monitor')
console = Console()

server = BedrockServer.lookup(f'{SERVER_IP}:{SERVER_PORT}')


def listen_for_stop(stop_event: threading.Event):
    while not stop_event.is_set():
        ch = readchar.readchar()
        if ch == 'q':
            logger.info('Manual shutdown requested.')
            stop_event.set()


def stream_compose_logs(logs_buffer: deque, stop_event: threading.Event):
    cmd = ['docker', 'compose', 'logs', '--no-color', '-f', 'bds']
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    for line in proc.stdout:
        logs_buffer.append(line.rstrip('\n').replace('bds  | ', ''))
        if stop_event.is_set():
            proc.terminate()
            break


def build_status_panel(online: int, maxp: int, latency: float, idle: int) -> Panel:
    content = (
        f'Players     : {online}/{maxp}\n'
        f'Latency     : {latency:.0f} ms\n'
        f'Idle Time   : {idle} s\n'
        f'Time Checked: {time.strftime("%m-%d-%Y %H:%M:%S", time.localtime())}'
    )
    return Panel(
        Align.center(content),
        title='[bold green]Server Status[/]',
        expand=True
    )


def build_logs_panel(logs: deque) -> Panel:
    available_space = console.size.height - 11
    tail = list(logs)[-available_space:]
    content = '\n'.join(tail)
    return Panel(
        Align.left(content),
        title='[bold green]Server Logs[/]',
        expand=True
    )


def main():
    parser = argparse.ArgumentParser(description='Monitor a Minecraft Bedrock server.')
    parser.add_argument(
        '--automatic-shutdown', action='store_true',
        help='Enable automatic shutdown if server is empty.'
    )
    args = parser.parse_args()
    do_shutdown = args.automatic_shutdown

    stop_event = threading.Event()
    time_since_last_player = 0

    listener_thread = threading.Thread(target=listen_for_stop, args=(stop_event,), daemon=True)
    listener_thread.start()

    local_network_ip = socket.gethostbyname(socket.gethostname())

    logs = deque(maxlen=70)
    log_thread = threading.Thread(
        target=stream_compose_logs,
        args=(logs, stop_event),
        daemon=True
    )
    log_thread.start()

    text = [
        Align.center(f'Monitoring Minecraft Bedrock server at [bold cyan]{SERVER_IP}:{SERVER_PORT}[/]'),
        Align.center(f'It will shutdown if empty for more than {timeout}, or when you press \'q\'.'),
        Align.center(f'Local Network Address: [bold yellow]{local_network_ip}:{SERVER_PORT}[/]'),
    ]

    layout = Layout()
    layout.split_column(
        Layout(Group(*text), name='header', size=3),
        Layout(name='status', size=6),
        Layout(name='logs'),
    )

    layout['status'].update(Panel(Align.center(
        'Loading...',
        style='yellow',
        vertical='middle'),
        title='[bold green]Server Status[/]')
    )
    layout['logs'].update(build_logs_panel(logs))

    with Live(layout, console=console, refresh_per_second=4):
        while not stop_event.is_set():
            layout['logs'].update(build_logs_panel(logs))
            try:
                status = server.status()
            except Exception:
                layout.update(Align.center('Server is offline', style='red'))
                time.sleep(CHECK_INTERVAL)
                continue

            online = status.players.online
            maxp = status.players.max
            latency = status.latency

            layout['status'].update(build_status_panel(online, maxp, latency, time_since_last_player))

            if online == 0:
                time_since_last_player += CHECK_INTERVAL
            else:
                time_since_last_player = 0

            if time_since_last_player >= SERVER_TIMEOUT > 0:
                logger.warning('No players for too long, initiating shutdown...')
                stop_event.set()
                break

            time.sleep(CHECK_INTERVAL)

    stop_server(do_shutdown)


if __name__ == '__main__':
    main()
