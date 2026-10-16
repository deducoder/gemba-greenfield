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


def idol_alta(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    grupo = conn.execute("select id from grupo where nombre = ?", (args.grupo,)).fetchone()
    if grupo is None:
        return error(f"el grupo {args.grupo} no existe")
    conn.execute("insert into idol (nombre, grupo_id) values (?, ?)", (args.nombre, grupo[0]))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="stan")
    entidades = p.add_subparsers(required=True)

    grupo = entidades.add_parser("grupo").add_subparsers(required=True)
    alta = grupo.add_parser("alta")
    alta.add_argument("nombre")
    alta.set_defaults(comando=grupo_alta)

    idol = entidades.add_parser("idol").add_subparsers(required=True)
    alta = idol.add_parser("alta")
    alta.add_argument("nombre")
    alta.add_argument("--grupo", required=True)
    alta.set_defaults(comando=idol_alta)

    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    conn = connect()
    try:
        with conn:
            return args.comando(conn, args)
    finally:
        conn.close()
