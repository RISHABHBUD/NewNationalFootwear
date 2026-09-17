from fastapi.templating import Jinja2Templates
import json

templates = Jinja2Templates(directory="app/templates")


def ensure_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    if value is None:
        return []
    try:
        return list(value)
    except Exception:
        return []


def tojson_filter(value):
    return json.dumps(value, ensure_ascii=False)


templates.env.filters["ensure_list"] = ensure_list
templates.env.filters["tojson"] = tojson_filter
