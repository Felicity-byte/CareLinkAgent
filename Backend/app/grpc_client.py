"""Shared gRPC client module with TLS support and auto-reconnect (v2)"""
import os
import sys
import grpc
from typing import Optional, Tuple, Any

AI_SERVICE_HOST = os.getenv("AI_SERVICE_HOST", "127.0.0.1:50053")
GRPC_SECURE = os.getenv("GRPC_SECURE", "false").lower() == "true"
GRPC_CA_CERT = os.getenv("GRPC_CA_CERT", "")
GRPC_CONNECT_TIMEOUT = float(os.getenv("AI_GRPC_CONNECT_TIMEOUT", "3"))

_stub: Optional[Any] = None
_channel: Optional[grpc.Channel] = None
_pb2_module: Any = None


def _get_pb2_modules():
    """Import and cache the protobuf modules."""
    global _pb2_module
    if _pb2_module is not None:
        return _pb2_module

    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(backend_dir)
    connect_dir = os.path.join(project_root, "GlmAI", "connect")
    if connect_dir not in sys.path:
        sys.path.insert(0, connect_dir)

    import medical_ai_pb2
    import medical_ai_pb2_grpc

    _pb2_module = medical_ai_pb2
    return medical_ai_pb2, medical_ai_pb2_grpc


def _create_channel():
    """Create a gRPC channel (secure or insecure)."""
    if GRPC_SECURE:
        if not GRPC_CA_CERT:
            raise ValueError(
                "GRPC_SECURE=true but GRPC_CA_CERT is not set. "
                "Provide the path to the CA certificate."
            )
        with open(GRPC_CA_CERT, "rb") as f:
            root_cert = f.read()
        credentials = grpc.ssl_channel_credentials(root_certificates=root_cert)
        channel = grpc.secure_channel(
            AI_SERVICE_HOST,
            credentials,
            options=[
                ("grpc.keepalive_time_ms", 30000),
                ("grpc.keepalive_timeout_ms", 10000),
                ("grpc.http2.max_pings_without_data", 0),
            ],
        )
    else:
        if os.getenv("GRPC_ALLOW_INSECURE", "true") != "true":
            raise RuntimeError("Insecure gRPC connections disabled via GRPC_ALLOW_INSECURE")
        channel = grpc.insecure_channel(
            AI_SERVICE_HOST,
            options=[
                ("grpc.keepalive_time_ms", 30000),
                ("grpc.keepalive_timeout_ms", 10000),
                ("grpc.http2.max_pings_without_data", 0),
            ],
        )
    return channel


def get_grpc_stub():
    """Get or create a gRPC stub with health check and auto-reconnect."""
    global _stub, _channel, _pb2_module

    try:
        if _stub and _channel:
            try:
                grpc.channel_ready_future(_channel).result(timeout=GRPC_CONNECT_TIMEOUT)
                return _stub, _channel, _pb2_module
            except (grpc.FutureTimeoutError, grpc.RpcError):
                print("[WARNING] gRPC channel unhealthy, reconnecting...")
                _channel.close()
                _stub = None
                _channel = None

        pb2, pb2_grpc = _get_pb2_modules()

        _channel = _create_channel()
        grpc.channel_ready_future(_channel).result(timeout=GRPC_CONNECT_TIMEOUT)

        _stub = pb2_grpc.PostSurgeryFollowUpServiceStub(_channel)
        return _stub, _channel, _pb2_module

    except Exception as e:
        print(f"[ERROR] gRPC connection failed: {e}")
        if _channel:
            _channel.close()
        _stub = None
        _channel = None
        return None, None, None


def reset_grpc_stub():
    """Force reset the gRPC stub for recovery."""
    global _stub, _channel
    if _channel:
        _channel.close()
    _stub = None
    _channel = None
