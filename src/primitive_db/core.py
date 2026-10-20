from typing import Any

SUPPORTED_TYPES = {"int", "str", "bool"}


def _print_invalid_value(value: object) -> None:
    print(f"Некорректное значение: {value}. Попробуйте снова.")


def _parse_column(column: object) -> dict[str, str] | None:
    """Преобразовать описание столбца в словарь."""
    if isinstance(column, str):
        if ":" not in column:
            _print_invalid_value(column)
            return None

        column_name, column_type = column.split(":", maxsplit=1)
    elif isinstance(column, dict):
        column_name = column.get("name")
        column_type = column.get("type")
    elif isinstance(column, (tuple, list)) and len(column) == 2:
        column_name, column_type = column
    else:
        _print_invalid_value(column)
        return None

    if not isinstance(column_name, str):
        _print_invalid_value(column)
        return None

    column_name = column_name.strip()

    if not column_name:
        _print_invalid_value(column)
        return None

    if not isinstance(column_type, str):
        _print_invalid_value(column)
        return None

    column_type = column_type.strip()

    if column_type not in SUPPORTED_TYPES:
        _print_invalid_value(column)
        return None

    return {
        "name": column_name,
        "type": column_type,
    }


def create_table(
    metadata: dict[str, Any],
    table_name: str,
    columns: list[object],
) -> dict[str, Any]:
    """Создать таблицу и вернуть обновлённые метаданные."""
    if not isinstance(table_name, str) or not table_name.strip():
        _print_invalid_value(table_name)
        return metadata

    table_name = table_name.strip()

    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    parsed_columns: list[dict[str, str]] = []
    column_names: set[str] = set()

    for column in columns:
        parsed_column = _parse_column(column)

        if parsed_column is None:
            return metadata

        column_name = parsed_column["name"]

        if column_name in column_names:
            _print_invalid_value(column)
            return metadata

        column_names.add(column_name)
        parsed_columns.append(parsed_column)

    if "ID" in column_names:
        id_column = next(column for column in parsed_columns if column["name"] == "ID")

        if id_column["type"] != "int":
            _print_invalid_value("ID должен иметь тип int")
            return metadata

        parsed_columns = [
            id_column,
            *[column for column in parsed_columns if column["name"] != "ID"],
        ]
    else:
        parsed_columns.insert(
            0,
            {
                "name": "ID",
                "type": "int",
            },
        )

    metadata[table_name] = {
        "columns": parsed_columns,
    }

    columns_text = ", ".join(
        f"{column['name']}:{column['type']}" for column in parsed_columns
    )

    print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_text}')

    return metadata


def drop_table(
    metadata: dict[str, Any],
    table_name: str,
) -> dict[str, Any]:
    """Удалить таблицу и вернуть обновлённые метаданные."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    del metadata[table_name]

    print(f'Таблица "{table_name}" успешно удалена.')

    return metadata


def list_tables(metadata: dict[str, Any]) -> None:
    """Вывести список всех таблиц."""
    if not metadata:
        print("Таблиц пока нет.")
        return

    for table_name in metadata:
        print(f"- {table_name}")
