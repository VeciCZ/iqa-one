import logging
import posixpath
import re
import time
from enum import Enum
from typing import Union, Optional

from typing.re import Pattern

from iqa.system.command.command_ansible import CommandAnsible
from iqa.system.command.command_base import Command
from iqa.system.executor import Executor, ExecutorAnsible
from iqa.system.executor.execution import Execution
from iqa.system.service.service import ServiceStatus
from iqa.system.service.service_fake import ServiceFake
from iqa.utils.tcp_util import TcpUtil


class ServiceFakeArtemis(ServiceFake):
    """
    Implementation of a Artemis pseudo-service to manage a Server component.
    """

    MAX_ATTEMPTS: int = 10
    DELAY: int = 3

    _logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, name: Optional[str], executor: Executor, **kwargs):
        super().__init__(name, executor)
        self.name: Optional[str] = 'artemis-service'

        self.ansible_host: str = kwargs.get('ansible_host', 'localhost')
        self.service_default_port: str = kwargs.get('artemis_port', '61616')
        self.service_web_port: str = kwargs.get('broker_web_port', '8161')
        self.service_path: str = posixpath.join(kwargs.get('broker_path'), 'bin', 'artemis-service')  # type: ignore
        self.service_username: str = kwargs.get('broker_service_user', 'jamq')

    class ServiceSystemState(Enum):
        STARTED = ('start', 'started')
        STOPPED = ('stop', 'stopped')
        RESTARTED = ('restart', 'restarted')

        def __init__(self, system_state, ansible_state):
            self.system_state = system_state
            self.ansible_state = ansible_state

    def status(self) -> ServiceStatus:
        """
        Returns the service status based on linux service.
        :return: The status of this specific service
        :rtype: ServiceStatus
        """
        # service output :
        # is running
        # is stopped

        # systemctl output:
        # (running)
        # (dead)

        # On RHEL7> service is automatically redirected to systemctl
        cmd_status: Command = Command(
            ['runuser', '-l', self.service_username, '%s status' % self.service_path],
            stdout=True,
            timeout=self.TIMEOUT,
        )
        execution: Execution = self.executor.execute(cmd_status)

        service_output: Optional[Union[str, list]] = execution.read_stdout()

        if not service_output:
            ServiceFakeArtemis._logger.debug('Service: %s - Status: FAILED' % self.name)
            return ServiceStatus.FAILED

        running_pattern: Pattern = r'(is running|\(running\)|Running)'
        stopped_pattern: Pattern = r'(is stopped|\(dead\)|Stopped)'
        if re.search(running_pattern, service_output):
            ServiceFakeArtemis._logger.debug(
                'Service: %s - Status: RUNNING' % self.name
            )
            return ServiceStatus.RUNNING
        elif re.search(stopped_pattern, service_output):
            ServiceFakeArtemis._logger.debug(
                'Service: %s - Status: STOPPED' % self.name
            )
            return ServiceStatus.STOPPED

        ServiceFakeArtemis._logger.debug('Service: %s - Status: UNKNOWN' % self.name)
        return ServiceStatus.UNKNOWN

    def start(self, wait_for_messaging=False) -> Execution:
        execution: Execution = self.executor.execute(
            self._create_command(self.ServiceSystemState.STARTED)
        )
        self._wait_for_messaging(wait_for_messaging)
        return execution

    def stop(self) -> Execution:
        return self.executor.execute(
            self._create_command(self.ServiceSystemState.STOPPED)
        )

    def enable(self) -> Execution:
        return NotImplemented

    def disable(self) -> Execution:
        return NotImplemented

    def restart(self, wait_for_messaging=False) -> Execution:
        execution: Execution = self.executor.execute(
            self._create_command(self.ServiceSystemState.RESTARTED)
        )
        self._wait_for_messaging(wait_for_messaging)
        return execution

    def _wait_for_messaging(self, messaging_wait=False):
        # Wait until broker web port is available
        self.__tcp_wait_for_accessible_port(self.service_web_port, self.ansible_host)

        # Or also messaging subsystem goes up
        if messaging_wait:
            self.__tcp_wait_for_accessible_port(
                self.service_default_port, self.ansible_host
            )

    @staticmethod
    def __tcp_wait_for_accessible_port(port, host):
        for attempt in range(ServiceFakeArtemis.MAX_ATTEMPTS):
            if attempt == ServiceFakeArtemis.MAX_ATTEMPTS - 1:
                print(
                    '     broker is not reachable after %d attempts'
                    % ServiceFakeArtemis.MAX_ATTEMPTS
                )

            if TcpUtil.is_tcp_port_available(int(port), host):
                return True

            time.sleep(ServiceFakeArtemis.DELAY)
        ServiceFakeArtemis._logger.warning(
            'Unable to connect to hostname:port: %s:%s' % (host, port)
        )
        return False

    def _create_command(self, service_state: ServiceSystemState):
        """
        Creates a Command instance based on executor type and state
        that is specific to each type of command.
        :param service_state:
        :return:
        :return:
        """
        command: str = 'runuser -l %s %s %s' % (
            self.service_username,
            self.service_path,
            service_state.system_state,
        )
        if isinstance(self.executor, ExecutorAnsible):
            return CommandAnsible(
                command, ansible_module='command', stdout=True, timeout=self.TIMEOUT
            )
        else:
            return Command(command.split(), stdout=True, timeout=self.TIMEOUT)
