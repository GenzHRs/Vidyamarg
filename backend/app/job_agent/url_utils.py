"""
VidyaMarg AI — URL Security & SSRF Protection Utilities.
Guarantees outbound HTTP requests are restricted to safe public destinations.
Blocks loopback, private IPv4/IPv6 ranges, link-local metadata endpoints, and internal hostnames.
"""
import ipaddress
import socket
import urllib.parse
import logging
from typing import Optional, Tuple

logger = logging.getLogger("app.job_agent.url_utils")

BLOCKED_HOSTNAMES = {"localhost", "loopback", "metadata", "instance-data"}

def is_safe_public_url(url: str) -> bool:
    """
    Validates whether a URL targets a valid, safe public internet destination.
    Returns False for loopback, private IPs, cloud metadata IPs, and internal domains.
    """
    if not url or not isinstance(url, str):
        return False
    
    url_trimmed = url.strip()
    if not (url_trimmed.startswith("http://") or url_trimmed.startswith("https://")):
        return False

    try:
        parsed = urllib.parse.urlparse(url_trimmed)
        hostname = parsed.hostname
        if not hostname:
            return False

        hostname_lower = hostname.lower()
        if hostname_lower in BLOCKED_HOSTNAMES or hostname_lower.endswith((".local", ".internal", ".lan")):
            return False

        # Resolve hostname to IP address
        try:
            addr_info = socket.getaddrinfo(hostname, None)
        except Exception as err:
            logger.warning(f"SSRF Check: Unable to resolve hostname '{hostname}': {err}")
            return False

        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
                if (
                    ip_obj.is_private
                    or ip_obj.is_loopback
                    or ip_obj.is_link_local
                    or ip_obj.is_multicast
                    or ip_obj.is_reserved
                    or ip_str.startswith("169.254.")
                ):
                    logger.warning(f"SSRF Protection blocked IP '{ip_str}' for URL '{url}'")
                    return False
            except ValueError:
                return False

        return True
    except Exception as e:
        logger.warning(f"SSRF Check error for URL '{url}': {e}")
        return False


def canonicalize_url(url: str) -> str:
    """
    Canonicalizes job URLs while strictly preserving query parameters
    that identify specific jobs (e.g., jobId, gh_jid, id, reqId, jk, vjs).
    """
    if not url:
        return ""
    
    trimmed = url.strip()
    try:
        parsed = urllib.parse.urlparse(trimmed)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path
        if path.endswith("/") and len(path) > 1:
            path = path[:-1]
        
        # Sort query params for consistent hashing while preserving all keys and values
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        sorted_query = urllib.parse.urlencode(sorted(query_pairs))
        
        canonical = urllib.parse.urlunparse((scheme, netloc, path, parsed.params, sorted_query, ""))
        return canonical
    except Exception:
        return trimmed
