import os


DEFAULT_APP_PORT = 5001


def resolve_server_port(default=DEFAULT_APP_PORT):
    raw_value = os.getenv('PORT')
    if raw_value is None:
        return default

    try:
        port = int(raw_value)
    except ValueError:
        return default

    if 1 <= port <= 65535:
        return port
    return default


def preview_face_detector_enabled():
    raw_value = os.getenv('ENABLE_PREVIEW_FACE_DETECTOR', '1').strip().lower()
    return raw_value not in {'0', 'false', 'no', 'off'}
