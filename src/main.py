import uci


def main() -> None:
    uciLoop = uci.UCI()

    while True:
        command = input()
        uciLoop.processCommand(command)

        if command == "quit":
            break


if __name__ == "__main__":
    main()
