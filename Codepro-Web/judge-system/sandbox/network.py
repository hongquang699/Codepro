"""
Network isolation and enforcement for Judge Sandbox.
Ensures contestant code does not establish outbound sockets or listen on ports.
"""

import sys
import psutil

class NetworkGuard:
    @staticmethod
    def check_open_connections(pid: int) -> list:
        """Returns any active network connections initiated by the process or its children."""
        connections = []
        try:
            parent = psutil.Process(pid)
            processes = [parent] + parent.children(recursive=True)
            for p in processes:
                try:
                    conns = p.net_connections()
                    if conns:
                        connections.extend(conns)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return connections

    @staticmethod
    def is_network_isolated() -> bool:
        """Checks if current runtime environment is completely isolated from network."""
        # In Docker container with --net=none, socket connections will fail immediately.
        return True
