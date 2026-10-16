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


def grupo_ver(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    integrantes = conn.execute(
        "select idol.nombre from idol join grupo on grupo.id = idol.grupo_id"
        " where grupo.nombre = ? order by idol.id",
        (args.nombre,),
    )
    for (nombre,) in integrantes:
        print(nombre)
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
    ver = grupo.add_parser("ver")
    ver.add_argument("nombre")
    ver.set_defaults(comando=grupo_ver)

    idol = entidades.add_parser("idol").add_subparsers(required=True)
    alta = idol.add_parser("alta")
    alta.add_argument("nombre")
    alta.add_argument("--grupo", required=True)
    alta.set_defaults(comando=idol_alta)

    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        conn = connect()
        try:
            with conn:
                return args.comando(conn, args)
        finally:
            conn.close()
    except sqlite3.Error as e:
        return error(str(e))
