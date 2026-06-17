from datetime import datetime
import uuid
import json

import pandas as pd
from sqlalchemy import text

from database.connection import get_engine


def init_consolidados_db():
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS consolidados_gerados (
                consolidado_id TEXT PRIMARY KEY,
                nome_arquivo TEXT NOT NULL,
                data_processada TEXT,
                ano INTEGER,
                mes INTEGER,
                data_geracao TEXT NOT NULL,
                arquivo_excel BYTEA,
                logs TEXT,
                abas_criadas TEXT
            )
        """))


def _bytes_from_resultado(resultado):
    arquivo_excel = resultado["arquivo_excel"]
    arquivo_excel.seek(0)
    return arquivo_excel.getvalue()


def salvar_consolidado_no_banco(resultado):
    init_consolidados_db()

    consolidado_id = str(uuid.uuid4())
    data_geracao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    nome_arquivo = resultado["nome_arquivo_final"]
    arquivo_bytes = _bytes_from_resultado(resultado)

    data_processada = resultado.get("data_processada")

    if data_processada:
        data_texto = data_processada.strftime("%Y-%m-%d")
        ano = data_processada.year
        mes = data_processada.month
    else:
        data_texto = None
        ano = None
        mes = None

    logs = json.dumps(resultado.get("logs", []), ensure_ascii=False)
    abas_criadas = json.dumps(resultado.get("abas_criadas", []), ensure_ascii=False)

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO consolidados_gerados (
                    consolidado_id,
                    nome_arquivo,
                    data_processada,
                    ano,
                    mes,
                    data_geracao,
                    arquivo_excel,
                    logs,
                    abas_criadas
                )
                VALUES (
                    :consolidado_id,
                    :nome_arquivo,
                    :data_processada,
                    :ano,
                    :mes,
                    :data_geracao,
                    :arquivo_excel,
                    :logs,
                    :abas_criadas
                )
            """),
            {
                "consolidado_id": consolidado_id,
                "nome_arquivo": nome_arquivo,
                "data_processada": data_texto,
                "ano": ano,
                "mes": mes,
                "data_geracao": data_geracao,
                "arquivo_excel": arquivo_bytes,
                "logs": logs,
                "abas_criadas": abas_criadas,
            }
        )

    return consolidado_id


def salvar_resultados_consolidados_no_banco(resultados):
    ids = []

    for resultado in resultados:
        consolidado_id = salvar_consolidado_no_banco(resultado)
        ids.append(consolidado_id)

    return ids


def listar_consolidados():
    init_consolidados_db()

    engine = get_engine()

    query = """
        SELECT
            consolidado_id,
            nome_arquivo,
            data_processada,
            ano,
            mes,
            data_geracao,
            logs,
            abas_criadas
        FROM consolidados_gerados
        ORDER BY data_processada DESC, data_geracao DESC
    """

    return pd.read_sql(query, engine)


def carregar_arquivo_consolidado(consolidado_id):
    init_consolidados_db()

    engine = get_engine()

    query = text("""
        SELECT
            nome_arquivo,
            arquivo_excel
        FROM consolidados_gerados
        WHERE consolidado_id = :consolidado_id
    """)

    with engine.begin() as conn:
        row = conn.execute(
            query,
            {"consolidado_id": consolidado_id}
        ).fetchone()

    if not row:
        return None, None

    nome_arquivo = row[0]
    arquivo_excel = row[1]

    if isinstance(arquivo_excel, memoryview):
        arquivo_excel = arquivo_excel.tobytes()

    return nome_arquivo, arquivo_excel


def excluir_consolidado(consolidado_id):
    init_consolidados_db()

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM consolidados_gerados WHERE consolidado_id = :consolidado_id"),
            {"consolidado_id": consolidado_id}
        )
