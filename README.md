# Primitive DB

Учебное консольное приложение на Python.

На текущем этапе реализованы интерактивный цикл,
справка и завершение программы.

## Требования

- uv
- Python 3.12 или новее

## Подготовка
```powershell
uv sync
```

## Запуск
```powershell
uv run project
```

Альтернативный запуск:
```powershell
uv run python -m primitive_db.main
```

## Команды

- `help` — показать справку.
- `exit` — завершить программу.

## Качество кода
```powershell
uv run ruff check .
uv run ruff format --check .
```

## Сборка
```powershell
uv build
```

## Управление таблицами

Для запуска базы данных используется команда:
```powershell
uv run database

## Демонстрация

[Запись работы базы данных на Asciinema](https://asciinema.org/connect/5c9af3bf-7631-443f-bfd6-81ae7afbb649)
