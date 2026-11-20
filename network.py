"""Per-request routing with bounded TCP attempts; TLS verification stays enabled."""
import http.client
import socket
import time
import urllib.request


def connect(address, timeout=60, source_address=None):
    # Some networks advertise IPv6 routes that silently drop outgoing traffic.
    # Prefer IPv4 for this client only, retaining IPv6 as a fallback. Do not
    # patch global sockets: other Streamlit sessions must remain independent.
    host, port = address
    deadline = time.monotonic() + min(float(timeout), 10)
    records = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
    records.sort(key=lambda r: r[0] != socket.AF_INET)
    last_error = None
    for family, kind, protocol, _, sockaddr in records:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        sock = socket.socket(family, kind, protocol)
        try:
            sock.settimeout(min(2, remaining))
            if source_address:
                sock.bind(source_address)
            sock.connect(sockaddr)
            sock.settimeout(timeout)
            return sock
        except OSError as error:
            last_error = error
            sock.close()
    raise last_error or TimeoutError('Provider TCP connection timed out.')


class HTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_connection = connect


class HTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, request):
        # Use urllib's normal certificate-verifying SSL context and headers.
        return self.do_open(HTTPSConnection, request, context=self._context)


def open_request(request, timeout=60):
    return urllib.request.build_opener(HTTPSHandler()).open(request, timeout=timeout)
