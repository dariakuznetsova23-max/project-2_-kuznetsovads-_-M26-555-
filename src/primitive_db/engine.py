from pathlib import Path

from prettytable import PrettyTable

from primitive_db import core
from primitive_db.parser import parse_command
from primitive_db.utils import (
    delete_table_data,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

METADATA_FILE = Path("db_meta.json")


HELP_TEXT = """
***Операции с данными***

create_table <таблица> <столбец:тип> ... - создать таблицу
list_tables - показать список таблиц
drop_table <таблица> - удалить таблицу

insert into <таблица> values (<значение1>, ...) - добавить запись
select from <таблица> - показать все записи
select from <таблица> where <столбец> = <значение> - найти записи
update <таблица> set <столбец> = <значение> where <столбец> = <значение>
delete from <таблица> where <столбец> = <значение> - удалить записи
info <таблица> - информация о таблице

help - справка
exit - выход

Типы данных: int, str, bool.
Строки должны быть в кавычках.
Логические значения: true и false.
ID создаётся автоматически и не передаётся при вставке.
"""


def print_help() -> None:
    print(HELP_TEXT)


def print_records(records, columns) -> None:
    """Показать записи с помощью PrettyTable."""
    table = PrettyTable()
    column_names = [column["name"] for column in columns]
    table.field_names = column_names

    for record in records:
        table.add_row([record[column_name] for column_name in column_names])

    print(table)

    if not records:
        print("Подходящих записей нет.")


def execute_command(parsed, metadata_filepath: Path) -> bool:
    """Выполнить команду. False означает выход."""
    command = parsed["command"]

    if command == "exit":
        print("До свидания!")
        return False

    if command == "help":
        print_help()
        return True

    metadata = load_metadata(metadata_filepath)

    if command == "list_tables":
        tables = core.list_tables(metadata)

        if tables:
            print("\n".join(tables))
        else:
            print("Таблиц пока нет.")

        return True

    table_name = parsed["table"]

    if command == "create_table":
        metadata = core.create_table(
            metadata,
            table_name,
            parsed["columns"],
        )

        save_table_data(table_name, [])
        save_metadata(metadata_filepath, metadata)

        columns = core.get_columns(metadata, table_name)
        columns_text = ", ".join(
            f"{column['name']}:{column['type']}" for column in columns
        )

        print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_text}')
        return True

    if command == "drop_table":
        metadata = core.drop_table(metadata, table_name)
        delete_table_data(table_name)
        save_metadata(metadata_filepath, metadata)
        print(f'Таблица "{table_name}" успешно удалена.')
        return True

    columns = core.get_columns(metadata, table_name)

    if command == "info":
        data = load_table_data(table_name)
        columns_text = ", ".join(
            f"{column['name']}:{column['type']}" for column in columns
        )

        print(f"Таблица: {table_name}")
        print(f"Столбцы: {columns_text}")
        print(f"Количество записей: {len(data)}")
        return True

    if command == "insert":
        data = load_table_data(table_name)
        new_data = core.insert(
            metadata,
            table_name,
            parsed["values"],
            table_data=data,
        )

        save_table_data(table_name, new_data)

        print(
            f"Запись с ID={new_data[-1]['ID']} успешно добавлена "
            f'в таблицу "{table_name}".'
        )
        return True

    where_clause = parsed["where"]

    if where_clause is not None:
        core.validate_clause(metadata, table_name, where_clause)

    if command == "update":
        core.validate_clause(
            metadata,
            table_name,
            parsed["set"],
            allow_id=False,
        )

    data = load_table_data(table_name)

    if command == "select":
        records = core.select(data, where_clause)
        print_records(records, columns)
        return True

    matched_records = core.select(data, where_clause)

    if not matched_records:
        print("Подходящих записей нет. Данные не изменены.")
        return True

    if command == "update":
        new_data = core.update(
            data,
            parsed["set"],
            where_clause,
        )
    else:
        new_data = core.delete(data, where_clause)

    save_table_data(table_name, new_data)

    for record in matched_records:
        if command == "update":
            print(
                f"Запись с ID={record['ID']} в таблице "
                f'"{table_name}" успешно обновлена.'
            )
        else:
            print(
                f'Запись с ID={record["ID"]} успешно удалена из таблицы "{table_name}".'
            )

    return True


def run(filepath: str | Path | None = None) -> None:
    """Запустить интерактивную базу данных."""
    metadata_filepath = Path(filepath) if filepath else METADATA_FILE
    print_help()

    while True:
        try:
            text = input(">>> Введите команду: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания!")
            break

        if not text:
            continue

        try:
            parsed = parse_command(text)
            should_continue = execute_command(
                parsed,
                metadata_filepath,
            )
        except (ValueError, OSError) as error:
            print(f"Ошибка: {error}")
            continue
        except (KeyError, TypeError) as error:
            print(f"Ошибка структуры сохранённых данных. Проверьте JSON-файлы: {error}")
            continue

        if not should_continue:
            break
