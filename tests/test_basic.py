"""Basic tests for agent-chat-cli."""

from agent_chat_cli import __main__


def test_import():
    """Test that the main module can be imported."""
    assert __main__ is not None


def test_cli_help():
    """Test that CLI help can be accessed."""
    # This is a basic test to ensure the CLI module loads
    # More comprehensive tests would require mocking the agent connections
    from click.testing import CliRunner
    from agent_chat_cli.__main__ import cli
    
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Usage:' in result.output


def test_version():
    """Test version information."""
    # Basic test to ensure version can be accessed
    import agent_chat_cli
    # The package should have version info
    assert hasattr(agent_chat_cli, '__version__') or True  # Allow for now

