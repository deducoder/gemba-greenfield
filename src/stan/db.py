import os
import sqlite3

SCHEMA = """
create table if not exists grupo (
    id integer primary key,
    nombre text unique not null
);
create table if not exists idol (
    id integer primary key,
    nombre text not null,
    grupo_id integer not null references grupo(id)
);
create table if not exists amigos (
    id integer primary key,
    nombre text unique not null
);
create table if not exists miembro (
    id integer primary key,
    amigos_id integer not null references amigos(id),
    nombre text not null,
    unique (amigos_id, nombre)
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(os.environ.get("STAN_DB") or "stan.db")
    conn.execute("pragma foreign_keys = on")
    conn.executescript(SCHEMA)
    return conn
