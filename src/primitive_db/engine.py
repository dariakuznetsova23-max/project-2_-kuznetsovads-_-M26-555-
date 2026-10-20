import prompt

HELP_TEXT = """<command> exit - выйти из программы
<command> help - справочная информация"""


def welcome() -> None:
    print("Первая попытка запустить проект!")
    print()
    print("***")
    print(HELP_TEXT)

    while True:
        try:
            command = prompt.string("Введите команду: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания!")
            break

        if command == "exit":
            print("До свидания!")
            break

        if command == "help":
            print()
            print(HELP_TEXT)
        elif command:
            print("Неизвестная команда. Введите help для справки.")