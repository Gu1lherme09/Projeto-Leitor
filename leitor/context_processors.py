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
    Devolve, por exemplo:
      - cache_last_updated_label: "há 5 min", "há 2 h", "há 1 d"
      - cache_age_minutes: idade do cache em minutos (int ou None)
      - cache_stale: True se o cache passou de 30 minutos
    """
    label = "indisponível"
    cache_age_minutes = None
    cache_stale = False

    try:
        with CACHE_JSON_PATH.open(encoding="utf-8") as f:
            data = json.load(f)

        raw = data.get("data")  # string no formato "%d_%m_%Y,%H:%M"
        if raw:
            dt = datetime.strptime(raw, "%d_%m_%Y,%H:%M")
            dt = timezone.make_aware(dt, timezone.get_default_timezone())

            now = timezone.now()
            delta = now - dt

            # texto amigável que você já usava
            label = f"há {_humanize_delta(delta)}"

            # idade em minutos
            cache_age_minutes = max(0, int(delta.total_seconds() // 60))

            # considerado "velho" se passou de 30 minutos
            if cache_age_minutes >= 30:
                cache_stale = True

    except Exception:
        # se der qualquer pau, deixamos os defaults
        pass

    return {
        "cache_last_updated_label": label,
        "cache_age_minutes": cache_age_minutes,
        "cache_stale": cache_stale,
    }
