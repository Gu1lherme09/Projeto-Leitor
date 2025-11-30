# leitor/context_processors.py
import json
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.utils import timezone

CACHE_JSON_PATH = Path(settings.BASE_DIR) / "Cache" / "cache.json"


def _humanize_delta(delta):
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "alguns segundos"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} h"
    days = hours // 24
    return f"{days} d"


def cache_info(request):
    """
    Devolve algo como: "há 5 min", "há 2 h", "há 1 d" etc.
    Fica disponível no template como: cache_last_updated_label
    """
    label = "indisponível"

    try:
        with CACHE_JSON_PATH.open(encoding="utf-8") as f:
            data = json.load(f)

        raw = data.get("data") 
        if raw:
            dt = datetime.strptime(raw, "%d_%m_%Y,%H:%M")
            # deixa aware no timezone do Django
            dt = timezone.make_aware(dt, timezone.get_default_timezone())

            now = timezone.now()
            delta = now - dt
            label = f"há {_humanize_delta(delta)}"
    except Exception:
        # se der qualquer pau, mantemos "indisponível"
        pass

    return {
        "cache_last_updated_label": label,
    }
