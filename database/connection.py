from pathlib import Path

import streamlit as st
from sqlalchemy import create_engine


def get_database_url():
    try:
        database_url = st.secrets.get("DATABASE_URL", "")
    except Exception:
        database_url = ""

    if database_url:
        database_url = str(database_url).strip()

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
    return create_engine(
        get_database_url(),
        future=True,
        pool_pre_ping=True
    )
