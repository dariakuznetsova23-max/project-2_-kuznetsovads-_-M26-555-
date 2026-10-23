from pathlib import Path
from typing import Any

from prettytable import PrettyTable

from primitive_db import core
from primitive_db.core import clear_select_cache
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
    """Вывести справку по командам."""
    print(HELP_TEXT)


def print_records(
    records: list[dict[str, Any]],
    columns: list[dict[str, str]],
) -> None:
    """Показать записи с помощью PrettyTable."""
    table = PrettyTable()

    column_names = [column["name"] for column in columns]

    table.field_names = column_names

    for record in records:
        table.add_row([record[column_name] for column_name in column_names])

    print(table)

    if not records:
        print("Подходящих записей нет.")


def execute_command(
    parsed: dict[str, Any],
    metadata_filepath: Path,
) -> bool:
    """
    Выполнить одну команду.

    Возвращает False, если приложение должно завершить работу.
    Возвращает True, если нужно продолжить работу.
    """
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

    if command == "create_table":
        table_name = parsed["table"]

        result = core.create_table(
            metadata,
            table_name,
            parsed["columns"],
        )

        if result is None:
            return True

        save_metadata(
            metadata_filepath,
            result,
        )

        save_table_data(
            table_name,
            [],
        )

        clear_select_cache()

        columns = core.get_columns(
            result,
            table_name,
        )

        columns_text = ", ".join(
            f"{column['name']}:{column['type']}" for column in columns
        )

        print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_text}')

        return True

    if command == "drop_table":
        table_name = parsed["table"]

        result = core.drop_table(
            metadata,
            table_name,
        )

        if result is None:
            return True

        delete_table_data(table_name)

        save_metadata(
            metadata_filepath,
            result,
        )

        clear_select_cache()

        print(f'Таблица "{table_name}" успешно удалена.')

        return True

    table_name = parsed["table"]

    columns = core.get_columns(
        metadata,
        table_name,
    )

    if command == "info":
        table_data = load_table_data(table_name)

        columns_text = ", ".join(
            f"{column['name']}:{column['type']}" for column in columns
        )

        print(f"Таблица: {table_name}")
        print(f"Столбцы: {columns_text}")
        print(f"Количество записей: {len(table_data)}")

        return True

    if command == "insert":
        table_data = load_table_data(table_name)

        result = core.insert(
            metadata,
            table_name,
            parsed["values"],
            table_data=table_data,
        )

        if result is None:
            return True

        save_table_data(
            table_name,
            result,
        )

        clear_select_cache()

        print(
            f"Запись с ID={result[-1]['ID']} успешно добавлена "
            f'в таблицу "{table_name}".'
        )

        return True

    where_clause = parsed.get("where")

    if where_clause is not None:
        core.validate_clause(
            metadata,
            table_name,
            where_clause,
        )

    if command == "select":
        table_data = load_table_data(table_name)

        result = core.select(
            table_data,
            where_clause,
        )

        if result is None:
            return True

        print_records(
            result,
            columns,
        )

        return True

    if command == "update":
        set_clause = parsed["set"]

        core.validate_clause(
            metadata,
            table_name,
            set_clause,
            allow_id=False,
        )

        table_data = load_table_data(table_name)

        matched_records = core.select(
            table_data,
            where_clause,
        )

        if matched_records is None:
            return True

        if not matched_records:
            print("Подходящих записей нет. Данные не изменены.")
            return True

        result = core.update(
            table_data,
            set_clause,
            where_clause,
        )

        if result is None:
            return True

        save_table_data(
            table_name,
            result,
        )

        clear_select_cache()

        for record in matched_records:
            print(
                f"Запись с ID={record['ID']} в таблице "
                f'"{table_name}" успешно обновлена.'
            )

        return True

    if command == "delete":
        table_data = load_table_data(table_name)

        matched_records = core.select(
            table_data,
            where_clause,
        )

        if matched_records is None:
            return True

        if not matched_records:
            print("Подходящих записей нет. Данные не изменены.")
            return True

        result = core.delete(
            table_data,
            where_clause,
        )

        if result is None:
            return True

        save_table_data(
            table_name,
            result,
        )

        clear_select_cache()

        for record in matched_records:
            print(
                f'Запись с ID={record["ID"]} успешно удалена из таблицы "{table_name}".'
            )

        return True

    raise ValueError(f'Команда "{command}" не поддерживается.')


def run(filepath: str | Path | None = None) -> None:
    """Запустить интерактивную базу данных."""
    metadata_filepath = Path(filepath) if filepath is not None else METADATA_FILE

    print_help()

    while True:
        try:
            text = input(">>> Введите команду: ").strip()

            if not text:
                continue

            parsed = parse_command(text)

            should_continue = execute_command(
                parsed,
                metadata_filepath,
            )

            if not should_continue:
                break

        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания!")
            break

        except ValueError as error:
            print(f"Ошибка валидации или формата данных: {error}")

        except KeyError as error:
            name = error.args[0] if error.args else "неизвестный объект"
            print(
                f"Ошибка: Таблица, столбец или обязательное поле {name!r} не найдено."
            )

        except OSError as error:
            print(f"Ошибка работы с файлом: {error}")

        except TypeError as error:
            print(f"Ошибка структуры данных. Проверьте JSON-файлы: {error}")
