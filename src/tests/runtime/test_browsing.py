"""Browsing-related tests for the DockerRuntime, which connects to the ActionExecutor running in the sandbox."""

from conftest import _close_test_runtime, _load_runtime

from teai.core.logger import teai_logger as logger
from teai.events.action import (
    BrowseURLAction,
    CmdRunAction,
)
from teai.events.observation import (
    BrowserOutputObservation,
    CmdOutputObservation,
)

# ============================================================================================================================
# Browsing tests, without evaluation (poetry install --without evaluation)
# For eval environments, tests need to run with poetry install
# ============================================================================================================================


def test_simple_browse(temp_dir, runtime_cls, run_as_teai):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_teai)

    # Test browse
    action_cmd = CmdRunAction(command='python3 -m http.server 8000 > server.log 2>&1 &')
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert '[1]' in obs.content

    action_cmd = CmdRunAction(command='sleep 3 && cat server.log')
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    action_browse = BrowseURLAction(url='http://localhost:8000')
    logger.info(action_browse, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_browse)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, BrowserOutputObservation)
    assert 'http://localhost:8000' in obs.url
    assert not obs.error
    assert obs.open_pages_urls == ['http://localhost:8000/']
    assert obs.active_page_index == 0
    assert obs.last_browser_action == 'goto("http://localhost:8000")'
    assert obs.last_browser_action_error == ''
    assert 'Directory listing for /' in obs.content
    assert 'server.log' in obs.content

    # clean up
    action = CmdRunAction(command='rm -rf server.log')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    _close_test_runtime(runtime)
