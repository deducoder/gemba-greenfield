import argparse
import sqlite3
import sys

from stan.db import connect


def error(mensaje: str) -> int:
    print(f"error: {mensaje}", file=sys.stderr)
    return 1


def grupo_alta(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    try:
        conn.execute("insert into grupo (nombre) values (?)", (args.nombre,))
    except sqlite3.IntegrityError:
        return error(f"el grupo {args.nombre} ya existe")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="stan")
    entidades = p.add_subparsers(required=True)

    grupo = entidades.add_parser("grupo").add_subparsers(required=True)
    alta = grupo.add_parser("alta")
    alta.add_argument("nombre")
    alta.set_defaults(comando=grupo_alta)

    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    conn = connect()
    try:
        with conn:
            return args.comando(conn, args)
    finally:
        conn.close()
