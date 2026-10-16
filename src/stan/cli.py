import argparse
import sqlite3
import sys
from contextlib import closing

from stan.db import connect


def error(mensaje: str, codigo: int = 1) -> int:
    print(f"error: {mensaje}", file=sys.stderr)
    return codigo


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
    filas = conn.execute(
        "select miembro.nombre, idol.nombre, grupo.nombre from miembro"
        " join amigos on amigos.id = miembro.amigos_id"
        " left join bias on bias.amigos_id = miembro.amigos_id and bias.persona = miembro.nombre"
        " left join idol on idol.id = bias.idol_id"
        " left join grupo on grupo.id = bias.grupo_id"
        " where amigos.nombre = ? order by miembro.id, bias.id",
        (args.nombre,),
    )
    biases: dict[str, list[str]] = {}
    for miembro, idol, grupo in filas:
        suyas = biases.setdefault(miembro, [])
        if idol is not None:
            suyas.append(f"{idol} ({grupo})")
    for miembro, suyas in biases.items():
        print(f"{miembro}: {', '.join(suyas)}" if suyas else miembro)
    return 0


def apartar(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    amigos = conn.execute("select id from amigos where nombre = ?", (args.amigos,)).fetchone()
    if amigos is None:
        return error(f"el grupo de amigos {args.amigos} no existe")
    (amigos_id,) = amigos
    idol = conn.execute("select id, grupo_id from idol where nombre = ?", (args.idol,)).fetchone()
    if idol is None:
        return error(f"la idol {args.idol} no está registrada")
    idol_id, grupo_id = idol
    miembro = conn.execute(
        "select 1 from miembro where amigos_id = ? and nombre = ?", (amigos_id, args.yo)
    ).fetchone()
    if miembro is None:
        return error(f"{args.yo} no es miembro de {args.amigos}")
    propia = conn.execute(
        "select idol.nombre, grupo.nombre from bias"
        " join idol on idol.id = bias.idol_id join grupo on grupo.id = bias.grupo_id"
        " where bias.amigos_id = ? and bias.persona = ? and bias.grupo_id = ?",
        (amigos_id, args.yo, grupo_id),
    ).fetchone()
    if propia is not None:
        return error(f"{args.yo} ya tiene a {propia[0]} como bias de {propia[1]}", 2)
    ocupada = conn.execute(
        "select persona from bias where amigos_id = ? and idol_id = ?", (amigos_id, idol_id)
    ).fetchone()
    if ocupada is not None:
        return error(f"{args.idol} ya la apartó {ocupada[0]}", 2)
    conn.execute(
        "insert into bias (amigos_id, persona, idol_id, grupo_id) values (?, ?, ?, ?)",
        (amigos_id, args.yo, idol_id, grupo_id),
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
