import pytest

from iqa.system.executor.executor_container import ExecutorContainer
from iqa.system.service.service import ServiceStatus
from iqa.system.service.service_docker import ServiceDocker


class TestServiceDocker:

    @pytest.fixture
    def service(self) -> ServiceDocker:
        executor: ExecutorContainer = ExecutorContainer(
            name='Docker executor',
            container_name='artemis'
        )

        service: ServiceDocker = ServiceDocker(
            name='artemis',
            executor=executor
        )

        return service

    def test_service_start(self, service: ServiceDocker) -> None:
        service.start()
        assert service.status() == ServiceStatus.RUNNING

    def test_service_restart(self, service: ServiceDocker) -> None:
        service.restart()
        assert service.status() == ServiceStatus.RUNNING

    def test_service_stop(self, service: ServiceDocker) -> None:
        service.stop()
        assert service.status() == ServiceStatus.STOPPED
