import os
import subprocess
import time
from dataclasses import dataclass

from teai.core.logger import teai_logger as logger
from teai.events.action import Action, IPythonRunCellAction
from teai.events.observation import IPythonRunCellObservation
from teai.runtime.plugins.jupyter.execute_server import JupyterKernel
from teai.runtime.plugins.requirement import Plugin, PluginRequirement
from teai.runtime.utils import find_available_tcp_port
from teai.utils.shutdown_listener import should_continue


@dataclass
class JupyterRequirement(PluginRequirement):
    name: str = 'jupyter'


class JupyterPlugin(Plugin):
    name: str = 'jupyter'

    async def initialize(self, username: str, kernel_id: str = 'teai-default'):
        self.kernel_gateway_port = find_available_tcp_port(40000, 49999)
        self.kernel_id = kernel_id
        if username in ['root', 'teai']:
            # Non-LocalRuntime
            prefix = f'su - {username} -s '
            # cd to code repo, setup all env vars and run micromamba
            poetry_prefix = (
                'cd /teai/code\n'
                'export POETRY_VIRTUALENVS_PATH=/teai/poetry;\n'
                'export PYTHONPATH=/teai/code:$PYTHONPATH;\n'
                'export MAMBA_ROOT_PREFIX=/teai/micromamba;\n'
                '/teai/micromamba/bin/micromamba run -n teai '
            )
        else:
            # LocalRuntime
            prefix = ''
            code_repo_path = os.environ.get('TEAI_REPO_PATH')
            if not code_repo_path:
                raise ValueError(
                    'TEAI_REPO_PATH environment variable is not set. '
                    'This is required for the jupyter plugin to work with LocalRuntime.'
                )
            # assert POETRY_VIRTUALENVS_PATH is set
            poetry_venvs_path = os.environ.get('POETRY_VIRTUALENVS_PATH')
            if not poetry_venvs_path:
                raise ValueError(
                    'POETRY_VIRTUALENVS_PATH environment variable is not set. '
                    'This is required for the jupyter plugin to work with LocalRuntime.'
                )
            poetry_prefix = f'cd {code_repo_path}\n'
        jupyter_launch_command = (
            f"{prefix}/bin/bash << 'EOF'\n"
            f'{poetry_prefix}'
            'poetry run jupyter kernelgateway '
            '--KernelGatewayApp.ip=0.0.0.0 '
            f'--KernelGatewayApp.port={self.kernel_gateway_port}\n'
            'EOF'
        )
        logger.debug(f'Jupyter launch command: {jupyter_launch_command}')

        self.gateway_process = subprocess.Popen(
            jupyter_launch_command,
            stderr=subprocess.STDOUT,
            shell=True,
        )
        # read stdout until the kernel gateway is ready
        output = ''
        while should_continue() and self.gateway_process.stdout is not None:
            line = self.gateway_process.stdout.readline().decode('utf-8')
            output += line
            if 'at' in line:
                break
            time.sleep(1)
            logger.debug('Waiting for jupyter kernel gateway to start...')

        logger.debug(
            f'Jupyter kernel gateway started at port {self.kernel_gateway_port}. Output: {output}'
        )
        _obs = await self.run(
            IPythonRunCellAction(code='import sys; print(sys.executable)')
        )
        self.python_interpreter_path = _obs.content.strip()

    async def _run(self, action: Action) -> IPythonRunCellObservation:
        """Internal method to run a code cell in the jupyter kernel."""
        if not isinstance(action, IPythonRunCellAction):
            raise ValueError(
                f'Jupyter plugin only supports IPythonRunCellAction, but got {action}'
            )

        if not hasattr(self, 'kernel'):
            self.kernel = JupyterKernel(
                f'localhost:{self.kernel_gateway_port}', self.kernel_id
            )

        if not self.kernel.initialized:
            await self.kernel.initialize()
        output = await self.kernel.execute(action.code, timeout=action.timeout)
        return IPythonRunCellObservation(
            content=output,
            code=action.code,
        )

    async def run(self, action: Action) -> IPythonRunCellObservation:
        obs = await self._run(action)
        return obs
