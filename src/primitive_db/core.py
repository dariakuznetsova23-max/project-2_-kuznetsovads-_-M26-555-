from typing import Any

from primitive_db.utils import load_table_data

TYPE_CLASSES = {
    "int": int,
    "str": str,
    "bool": bool,
}


def get_columns(
    metadata: dict[str, Any],
    table_name: str,
) -> list[dict[str, str]]:
    """Получить схему существующей таблицы."""
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    table = metadata[table_name]

    if not isinstance(table, dict):
        raise ValueError("Не поддерживается формат метаданных таблицы.")

    columns = table.get("columns")

    if not isinstance(columns, list) or not columns:
        raise ValueError("Не поддерживается формат столбцов таблицы.")

    return columns


def create_table(
    metadata: dict[str, Any],
    table_name: str,
    columns: list[str],
) -> dict[str, Any]:
    """Создать таблицу с автоматическим столбцом ID."""
    if not table_name.isidentifier():
        raise ValueError("Некорректное имя таблицы.")

    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')

    if not columns:
        raise ValueError("Укажите хотя бы один пользовательский столбец.")

    parsed_columns = [{"name": "ID", "type": "int"}]
    names = {"ID"}

    for description in columns:
        parts = description.split(":")

        if len(parts) != 2:
            raise ValueError(f"Некорректное описание столбца: {description}")

        column_name, column_type = parts

        if not column_name.isidentifier():
            raise ValueError(f"Некорректное имя столбца: {column_name}")

        if column_name.lower() == "id":
            raise ValueError("ID добавляется автоматически. Не указывайте его.")

        if column_name in names:
            raise ValueError(f'Столбец "{column_name}" указан несколько раз.')

        if column_type not in TYPE_CLASSES:
            raise ValueError(
                f"Неподдерживаемый тип: {column_type}. Доступны int, str, bool."
            )

        names.add(column_name)
        parsed_columns.append({"name": column_name, "type": column_type})

    metadata[table_name] = {"columns": parsed_columns}
    return metadata


def drop_table(
    metadata: dict[str, Any],
    table_name: str,
) -> dict[str, Any]:
    """Удалить таблицу из метаданных."""
    get_columns(metadata, table_name)
    del metadata[table_name]
    return metadata


def list_tables(metadata: dict[str, Any]) -> list[str]:
    """Получить отсортированный список таблиц."""
    return sorted(metadata)


def validate_clause(
    metadata: dict[str, Any],
    table_name: str,
    clause: dict[str, Any],
    *,
    allow_id: bool = True,
) -> None:
    """Проверить имена столбцов и типы значений."""
    columns = get_columns(metadata, table_name)
    column_types = {column["name"]: column["type"] for column in columns}

    if not clause:
        raise ValueError("Не указаны столбцы и значения.")

    for column_name, value in clause.items():
        if column_name not in column_types:
            raise ValueError(
                f'Столбец "{column_name}" не существует в таблице "{table_name}".'
            )

        if column_name == "ID" and not allow_id:
            raise ValueError("Столбец ID нельзя изменять.")

        expected_type = column_types[column_name]

        if type(value) is not TYPE_CLASSES[expected_type]:
            raise ValueError(
                f'Для столбца "{column_name}" ожидается тип {expected_type}.'
            )


def insert(
    metadata: dict[str, Any],
    table_name: str,
    values: list[Any],
    table_data: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Добавить запись и вернуть обновлённые данные."""
    columns = get_columns(metadata, table_name)
    user_columns = [column for column in columns if column["name"] != "ID"]

    if len(values) != len(user_columns):
        raise ValueError(
            f"Ожидалось значений: {len(user_columns)}, "
            f"получено: {len(values)}. ID вводить не нужно."
        )

    record = {column["name"]: value for column, value in zip(user_columns, values)}

    validate_clause(metadata, table_name, record, allow_id=False)

    if table_data is None:
        table_data = load_table_data(table_name)

    new_id = (
        max(
            (row["ID"] for row in table_data),
            default=0,
        )
        + 1
    )

    new_record = {"ID": new_id, **record}
    return [*table_data, new_record]


def _matches(
    record: dict[str, Any],
    where_clause: dict[str, Any],
) -> bool:
    """Проверить, соответствует ли запись условию."""
    return all(
        column in record and record[column] == value
        for column, value in where_clause.items()
    )


def select(
    table_data: list[dict[str, Any]],
    where_clause: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Получить все записи или записи по условию."""
    if where_clause is None:
        return list(table_data)

    return [record for record in table_data if _matches(record, where_clause)]


def update(
    table_data: list[dict[str, Any]],
    set_clause: dict[str, Any],
    where_clause: dict[str, Any],
) -> list[dict[str, Any]]:
    """Обновить подходящие записи, сохранив остальные."""
    return [
        {**record, **set_clause} if _matches(record, where_clause) else dict(record)
        for record in table_data
    ]


def delete(
    table_data: list[dict[str, Any]],
    where_clause: dict[str, Any],
) -> list[dict[str, Any]]:
    """Удалить подходящие записи."""
    return [record for record in table_data if not _matches(record, where_clause)]
