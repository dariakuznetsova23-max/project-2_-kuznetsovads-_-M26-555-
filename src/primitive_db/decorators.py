from functools import wraps
from time import monotonic

import prompt


def handle_db_errors(func):
    """Обрабатывает ошибки операций базы данных."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            )
        except KeyError as error:
            name = error.args[0] if error.args else "неизвестный объект"
            print(f"Ошибка: Таблица или столбец {name!r} не найден.")
        except ValueError as error:
            print(f"Ошибка валидации: {error}")
        except OSError as error:
            print(f"Ошибка работы с файлом: {error}")
        except Exception as error:
            print(f"Произошла непредвиденная ошибка: {error}")

        return None

    return wrapper


def confirm_action(action_name):
    """Запрашивает подтверждение перед выполнением операции."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            answer = prompt.string(
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            )

            if answer.strip().lower() != "y":
                print("Операция отменена.")
                return None

            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_time(func):
    """Выводит время выполнения функции."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        started_at = monotonic()

        try:
            return func(*args, **kwargs)
        finally:
            elapsed = monotonic() - started_at
            print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")

    return wrapper
