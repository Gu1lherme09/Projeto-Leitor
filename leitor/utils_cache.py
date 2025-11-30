# core/utils_cache.py
import json
from pathlib import Path
from django.conf import settings

CACHE_PATH = Path(settings.BASE_DIR) / "Cache" / "cache.json"

def ler_cache_bruto():
    """
    Lê o cache.json e devolve o dict Python.
    Se não existir, devolve None.
    """
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
