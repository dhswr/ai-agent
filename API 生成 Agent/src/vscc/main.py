"""VSCC 统一入口."""

from .cli.commands import app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
