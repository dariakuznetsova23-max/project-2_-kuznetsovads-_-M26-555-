import shlex
from pathlib import Path

import prompt

from primitive_db.core import create_table, drop_table, list_tables
from primitive_db.utils import load_metadata, save_metadata

METADATA_FILE = Path("db_meta.json")


def print_help() -> None:
    """Вывести справку по командам."""
    print("\n***База данных***")
    print("Функции:")
    print(
        "<command> create_table <имя_таблицы> "
        "<столбец1:тип> <столбец2:тип> .. - создать таблицу"
    )
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def _print_invalid_value(value: object) -> None:
    print(f"Некорректное значение: {value}. Попробуйте снова.")


def _parse_input(user_input: str) -> list[str] | None:
    """Безопасно разобрать строку команды с помощью shlex."""
    try:
        return shlex.split(user_input)
    except ValueError:
        _print_invalid_value(user_input)
        return None


def run(filepath: str | Path | None = None) -> None:
    """Запустить основной цикл базы данных."""
    metadata_filepath = filepath or METADATA_FILE

    print_help()

    while True:
        metadata = load_metadata(metadata_filepath)

        try:
            user_input = prompt.string(">>>Введите команду: ")
        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания!")
            break

        arguments = _parse_input(user_input)

        if not arguments:
            continue

        command = arguments[0].lower()

        if command == "exit":
            print("До свидания!")
            break

        if command == "help":
            print_help()
            continue

        if command == "list_tables":
            if len(arguments) != 1:
                _print_invalid_value(" ".join(arguments))
                continue

            list_tables(metadata)
            continue

        if command == "create_table":
            if len(arguments) < 3:
                _print_invalid_value(" ".join(arguments))
                continue

            table_name = arguments[1]
            columns = arguments[2:]
            table_existed = table_name in metadata

            updated_metadata = create_table(
                metadata,
                table_name,
                columns,
            )

            table_created = not table_existed and table_name in updated_metadata

            if table_created:
                save_metadata(
                    metadata_filepath,
                    updated_metadata,
                )

            continue

        if command == "drop_table":
            if len(arguments) != 2:
                _print_invalid_value(" ".join(arguments))
                continue

            table_name = arguments[1]
            table_existed = table_name in metadata

            updated_metadata = drop_table(
                metadata,
                table_name,
            )

            table_deleted = table_existed and table_name not in updated_metadata

            if table_deleted:
                save_metadata(
                    metadata_filepath,
                    updated_metadata,
                )

            continue

        print(f"Функции {arguments[0]} нет. Попробуйте снова.")
