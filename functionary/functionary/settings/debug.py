import socket

from .base import *  # noqa

DEBUG = True

INSTALLED_APPS += ["debug_toolbar"]

# Note: Order of MIDDLEWARE content matters
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]


# Docker specific method for setting INTERNAL_IPS
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + [
    "127.0.0.1",
    "10.0.2.2",
]

try:
    from .local import *
except ImportError:
    pass
