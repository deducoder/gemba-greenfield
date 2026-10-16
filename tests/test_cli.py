import sqlite3

import pytest

from stan.cli import main


@pytest.fixture
def db(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setenv("STAN_DB", str(path))
    return path


def rows(path, sql):
    with sqlite3.connect(path) as conn:
        return conn.execute(sql).fetchall()


def test_grupo_alta_registra_el_grupo(db):
    assert main(["grupo", "alta", "TWICE"]) == 0
    assert rows(db, "select nombre from grupo") == [("TWICE",)]


def test_grupo_alta_usa_stan_db_sin_tocar_el_directorio_actual(db, tmp_path, monkeypatch):
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    assert main(["grupo", "alta", "TWICE"]) == 0
    assert db.exists()
    assert not (cwd / "stan.db").exists()


def test_grupo_alta_sin_stan_db_usa_stan_db_del_directorio_actual(tmp_path, monkeypatch):
    monkeypatch.delenv("STAN_DB", raising=False)
    monkeypatch.chdir(tmp_path)
    assert main(["grupo", "alta", "TWICE"]) == 0
    assert rows(tmp_path / "stan.db", "select nombre from grupo") == [("TWICE",)]


def test_grupo_alta_repetido_falla_sin_duplicar(db, capsys):
    main(["grupo", "alta", "TWICE"])
    assert main(["grupo", "alta", "TWICE"]) != 0
    assert "TWICE" in capsys.readouterr().err
    assert rows(db, "select count(*) from grupo") == [(1,)]


def test_idol_alta_registra_a_la_integrante(db):
    main(["grupo", "alta", "TWICE"])
    assert main(["idol", "alta", "Nayeon", "--grupo", "TWICE"]) == 0
    assert rows(
        db, "select idol.nombre, grupo.nombre from idol join grupo on grupo.id = idol.grupo_id"
    ) == [("Nayeon", "TWICE")]


def test_idol_alta_en_grupo_inexistente_falla_sin_registrar(db, capsys):
    assert main(["idol", "alta", "Nayeon", "--grupo", "TWICE"]) != 0
    assert "TWICE" in capsys.readouterr().err
    assert rows(db, "select count(*) from idol") == [(0,)]


def test_grupo_ver_lista_a_cada_integrante(db, capsys):
    main(["grupo", "alta", "TWICE"])
    main(["idol", "alta", "Nayeon", "--grupo", "TWICE"])
    main(["idol", "alta", "Momo", "--grupo", "TWICE"])
    main(["grupo", "alta", "aespa"])
    main(["idol", "alta", "Karina", "--grupo", "aespa"])
    capsys.readouterr()
    assert main(["grupo", "ver", "TWICE"]) == 0
    assert capsys.readouterr().out.splitlines() == ["Nayeon", "Momo"]
