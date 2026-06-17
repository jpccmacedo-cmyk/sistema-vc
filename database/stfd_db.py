from datetime import datetime
import uuid

import pandas as pd
from sqlalchemy import text

from database.connection import get_engine


def init_stfd_db():
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stfd_uploads (
                batch_id TEXT PRIMARY KEY,
                nome_arquivo TEXT NOT NULL,
                data_upload TEXT NOT NULL,
                usuario TEXT,
                observacao TEXT
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stfd_records (
                id TEXT PRIMARY KEY,
                batch_id TEXT NOT NULL,
                fonte TEXT NOT NULL,
                ano INTEGER,
                mes INTEGER,
                planta TEXT,
                kpi TEXT,
                dia INTEGER,
                data_label TEXT,
                valor_real REAL,
                m300 REAL,
                rf REAL,
                acumulado_mes REAL,
                data_upload TEXT NOT NULL
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_stfd_records_filtros
            ON stfd_records (fonte, ano, mes, planta, kpi)
        """))


def criar_batch_upload(nome_arquivo, usuario=None, observacao=None):
    init_stfd_db()

    batch_id = str(uuid.uuid4())
    data_upload = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO stfd_uploads (
                    batch_id,
                    nome_arquivo,
                    data_upload,
                    usuario,
                    observacao
                )
                VALUES (
                    :batch_id,
                    :nome_arquivo,
                    :data_upload,
                    :usuario,
                    :observacao
                )
            """),
            {
                "batch_id": batch_id,
                "nome_arquivo": nome_arquivo,
                "data_upload": data_upload,
                "usuario": usuario,
                "observacao": observacao,
            }
        )

    return batch_id, data_upload


def salvar_records_stfd(df_records):
    init_stfd_db()

    if df_records.empty:
        return 0

    df_records = df_records.copy()
    df_records["id"] = [str(uuid.uuid4()) for _ in range(len(df_records))]

    colunas = [
        "id",
        "batch_id",
        "fonte",
        "ano",
        "mes",
        "planta",
        "kpi",
        "dia",
        "data_label",
        "valor_real",
        "m300",
        "rf",
        "acumulado_mes",
        "data_upload",
    ]

    df_records = df_records[colunas]

    engine = get_engine()

    df_records.to_sql(
        "stfd_records",
        engine,
        if_exists="append",
        index=False
    )

    return len(df_records)


def listar_uploads():
    init_stfd_db()

    engine = get_engine()

    query = """
        SELECT
            batch_id,
            nome_arquivo,
            data_upload,
            usuario,
            observacao
        FROM stfd_uploads
        ORDER BY data_upload DESC
    """

    return pd.read_sql(query, engine)


def carregar_records():
    init_stfd_db()

    engine = get_engine()

    query = """
        SELECT
            r.*,
            u.nome_arquivo
        FROM stfd_records r
        LEFT JOIN stfd_uploads u
            ON r.batch_id = u.batch_id
    """

    return pd.read_sql(query, engine)


def excluir_batch(batch_id):
    init_stfd_db()

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM stfd_records WHERE batch_id = :batch_id"),
            {"batch_id": batch_id}
        )

        conn.execute(
            text("DELETE FROM stfd_uploads WHERE batch_id = :batch_id"),
            {"batch_id": batch_id}
        )
