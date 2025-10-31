# SPDX-License-Identifier: Apache-2.0

"""
Enhanced CLI input handling with better UX using Rich library features.
"""

from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text
import re

console = Console()


def show_input_field(field: Dict[str, Any]) -> Optional[str]:
    """
    Display an enhanced input field with better styling and validation.
    
    Args:
        field: Dictionary with field_name, field_description, field_values
        
    Returns:
        User's input value or None if cancelled
    """
    field_name = field.get('field_name', 'input')
    field_desc = field.get('field_description', f'Please provide {field_name}')
    field_values = field.get('field_values')
    
    # Display field description in a styled panel
    console.print()
    console.print(Panel(
        Markdown(field_desc),
        title=f"[cyan]📝 {field_name.replace('_', ' ').title()}[/cyan]",
        border_style="cyan",
        padding=(0, 2)
    ))
    console.print()
    
    # Dropdown selection with numbered options
    if field_values and len(field_values) > 0:
        return show_dropdown_selection(field_name, field_values)
    
    # Multi-line text for long descriptions
    elif field_name in ['description', 'body', 'content', 'message', 'details']:
        return show_multiline_input(field_name)
    
    # Boolean confirmation
    elif field_name in ['confirm', 'approved', 'enabled', 'active']:
        return show_confirmation(field_name, field_desc)
    
    # Numeric input
    elif field_name in ['count', 'number', 'quantity', 'limit', 'timeout']:
        return show_numeric_input(field_name)
    
    # Regular text input with enhanced styling
    else:
        return show_text_input(field_name)


def show_dropdown_selection(field_name: str, options: List[str]) -> Optional[str]:
    """
    Show a styled dropdown selection menu.
    
    Args:
        field_name: Name of the field
        options: List of available options
        
    Returns:
        Selected value or None
    """
    # Create a styled table for options
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="bright_black",
        box=None,
        padding=(0, 2)
    )
    table.add_column("Option", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    
    for idx, value in enumerate(options, 1):
        table.add_row(f"[{idx}]", value)
    
    console.print(table)
    console.print()
    
    # Enhanced prompt with choices
    choice_text = Text()
    choice_text.append("Enter ", style="dim")
    choice_text.append("number", style="bold cyan")
    choice_text.append(" or ", style="dim")
    choice_text.append("value", style="bold cyan")
    choice_text.append(" (or ", style="dim")
    choice_text.append("'cancel'", style="bold red")
    choice_text.append(" to skip)", style="dim")
    
    console.print(choice_text)
    
    while True:
        try:
            user_input = Prompt.ask(
                f"[cyan]{field_name.replace('_', ' ').title()}[/cyan]",
                default=""
            ).strip()
            
            if not user_input:
                console.print("[yellow]⚠️  No input provided. Please try again.[/yellow]")
                continue
            
            if user_input.lower() == 'cancel':
                console.print("[red]❌ Input cancelled[/red]")
                return None
            
            # Try numeric selection
            if user_input.isdigit():
                idx = int(user_input)
                if 1 <= idx <= len(options):
                    selected = options[idx - 1]
                    console.print(f"[green]✓[/green] Selected: [bold]{selected}[/bold]")
                    return selected
                else:
                    console.print(f"[red]❌ Invalid number. Please choose 1-{len(options)}[/red]")
                    continue
            
            # Try exact match
            if user_input in options:
                console.print(f"[green]✓[/green] Selected: [bold]{user_input}[/bold]")
                return user_input
            
            # Try fuzzy match
            user_lower = user_input.lower()
            matches = [opt for opt in options if user_lower in opt.lower()]
            
            if len(matches) == 1:
                console.print(f"[green]✓[/green] Matched: [bold]{matches[0]}[/bold]")
                return matches[0]
            elif len(matches) > 1:
                console.print(f"[yellow]⚠️  Ambiguous input. Multiple matches:[/yellow]")
                for match in matches:
                    console.print(f"  - {match}")
                console.print("[yellow]Please be more specific.[/yellow]")
            else:
                console.print(f"[red]❌ '{user_input}' not found in options. Please try again.[/red]")
                
        except KeyboardInterrupt:
            console.print("\n[red]❌ Input cancelled[/red]")
            return None
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
            continue


def show_text_input(field_name: str, default: str = "") -> Optional[str]:
    """
    Show an enhanced text input prompt.
    
    Args:
        field_name: Name of the field
        default: Default value
        
    Returns:
        User input or None
    """
    try:
        # Styled prompt
        prompt_text = f"[cyan]{field_name.replace('_', ' ').title()}[/cyan]"
        
        value = Prompt.ask(
            prompt_text,
            default=default if default else None
        ).strip()
        
        if value:
            console.print(f"[green]✓[/green] Entered: [bold]{value}[/bold]")
            return value
        else:
            console.print("[yellow]⚠️  Empty input[/yellow]")
            return None
            
    except KeyboardInterrupt:
        console.print("\n[red]❌ Input cancelled[/red]")
        return None


def show_multiline_input(field_name: str) -> Optional[str]:
    """
    Show a multi-line text input interface.
    
    Args:
        field_name: Name of the field
        
    Returns:
        Multi-line text or None
    """
    console.print(Panel(
        "[dim]Enter your text below. Press [bold]Ctrl+D[/bold] (Unix) or [bold]Ctrl+Z + Enter[/bold] (Windows) when done.[/dim]",
        border_style="dim",
        padding=(0, 1)
    ))
    console.print()
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    except KeyboardInterrupt:
        console.print("\n[red]❌ Input cancelled[/red]")
        return None
    
    text = '\n'.join(lines).strip()
    if text:
        console.print(f"\n[green]✓[/green] Captured {len(lines)} lines ({len(text)} characters)")
        return text
    else:
        console.print("[yellow]⚠️  No text entered[/yellow]")
        return None


def show_confirmation(field_name: str, description: str) -> Optional[str]:
    """
    Show a yes/no confirmation prompt.
    
    Args:
        field_name: Name of the field
        description: Description of what's being confirmed
        
    Returns:
        "true" or "false" as string, or None
    """
    try:
        result = Confirm.ask(
            f"[cyan]{description}[/cyan]",
            default=False
        )
        
        status = "✓ Yes" if result else "✗ No"
        console.print(f"[green]{status}[/green]")
        
        return "true" if result else "false"
        
    except KeyboardInterrupt:
        console.print("\n[red]❌ Input cancelled[/red]")
        return None


def show_numeric_input(field_name: str, minimum: Optional[int] = None, maximum: Optional[int] = None) -> Optional[str]:
    """
    Show a numeric input prompt with validation.
    
    Args:
        field_name: Name of the field
        minimum: Minimum allowed value
        maximum: Maximum allowed value
        
    Returns:
        Numeric value as string or None
    """
    try:
        prompt_text = f"[cyan]{field_name.replace('_', ' ').title()}[/cyan]"
        
        if minimum is not None and maximum is not None:
            prompt_text += f" [dim]({minimum}-{maximum})[/dim]"
        elif minimum is not None:
            prompt_text += f" [dim](min: {minimum})[/dim]"
        elif maximum is not None:
            prompt_text += f" [dim](max: {maximum})[/dim]"
        
        while True:
            value = IntPrompt.ask(prompt_text)
            
            if minimum is not None and value < minimum:
                console.print(f"[red]❌ Value must be at least {minimum}[/red]")
                continue
            
            if maximum is not None and value > maximum:
                console.print(f"[red]❌ Value must be at most {maximum}[/red]")
                continue
            
            console.print(f"[green]✓[/green] Entered: [bold]{value}[/bold]")
            return str(value)
            
    except KeyboardInterrupt:
        console.print("\n[red]❌ Input cancelled[/red]")
        return None


def show_multi_field_form(fields: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """
    Show an interactive form with multiple fields.
    
    Args:
        fields: List of field dictionaries
        
    Returns:
        Dictionary of field_name: value pairs, or None if cancelled
    """
    console.print()
    console.print(Panel(
        f"[bold cyan]📋 Form Input[/bold cyan]\n[dim]Please provide the following information:[/dim]",
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print()
    
    results = {}
    
    for idx, field in enumerate(fields, 1):
        field_name = field.get('field_name', f'field_{idx}')
        
        # Show progress
        console.print(f"[dim]Field {idx} of {len(fields)}[/dim]")
        
        # Get input for this field
        value = show_input_field(field)
        
        if value is None:
            # User cancelled
            if Confirm.ask("[yellow]Cancel entire form?[/yellow]", default=False):
                console.print("[red]❌ Form cancelled[/red]")
                return None
            else:
                # Skip this field
                console.print("[yellow]⏭️  Skipped field[/yellow]")
                continue
        
        results[field_name] = value
        console.print()
    
    # Summary
    console.print(Panel(
        "[green]✓ Form completed[/green]\n" + 
        "\n".join([f"  • {k}: {v}" for k, v in results.items()]),
        title="[bold green]Summary[/bold green]",
        border_style="green",
        padding=(1, 2)
    ))
    
    return results


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://[^\s]+$'
    return re.match(pattern, url) is not None


def show_validated_input(field_name: str, validator_type: str) -> Optional[str]:
    """
    Show input with specific validation.
    
    Args:
        field_name: Name of the field
        validator_type: Type of validation ('email', 'url', etc.)
        
    Returns:
        Validated input or None
    """
    validators = {
        'email': (validate_email, "Please enter a valid email address"),
        'url': (validate_url, "Please enter a valid URL (http:// or https://)")
    }
    
    if validator_type not in validators:
        return show_text_input(field_name)
    
    validator_func, error_msg = validators[validator_type]
    
    while True:
        value = show_text_input(field_name)
        
        if value is None:
            return None
        
        if validator_func(value):
            return value
        else:
            console.print(f"[red]❌ {error_msg}[/red]")

