#!/usr/bin/env python3

import time
import click
import importlib.util
import sys
from pathlib import Path
import logging
from rich.console import Console
from rich.theme import Theme
from rich.prompt import Prompt
from rich.panel import Panel
from rich.align import Align
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


def load_client_module(protocol):
    """Dynamically load the client module for the given protocol."""
    base_dir = Path(__file__).parent
    module_path = base_dir / f"{protocol}_client.py"

    if not module_path.exists():
        click.echo(f"❌ Error: {protocol}_client.py not found at {module_path}")
        sys.exit(1)

    try:
        spec = importlib.util.spec_from_file_location(f"{protocol}_client", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        click.echo(f"❌ Failed to load {protocol}_client: {e}")
        sys.exit(1)


@click.group()
@click.version_option()
def cli():
    """Agent CLI Chat Client — Interact with chat agents using multiple protocols."""
    pass


# Theme for general-purpose agent UX
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "agent": "green",
    "prompt": "magenta"
})
console = Console(theme=custom_theme)


@cli.command()
@click.option('--host', '-h', default=None, help='Host/IP of the A2A agent')
@click.option('--port', '-p', default=None, type=int, help='Port to connect to')
@click.option('--token', '-t', default=None, help='Authentication token')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def a2a(host, port, token, debug):
  """Run A2A protocol client."""


  if debug:
    logging.getLogger().setLevel(logging.DEBUG)

  # Read from environment if not provided
  env_host = os.environ.get("A2A_HOST", "localhost")
  env_port = os.environ.get("A2A_PORT", "8000")
  env_token = os.environ.get("A2A_TOKEN", "")

  # Enhanced popup prompt
  def popup_input(prompt_text, default=None, password=False):
    panel = Panel(
      Align.left(prompt_text, vertical="middle"),
      title="💬 Input Required",
      border_style="prompt",
      padding=(1, 2)
    )
    console.print(panel)
    return Prompt.ask("👉", default=default, password=password)

  def simple_prompt(label: str, default: str = None, password: bool = False) -> str:
    console.print(f"💬 [prompt]{label}[/prompt]", end="")
    return Prompt.ask("", default=default, password=password)

  # Intro panel
  console.print(Panel(
    Align.center("🔧 [agent]Welcome to A2A Client Setup[/agent]\nPlease provide connection details below.", vertical="middle"),
    title="🌐 Configuration",
    border_style="agent",
    padding=(1, 2)
  ))

  if not host:
    if env_host:
      host = env_host
    else:
      host = simple_prompt("[info]Enter host[/info]", default=None)

  if not port:
    if env_port:
      try:
        port = int(env_port)
      except ValueError:
        port = None
    if not port:
      port_input = simple_prompt("[info]Enter port[/info]", default=None)
      try:
        port = int(port_input)
      except (ValueError, TypeError):
        console.print("[error]❌ Invalid port. Please provide a valid port.[/error]")
        sys.exit(1)

  if token is None:
    if env_token:
      token = env_token
    else:
      console.print("[warning]⚠️ Token not provided. Connecting without authentication.[/warning]. You can provide it using the --token option or set A2A_TOKEN env variable.")
      time.sleep(1)

  console.print("🚀 [info]Launching A2A client...[/info]")
  if "A2A_HOST" not in os.environ:
    os.environ["A2A_HOST"] = str(host)
  if "A2A_PORT" not in os.environ:
    os.environ["A2A_PORT"] = str(port)

  if os.environ.get("A2A_TLS", "false").lower() in ["true", "1", "yes"]:
    tls = True
  else:
    tls = False
    
  client_module = load_client_module("a2a")
  client_module.main(host=host, port=port, token=token, tls=tls)


@cli.command()
@click.option('--endpoint', '-e', default=None, help='SLIM transport endpoint (e.g., 127.0.0.1:46357)')
@click.option('--remote-card', '-c', default=None, help='Remote agent card (URL, JSON string, or file path)')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def slim(endpoint, remote_card, debug):
    """Run SLIM protocol client."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("agent_chat_cli").setLevel(logging.DEBUG)
        logging.getLogger("agent_chat_cli.slim_client").setLevel(logging.DEBUG)
        logging.getLogger("agntcy_app_sdk").setLevel(logging.DEBUG)

    env_endpoint = os.environ.get("SLIM_ENDPOINT")
    env_remote_card = os.environ.get("SLIM_REMOTE_CARD")

    def simple_prompt(label: str, default: str = None, password: bool = False) -> str:
        console.print(f"💬 [prompt]{label}[/prompt]", end="")
        return Prompt.ask("", default=default, password=password)

    if not endpoint:
        endpoint = env_endpoint or simple_prompt("[info]Enter SLIM endpoint (host:port)[/info]")

    if not remote_card:
        remote_card = env_remote_card or simple_prompt("[info]Enter remote Agent Card (URL or JSON or file path)[/info]")

    # Ensure endpoint always contains scheme for SLIM transport
    if endpoint and not endpoint.startswith(("http://", "https://")):
        endpoint = f"http://{endpoint}"

    console.print("🚀 [info]Launching SLIM client...[/info]")
    client_module = load_client_module("slim")
    client_module.main(endpoint=endpoint, remote_card=remote_card, debug=debug)


if __name__ == '__main__':
    # Choose default subcommand from env when none is provided
    default_mode = os.environ.get("AGENT_CHAT_PROTOCOL", "").strip().lower() or "a2a"
    if len(sys.argv) == 1:
        if default_mode not in ("a2a", "slim"):
            default_mode = "a2a"
        sys.argv.insert(1, default_mode)
    cli()
