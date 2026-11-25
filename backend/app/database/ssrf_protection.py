import socket
import ipaddress
from app.core.config import settings

FORBIDDEN_HOSTS = {
    "169.254.169.254",  # AWS/Cloud metadata service
    "metadata.google.internal",
}

def validate_host_safety(host: str) -> None:
    """
    Validate that the destination host does not attempt unauthorized SSRF
    against internal cloud metadata or forbidden endpoints.
    """
    if not host:
        raise ValueError("Database host cannot be empty.")

    host_lower = host.strip().lower()

    if host_lower in FORBIDDEN_HOSTS:
        raise ValueError(f"Access to forbidden cloud metadata host '{host}' is blocked for security.")

    if not settings.ALLOW_PRIVATE_IPS:
        try:
            ip = ipaddress.ip_address(host_lower)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                raise ValueError(f"Access to private IP address '{host}' is restricted by organization policy.")
        except ValueError as e:
            if "restricted by organization policy" in str(e):
                raise
            # If host is a domain, resolve it
            try:
                resolved_ip = socket.gethostbyname(host_lower)
                ip = ipaddress.ip_address(resolved_ip)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    raise ValueError(f"Domain '{host}' resolves to restricted private IP '{resolved_ip}'.")
            except socket.gaierror:
                pass  # Resolution failed, will fail at connection time
