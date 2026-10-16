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


def amigos_crear(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    try:
        amigos = conn.execute("insert into amigos (nombre) values (?)", (args.nombre,))
    except sqlite3.IntegrityError:
        return error(f"el grupo de amigos {args.nombre} ya existe")
    conn.execute("insert into miembro (amigos_id, nombre) values (?, ?)", (amigos.lastrowid, args.yo))
    return 0


def amigos_unir(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    amigos = conn.execute("select id from amigos where nombre = ?", (args.nombre,)).fetchone()
    if amigos is None:
        return error(f"el grupo de amigos {args.nombre} no existe")
    try:
        conn.execute("insert into miembro (amigos_id, nombre) values (?, ?)", (amigos[0], args.yo))
    except sqlite3.IntegrityError:
        return error(f"{args.yo} ya es miembro de {args.nombre}")
    return 0


def amigos_ver(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    miembros = conn.execute(
        "select miembro.nombre from miembro join amigos on amigos.id = miembro.amigos_id"
        " where amigos.nombre = ? order by miembro.id",
        (args.nombre,),
    )
    for (nombre,) in miembros:
        print(nombre)
    return 0


def apartar(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    amigos = conn.execute("select id from amigos where nombre = ?", (args.amigos,)).fetchone()
    if amigos is None:
        return error(f"el grupo de amigos {args.amigos} no existe")
    idol_id, grupo_id = conn.execute(
        "select id, grupo_id from idol where nombre = ?", (args.idol,)
    ).fetchone()
    conn.execute(
        "insert into bias (amigos_id, persona, idol_id, grupo_id) values (?, ?, ?, ?)",
        (amigos[0], args.yo, idol_id, grupo_id),
    )
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

    amigos = entidades.add_parser("amigos").add_subparsers(required=True)
    amigos_crear_p = amigos.add_parser("crear")
    amigos_crear_p.add_argument("nombre")
    amigos_crear_p.add_argument("--yo", required=True)
    amigos_crear_p.set_defaults(comando=amigos_crear)
    amigos_unir_p = amigos.add_parser("unir")
    amigos_unir_p.add_argument("nombre")
    amigos_unir_p.add_argument("--yo", required=True)
    amigos_unir_p.set_defaults(comando=amigos_unir)
    amigos_ver_p = amigos.add_parser("ver")
    amigos_ver_p.add_argument("nombre")
    amigos_ver_p.set_defaults(comando=amigos_ver)

    apartar_p = entidades.add_parser("apartar")
    apartar_p.add_argument("idol")
    apartar_p.add_argument("--amigos", required=True)
    apartar_p.add_argument("--yo", required=True)
    apartar_p.set_defaults(comando=apartar)

    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        with closing(connect()) as conn, conn:
            return args.comando(conn, args)
    except sqlite3.Error as e:
        return error(str(e))
