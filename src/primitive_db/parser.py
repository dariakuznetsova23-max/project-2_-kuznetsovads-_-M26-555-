import ast
import re
from typing import Any

TOKEN_PATTERN = re.compile(
    r""""(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'"""
    r"|[+-]?[0-9]+"
    r"|[^\W\d]\w*"
    r"|[,():=]"
)


def tokenize(text: str) -> list[str]:
    """Разбить команду на части, сохранив строки в кавычках."""
    tokens = []
    position = 0

    while position < len(text):
        if text[position].isspace():
            position += 1
            continue

        match = TOKEN_PATTERN.match(text, position)

        if match is None:
            raise ValueError(f"Не удалось разобрать часть команды: {text[position:]}")

        tokens.append(match.group())
        position = match.end()

    return tokens


def parse_value(token: str) -> int | str | bool:
    """Преобразовать текст в int, str или bool."""
    if token.startswith(("'", '"')):
        try:
            value = ast.literal_eval(token)
        except (SyntaxError, ValueError) as error:
            raise ValueError(f"Некорректная строка: {token}") from error

        if type(value) is not str:
            raise ValueError("Ожидалась строка в кавычках.")

        return value

    if token.lower() == "true":
        return True

    if token.lower() == "false":
        return False

    if re.fullmatch(r"[+-]?[0-9]+", token):
        return int(token)

    raise ValueError(
        f"Некорректное значение: {token}. Строки необходимо заключать в кавычки."
    )


class Reader:
    """Последовательно прочитать части команды."""

    def __init__(self, text: str) -> None:
        self.tokens = tokenize(text)
        self.position = 0

    def peek(self) -> str | None:
        if self.position >= len(self.tokens):
            return None

        return self.tokens[self.position]

    def take(self) -> str:
        token = self.peek()

        if token is None:
            raise ValueError("Команда не закончена.")

        self.position += 1
        return token

    def expect(self, expected: str) -> None:
        token = self.take()

        if token.lower() != expected.lower():
            raise ValueError(f'Ожидалось "{expected}", получено "{token}".')

    def name(self) -> str:
        token = self.take()

        if not token.isidentifier():
            raise ValueError(f"Некорректное имя: {token}")

        return token

    def value(self) -> int | str | bool:
        return parse_value(self.take())

    def assignment(self) -> tuple[str, int | str | bool]:
        column_name = self.name()
        self.expect("=")
        return column_name, self.value()

    def where(self) -> dict[str, int | str | bool]:
        column_name, value = self.assignment()
        return {column_name: value}

    def assignments(self) -> dict[str, int | str | bool]:
        result = {}

        while True:
            column_name, value = self.assignment()

            if column_name in result:
                raise ValueError(f'Столбец "{column_name}" указан несколько раз.')

            result[column_name] = value

            if self.peek() != ",":
                break

            self.expect(",")

        return result

    def end(self) -> None:
        if self.peek() is not None:
            raise ValueError(f"Лишняя часть команды: {self.peek()}")


def parse_where_clause(text: str) -> dict[str, int | str | bool]:
    """Например: age = 28 -> {'age': 28}."""
    reader = Reader(text)
    result = reader.where()
    reader.end()
    return result


def parse_set_clause(text: str) -> dict[str, int | str | bool]:
    """Например: age = 29, is_active = false."""
    reader = Reader(text)
    result = reader.assignments()
    reader.end()
    return result


def parse_command(text: str) -> dict[str, Any]:
    """Разобрать одну команду базы данных."""
    reader = Reader(text)
    command = reader.take().lower()
    result: dict[str, Any] = {"command": command}

    if command in {"help", "exit", "list_tables"}:
        pass

    elif command == "create_table":
        result["table"] = reader.name()
        columns = []

        while reader.peek() is not None:
            column_name = reader.name()
            reader.expect(":")
            column_type = reader.name()
            columns.append(f"{column_name}:{column_type}")

        if not columns:
            raise ValueError("Укажите хотя бы один пользовательский столбец.")

        result["columns"] = columns

    elif command in {"drop_table", "info"}:
        result["table"] = reader.name()

    elif command == "insert":
        reader.expect("into")
        result["table"] = reader.name()
        reader.expect("values")
        reader.expect("(")

        values = []

        if reader.peek() != ")":
            while True:
                values.append(reader.value())

                if reader.peek() != ",":
                    break

                reader.expect(",")

        reader.expect(")")
        result["values"] = values

    elif command == "select":
        reader.expect("from")
        result["table"] = reader.name()
        result["where"] = None

        if reader.peek() is not None:
            reader.expect("where")
            result["where"] = reader.where()

    elif command == "update":
        result["table"] = reader.name()
        reader.expect("set")
        result["set"] = reader.assignments()
        reader.expect("where")
        result["where"] = reader.where()

    elif command == "delete":
        reader.expect("from")
        result["table"] = reader.name()
        reader.expect("where")
        result["where"] = reader.where()

    else:
        raise ValueError(f'Неизвестная команда "{command}". Введите help.')

    reader.end()
    return result
