import json
from pathlib import Path
from typing import Any


def load_metadata(filepath: str | Path) -> dict[str, Any]:
    """Загрузить метаданные таблиц из JSON-файла."""
    try:
        with open(filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath: str | Path, data: dict[str, Any]) -> None:
    """Сохранить метаданные таблиц в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        file.write("\n")
