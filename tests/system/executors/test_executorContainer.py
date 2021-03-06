from iqa.system.executor.executor_container import ExecutorContainer
from iqa.system.executor.execution import Execution
from iqa.system.command.command_base import Command


class TestExecutorContainer:
    def test_execute(self) -> None:
        executor: ExecutorContainer = ExecutorContainer(
            name="Container executor",
            container_name='sshd-iqa'
        )

        cmd: Command = Command(args=["whoami"])

        execution: Execution = executor.execute(cmd)

        assert execution.completed_successfully()
