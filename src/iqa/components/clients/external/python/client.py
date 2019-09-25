from iqa.components.clients.external import ClientExternal, protocols
from iqa.system.node import Node


class ClientPython(ClientExternal):
    """Python Proton client (base abstract class)."""

    supported_protocols = [protocols.Amqp10()]
    implementation = 'python'
    version = '1.0.1'

    def __init__(self, name: str, node: Node, **kwargs):
        super(ClientPython, self).__init__(name, node, **kwargs)
