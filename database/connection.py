from pathlib import Path

import streamlit as st
from sqlalchemy import create_engine


def get_database_url():
    """
    Em produção, usa DATABASE_URL do Streamlit Secrets.
    Em teste local, usa SQLite.
    """

    try:
        return st.secrets["DATABASE_URL"]
    except Exception:
        Path("data").mkdir(exist_ok=True)
        return "sqlite:///data/stfd_historico_local.db"


def get_engine():
    return create_engine(
        get_database_url(),
        future=True,
        pool_pre_ping=True
    )
