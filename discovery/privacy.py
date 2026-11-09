"""Local consent checked at the outbound boundary, including existing profiles."""
import json
from .paths import data_root


def enabled(name):
    if name not in ('communityEnabled', 'registryEnabled'):
        return False
    try:
        value = json.loads((data_root() / 'settings.json').read_text(encoding='utf-8'))
        return (isinstance(value, dict) and value.get('communityEnabled') is True
                and (name == 'communityEnabled' or value.get('registryEnabled') is True))
    except (OSError, ValueError):
        return False
