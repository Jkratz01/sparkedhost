from .client import Client, Server
from .exceptions import APIError, AuthenticationError, NotFoundError, SparkedHostError

__all__ = [
    "Client",
    "Server",
    "SparkedHostError",
    "AuthenticationError",
    "NotFoundError",
    "APIError",
]
__version__ = "0.1.0"
