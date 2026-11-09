"""Firewall topology definition for Online Judge."""
from typing import Dict, List

class FirewallTopology:
    @staticmethod
    def get_port_rules() -> Dict[str, List[Dict[str, str]]]:
        return {
            'public_ingress': [
                {'port': '80/tcp', 'service': 'HTTP (Redirect to HTTPS)', 'access': 'ALL'},
                {'port': '443/tcp', 'service': 'HTTPS (Nginx Reverse Proxy)', 'access': 'ALL'},
            ],
            'internal_ingress': [
                {'port': '3000/tcp', 'service': 'Node.js Frontend Server', 'access': 'LOCAL_PROXY_ONLY'},
                {'port': '8000/tcp', 'service': 'Django Backend API', 'access': 'LOCAL_PROXY_ONLY'},
                {'port': '9999/tcp', 'service': 'Judge Server REST Engine', 'access': 'BACKEND_AND_WORKERS_ONLY'},
                {'port': '5432/tcp', 'service': 'PostgreSQL Database', 'access': 'BACKEND_ONLY'},
                {'port': '6379/tcp', 'service': 'Redis Broker / Cache', 'access': 'BACKEND_AND_DISPATCHER_ONLY'},
            ]
        }
