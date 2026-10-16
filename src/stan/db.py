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
create unique index if not exists idol_grupo on idol (id, grupo_id);
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
create table if not exists bias (
    id integer primary key,
    amigos_id integer not null,
    persona text not null,
    idol_id integer not null,
    grupo_id integer not null,
    foreign key (idol_id, grupo_id) references idol(id, grupo_id),
    foreign key (amigos_id, persona) references miembro(amigos_id, nombre),
    unique (amigos_id, idol_id),
    unique (amigos_id, persona, grupo_id)
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(os.environ.get("STAN_DB") or "stan.db")
    conn.execute("pragma foreign_keys = on")
    conn.executescript(SCHEMA)
    return conn
