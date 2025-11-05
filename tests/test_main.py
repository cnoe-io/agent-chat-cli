"""Tests for CLI main entry point."""

from unittest.mock import patch, MagicMock
from click.testing import CliRunner


def test_get_version_from_metadata():
    """Test version reading from importlib.metadata."""
    from agent_chat_cli.__main__ import get_version

    with patch('importlib.metadata.version') as mock_version:
        mock_version.return_value = "1.2.3"
        result = get_version()
        assert result == "1.2.3"


def test_get_version_from_pyproject():
    """Test version reading from pyproject.toml as fallback."""
    from agent_chat_cli.__main__ import get_version

    with patch('importlib.metadata.version') as mock_version:
        mock_version.side_effect = Exception("Not found")
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value = mock_file
            mock_open.return_value = mock_file
            with patch('tomllib.load') as mock_toml:
                mock_toml.return_value = {"project": {"version": "2.3.4"}}
                result = get_version()
                assert result == "2.3.4"


def test_get_version_fallback():
    """Test version fallback to 0.0.0."""
    from agent_chat_cli.__main__ import get_version

    with patch('importlib.metadata.version') as mock_version:
        mock_version.side_effect = Exception("Not found")
        with patch('builtins.open', side_effect=Exception("File not found")):
            result = get_version()
            assert result == "0.0.0"


def test_cli_group_exists():
    """Test that CLI group is defined."""
    from agent_chat_cli.__main__ import cli
    assert cli is not None
    assert callable(cli)


def test_cli_version_option():
    """Test CLI --version option."""
    from agent_chat_cli.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])

    assert result.exit_code == 0
    assert 'agent-chat-cli' in result.output or 'version' in result.output.lower()


def test_cli_help():
    """Test CLI --help option."""
    from agent_chat_cli.__main__ import cli

    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])

    assert result.exit_code == 0
    assert 'Usage:' in result.output or 'help' in result.output.lower()


def test_a2a_command_exists():
    """Test that a2a command is registered."""
    from agent_chat_cli.__main__ import cli, a2a

    assert a2a is not None
    # Check that a2a is a subcommand
    assert 'a2a' in [cmd.name for cmd in cli.commands.values() if hasattr(cmd, 'name')]


def test_slim_command_exists():
    """Test that slim command is registered."""
    from agent_chat_cli.__main__ import cli, slim

    assert slim is not None
    # Check that slim is a subcommand
    assert 'slim' in [cmd.name for cmd in cli.commands.values() if hasattr(cmd, 'name')]


def test_a2a_command_parameters():
    """Test a2a command has expected parameters."""
    from agent_chat_cli.__main__ import a2a

    # Check that command has expected options
    param_names = [p.name for p in a2a.params]
    assert 'host' in param_names
    assert 'port' in param_names
    assert 'token' in param_names
    assert 'debug' in param_names


def test_slim_command_parameters():
    """Test slim command has expected parameters."""
    from agent_chat_cli.__main__ import slim

    # Check that command has expected options
    param_names = [p.name for p in slim.params]
    assert 'endpoint' in param_names or 'remote_card' in param_names


def test_load_client_module_function_exists():
    """Test that load_client_module function exists."""
    from agent_chat_cli.__main__ import load_client_module

    assert load_client_module is not None
    assert callable(load_client_module)

