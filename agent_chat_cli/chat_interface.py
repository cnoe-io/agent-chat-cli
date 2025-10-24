# SPDX-License-Identifier: Apache-2.0

import asyncio
import itertools
import os
import re
import readline
import platform
import signal
import sys
from typing import Callable, Awaitable

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme

# Theme for general-purpose agent
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "agent": "green"
})

console = Console(theme=custom_theme)

# Event to signal that streaming has started (set by protocol client)
_stream_start_event: asyncio.Event | None = None
_spinner_cleared_event: asyncio.Event | None = None

async def wait_spinner_cleared():
    global _spinner_cleared_event
    if _spinner_cleared_event is not None:
        await _spinner_cleared_event.wait()

def notify_streaming_started():
    global _stream_start_event
    if _stream_start_event is not None:
        _stream_start_event.set()

async def spinner(msg: str = "⏳ Waiting for agent...", stop_event: asyncio.Event | None = None, cleared_event: asyncio.Event | None = None):
    for frame in itertools.cycle(['|', '/', '-', '\\']):
        if stop_event is not None and stop_event.is_set():
            # Replace spinner char with an arrow on the same line
            try:
                sys.stdout.write(f"\r{msg} →")
                sys.stdout.flush()
            except Exception:
                pass
            if cleared_event is not None:
                cleared_event.set()
            break
        print(f"\r{msg} {frame}", end='', flush=True)
        await asyncio.sleep(0.1)

def render_answer(answer: str, agent_name: str = "Agent"):
    answer = answer.strip()
    if re.match(r"^b?[\"']?\{.*\}['\"]?$", answer):
        console.print("[warning]⚠️  Skipping raw byte/dict output.[/warning]")
        return

    console.print("\n")
    console.print(Panel(
        Markdown(answer),
        title=f"[agent]{agent_name} Response[/agent]",
        border_style="agent",
        padding=(1, 2)
    ))
    console.print("\n")

def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def print_welcome_message(agent_name: str, skills_description: str = "", skills_examples: str = ""):
  welcome_text = (
    f"[agent]🚀 Welcome to {agent_name} CLI[/agent]\n\n"
    "This agent helps you interact with tools dynamically.\n"
    "Type your question and hit enter.\n"
    "Type 'exit' or 'quit' to leave. Type 'clear' to clear the screen. Type 'history' to view chat history."
  )
  if skills_description:
    welcome_text += f"\n\n[info]Skills Description:[/info]\n{skills_description}"
  if skills_examples:
    # skills_examples is already a list
    bullets = "\n".join(f"- {ex}" for ex in skills_examples)
    welcome_text += f"\n\n[info]Example Skills:[/info]\n{bullets}"

  console.print(Panel(
    welcome_text,
    title=f"[agent]{agent_name}[/agent]",
    border_style="agent",
    padding=(1, 2)
  ))
  console.print("\n")

async def run_chat_loop(handle_user_input: Callable[[str], Awaitable[None]],
                        agent_name: str = "Agent",
                        skills_description: str = "",
                        skills_examples: str = "",
                        history_key: str = "agent"):
    print_welcome_message(agent_name, skills_description, skills_examples)
    history_file = os.path.expanduser(f"~/.{history_key}_chat_history")

    try:
        if os.path.exists(history_file):
            readline.read_history_file(history_file)
    except Exception as e:
        console.print(f"[warning]⚠️  Could not load history file: {e}[/warning]")

    # Signal handler for graceful exit
    def signal_handler(signum, frame):
        if signum == signal.SIGTSTP:
            # Save history before suspending
            try:
                readline.write_history_file(history_file)
            except Exception:
                pass
            console.print(f"\n[agent]🛑 {agent_name} suspended. Use 'fg' to resume.[/agent]")
            # Restore default handler and re-raise signal to actually suspend
            signal.signal(signal.SIGTSTP, signal.SIG_DFL)
            os.kill(os.getpid(), signal.SIGTSTP)
        elif signum == signal.SIGQUIT:
            console.print(f"\n[agent]👋 {agent_name} terminated. Goodbye![/agent]")
            # Save history before exiting
            try:
                readline.write_history_file(history_file)
            except Exception:
                pass
            sys.exit(0)
        elif signum == signal.SIGCONT:
            # Re-register SIGTSTP handler after resuming from suspension
            signal.signal(signal.SIGTSTP, signal_handler)
            console.print(f"[agent]▶️  {agent_name} resumed.[/agent]")
    
    # Register signal handlers  
    if platform.system() != "Windows":  # Signal handling works differently on Windows
        signal.signal(signal.SIGQUIT, signal_handler)  # Control+\ (quit)
        signal.signal(signal.SIGTSTP, signal_handler)  # Control+Z (suspend)
        signal.signal(signal.SIGCONT, signal_handler)  # Resume after suspension

    try:
        while True:
            try:
                user_input = input("💬 You: ").strip()
                if user_input.lower() in ["exit", "quit"]:
                    console.print(f"\n[agent]👋 Thank you for using {agent_name}. Goodbye![/agent]")
                    break
                elif user_input.lower() == "clear":
                    clear_screen()
                    print_welcome_message(agent_name)
                    continue
                elif user_input.lower() == "history":
                    console.print("\n[agent]📜 Chat History (last 100 entries):[/agent]")
                    history = [readline.get_history_item(i) for i in range(1, readline.get_current_history_length() + 1)]
                    for idx, entry in enumerate(history[-100:], 1):
                        console.print(f"{idx}: {entry}")
                    console.print()
                    continue
                if user_input:
                    readline.add_history(user_input)
                    stop_event = asyncio.Event()
                    spinner_cleared_event = asyncio.Event()
                    global _stream_start_event, _spinner_cleared_event
                    _stream_start_event = stop_event
                    _spinner_cleared_event = spinner_cleared_event
                    spinner_task = asyncio.create_task(spinner(stop_event=stop_event, cleared_event=spinner_cleared_event))
                    try:
                        await handle_user_input(user_input)
                    except Exception as e:
                        console.print(f"[error]⚠️  An error occurred: {e}[/error]")
                    finally:
                        stop_event.set()
                        spinner_task.cancel()
                        try:
                            await spinner_task
                        except asyncio.CancelledError:
                            pass
                        finally:
                            _stream_start_event = None
                            _spinner_cleared_event = None
            except (KeyboardInterrupt, EOFError):
                # KeyboardInterrupt: Control+C, EOFError: Control+D
                console.print("\n[agent]👋 Chat interrupted. Goodbye![/agent]")
                break
    finally:
        try:
            readline.write_history_file(history_file)
        except Exception as e:
            console.print(f"[warning]⚠️  Could not save history file: {e}[/warning]")

async def main():
    if len(sys.argv) < 2:
        console.print("[error]Please provide the agent name or base URL as an argument.[/error]")
        console.print("Example: python chat_interface.py MyAgent")
        sys.exit(1)

    agent_name_or_url = sys.argv[1]

    # Example placeholder — inject your agent or A2A client logic here
    class MockChat:
        async def send_message(self, message: str):
            render_answer(f"Echo: {message}", agent_name=agent_name_or_url)

    chat = MockChat()

    await run_chat_loop(lambda message: chat.send_message(message), agent_name=agent_name_or_url)

if __name__ == "__main__":
    asyncio.run(main())
