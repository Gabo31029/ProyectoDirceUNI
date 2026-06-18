from tests.integration import conftest as integration_conftest


class _ConnRecorder:
    def __init__(self) -> None:
        self.sql_texts: list[str] = []

    def execute(self, statement, params):
        self.sql_texts.append(str(statement))
        return None


def test_cleanup_skips_perfil_alumno_when_table_not_exists(monkeypatch):
    monkeypatch.setattr(integration_conftest, "_table_exists", lambda conn, name: False)
    conn = _ConnRecorder()

    integration_conftest._cleanup_integration_data(conn, "f1111111-1111-1111-1111-111111111111")

    assert not any("DELETE FROM perfil_alumno" in sql for sql in conn.sql_texts)


def test_cleanup_deletes_perfil_alumno_when_table_exists(monkeypatch):
    monkeypatch.setattr(
        integration_conftest,
        "_table_exists",
        lambda conn, name: name == "perfil_alumno",
    )
    conn = _ConnRecorder()

    integration_conftest._cleanup_integration_data(conn, "f1111111-1111-1111-1111-111111111111")

    assert any("DELETE FROM perfil_alumno" in sql for sql in conn.sql_texts)
