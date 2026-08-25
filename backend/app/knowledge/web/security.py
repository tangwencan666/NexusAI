import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

from app.core.exceptions import ApplicationError


def _is_public_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


async def validate_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
        raise ApplicationError("INVALID_URL", "Only public HTTP and HTTPS URLs are allowed")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in {"localhost", "localhost.localdomain"}:
        raise ApplicationError("UNSAFE_URL", "Local and private network URLs are not allowed")
    try:
        direct_ip = ipaddress.ip_address(hostname)
        addresses = [str(direct_ip)]
    except ValueError:
        try:
            info = await asyncio.to_thread(
                socket.getaddrinfo, hostname, parsed.port or (443 if parsed.scheme == "https" else 80)
            )
            addresses = list({item[4][0] for item in info})
        except socket.gaierror as exc:
            raise ApplicationError("FETCH_FAILED", "URL hostname could not be resolved", 422) from exc
    if not addresses or any(not _is_public_ip(address) for address in addresses):
        raise ApplicationError("UNSAFE_URL", "URL resolves to a non-public IP address")
    return url
