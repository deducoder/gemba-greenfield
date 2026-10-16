import sqlite3
from contextlib import closing

import pytest

from stan.cli import main


@pytest.fixture
def db(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setenv("STAN_DB", str(path))
    return path


def rows(path, sql):
    with closing(sqlite3.connect(path)) as conn:
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


def test_stan_db_vacia_usa_stan_db_del_directorio_actual(tmp_path, monkeypatch):
    monkeypatch.setenv("STAN_DB", "")
    monkeypatch.chdir(tmp_path)
    assert main(["grupo", "alta", "TWICE"]) == 0
    assert rows(tmp_path / "stan.db", "select nombre from grupo") == [("TWICE",)]


def test_base_inaccesible_muestra_error_sin_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("STAN_DB", str(tmp_path / "no-existe" / "test.db"))
    assert main(["grupo", "ver", "TWICE"]) == 1
    assert capsys.readouterr().err.startswith("error: ")


def test_amigos_crear_crea_el_grupo_con_quien_lo_crea(db):
    assert main(["amigos", "crear", "onces", "--yo", "dani"]) == 0
    assert rows(db, "select nombre from amigos") == [("onces",)]
    assert rows(db, "select nombre from miembro") == [("dani",)]


def test_amigos_y_grupos_comparten_stan_db(db):
    assert main(["grupo", "alta", "TWICE"]) == 0
    assert main(["amigos", "crear", "onces", "--yo", "dani"]) == 0
    assert rows(db, "select nombre from grupo") == [("TWICE",)]
    assert rows(db, "select nombre from amigos") == [("onces",)]


def test_amigos_crear_repetido_falla_sin_duplicar(db, capsys):
    main(["amigos", "crear", "onces", "--yo", "dani"])
    assert main(["amigos", "crear", "onces", "--yo", "dani"]) != 0
    assert "onces" in capsys.readouterr().err
    assert rows(db, "select count(*) from amigos") == [(1,)]


def test_amigos_unir_agrega_al_miembro(db):
    main(["amigos", "crear", "onces", "--yo", "dani"])
    assert main(["amigos", "unir", "onces", "--yo", "ana"]) == 0
    assert rows(db, "select nombre from miembro order by nombre") == [("ana",), ("dani",)]


def test_amigos_unir_a_grupo_inexistente_falla(db, capsys):
    assert main(["amigos", "unir", "onces", "--yo", "ana"]) != 0
    assert "onces" in capsys.readouterr().err
    assert rows(db, "select count(*) from miembro") == [(0,)]


def test_amigos_unir_repetido_falla_sin_duplicar(db, capsys):
    main(["amigos", "crear", "onces", "--yo", "dani"])
    main(["amigos", "unir", "onces", "--yo", "ana"])
    capsys.readouterr()
    assert main(["amigos", "unir", "onces", "--yo", "ana"]) != 0
    assert "ana" in capsys.readouterr().err
    assert rows(db, "select count(*) from miembro where nombre = 'ana'") == [(1,)]


def test_amigos_ver_lista_a_cada_miembro(db, capsys):
    main(["amigos", "crear", "onces", "--yo", "dani"])
    main(["amigos", "unir", "onces", "--yo", "ana"])
    main(["amigos", "crear", "otros", "--yo", "luis"])
    capsys.readouterr()
    assert main(["amigos", "ver", "onces"]) == 0
    assert capsys.readouterr().out.splitlines() == ["dani", "ana"]


def escenario():
    main(["grupo", "alta", "TWICE"])
    main(["idol", "alta", "Nayeon", "--grupo", "TWICE"])
    main(["idol", "alta", "Momo", "--grupo", "TWICE"])
    main(["grupo", "alta", "aespa"])
    main(["idol", "alta", "Karina", "--grupo", "aespa"])
    main(["amigos", "crear", "onces", "--yo", "dani"])
    main(["amigos", "unir", "onces", "--yo", "ana"])
    main(["amigos", "crear", "otros", "--yo", "dani"])


BIASES = (
    "select amigos.nombre, bias.persona, idol.nombre from bias"
    " join amigos on amigos.id = bias.amigos_id join idol on idol.id = bias.idol_id"
    " order by bias.id"
)


def test_apartar_aparta_la_bias(db):
    escenario()
    assert main(["apartar", "Nayeon", "--amigos", "onces", "--yo", "dani"]) == 0
    assert rows(db, BIASES) == [("onces", "dani", "Nayeon")]


def test_apartar_en_otro_grupo_de_amigos_si_se_puede(db):
    escenario()
    main(["apartar", "Nayeon", "--amigos", "otros", "--yo", "dani"])
    assert main(["apartar", "Nayeon", "--amigos", "onces", "--yo", "ana"]) == 0
    assert rows(db, BIASES) == [("otros", "dani", "Nayeon"), ("onces", "ana", "Nayeon")]


def test_apartar_una_bias_por_grupo_de_kpop(db):
    escenario()
    assert main(["apartar", "Nayeon", "--amigos", "onces", "--yo", "ana"]) == 0
    assert main(["apartar", "Karina", "--amigos", "onces", "--yo", "ana"]) == 0
    assert rows(db, BIASES) == [("onces", "ana", "Nayeon"), ("onces", "ana", "Karina")]


def test_apartar_idol_ya_apartada_se_rechaza_con_codigo_2(db, capsys):
    escenario()
    main(["apartar", "Nayeon", "--amigos", "onces", "--yo", "ana"])
    capsys.readouterr()
    assert main(["apartar", "Nayeon", "--amigos", "onces", "--yo", "dani"]) == 2
    assert "Nayeon ya la apartó ana" in capsys.readouterr().err
    assert rows(db, BIASES) == [("onces", "ana", "Nayeon")]


def test_apartar_segunda_bias_del_mismo_grupo_se_rechaza_con_codigo_2(db, capsys):
    escenario()
    main(["apartar", "Nayeon", "--amigos", "onces", "--yo", "ana"])
    capsys.readouterr()
    assert main(["apartar", "Momo", "--amigos", "onces", "--yo", "ana"]) == 2
    assert "ana ya tiene a Nayeon como bias de TWICE" in capsys.readouterr().err
    assert rows(db, BIASES) == [("onces", "ana", "Nayeon")]


def test_apartar_sin_ser_miembro_falla_sin_apartar(db, capsys):
    escenario()
    capsys.readouterr()
    assert main(["apartar", "Momo", "--amigos", "onces", "--yo", "luis"]) == 1
    assert "luis no es miembro de onces" in capsys.readouterr().err
    assert rows(db, BIASES) == []


def test_apartar_idol_no_registrada_falla(db, capsys):
    escenario()
    capsys.readouterr()
    assert main(["apartar", "Jennie", "--amigos", "onces", "--yo", "dani"]) == 1
    assert "la idol Jennie no está registrada" in capsys.readouterr().err


def test_amigos_ver_muestra_la_bias_de_cada_miembro(db, capsys):
    escenario()
    main(["apartar", "Nayeon", "--amigos", "onces", "--yo", "ana"])
    main(["apartar", "Karina", "--amigos", "onces", "--yo", "ana"])
    main(["apartar", "Momo", "--amigos", "otros", "--yo", "dani"])
    capsys.readouterr()
    assert main(["amigos", "ver", "onces"]) == 0
    assert capsys.readouterr().out.splitlines() == ["dani", "ana: Nayeon (TWICE), Karina (aespa)"]
