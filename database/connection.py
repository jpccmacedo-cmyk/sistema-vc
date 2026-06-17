from pathlib import Path

import streamlit as st
from sqlalchemy import create_engine


def get_database_url():
    """
    Usa PostgreSQL se DATABASE_URL existir no Streamlit Secrets.
    Caso contrário, usa SQLite local para teste.
    """

    try:
        database_url = st.secrets.get("DATABASE_URL", "")
    except Exception:
        database_url = ""

    if database_url:
        database_url = str(database_url).strip()

        # Compatibilidade com URLs que começam com postgresql://
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://",
                "postgresql+psycopg2://",
                1
            )

        return database_url

    Path("data").mkdir(exist_ok=True)

    return "sqlite:///data/stfd_historico_local.db"


def get_engine():
    database_url = get_database_url()

    return create_engine(
        database_url,
        future=True,
        pool_pre_ping=True
    )
