from fastapi.templating import Jinja2Templates
import json

templates = Jinja2Templates(directory="app/templates")


def ensure_list(value):
    if value is None:
        return []
    if isinstance(value, dict):
        return [str(v) for v in value.values()]
    if isinstance(value, list):
        # flatten any dicts inside the list (e.g. [{"size": 6}, ...])
        result = []
        for item in value:
            if isinstance(item, dict):
                result.append(str(next(iter(item.values()))))
            else:
                result.append(item)
        return result
    try:
        return list(value)
    except Exception:
        return []


def tojson_filter(value):
    return json.dumps(value, ensure_ascii=False)


templates.env.filters["ensure_list"] = ensure_list
templates.env.filters["tojson"] = tojson_filter
