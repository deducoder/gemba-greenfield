import argparse
import sqlite3
import sys
from contextlib import closing

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
    grupo_alta_p = grupo.add_parser("alta")
    grupo_alta_p.add_argument("nombre")
    grupo_alta_p.set_defaults(comando=grupo_alta)
    grupo_ver_p = grupo.add_parser("ver")
    grupo_ver_p.add_argument("nombre")
    grupo_ver_p.set_defaults(comando=grupo_ver)

    idol = entidades.add_parser("idol").add_subparsers(required=True)
    idol_alta_p = idol.add_parser("alta")
    idol_alta_p.add_argument("nombre")
    idol_alta_p.add_argument("--grupo", required=True)
    idol_alta_p.set_defaults(comando=idol_alta)

    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        with closing(connect()) as conn, conn:
            return args.comando(conn, args)
    except sqlite3.Error as e:
        return error(str(e))
