import os
import html
from datetime import datetime, date
from io import BytesIO
from urllib.parse import urlparse, unquote

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

try:
    import streamlit as st
except Exception:
    st = None


# ============================================================
# Conexão com PostgreSQL / Neon
# ============================================================

def _secrets_get(*keys):
    """Busca chaves de forma segura em st.secrets."""
    if st is None:
        return None
    try:
        obj = st.secrets
        for key in keys:
            if key not in obj:
                return None
            obj = obj[key]
        return obj
    except Exception:
        return None


def _normalizar_url(url):
    """
    Normaliza URLs vindas do Streamlit Secrets/Neon.

    Corrige casos comuns:
    - postgresql+psycopg2:// -> postgresql://
    - postgres+psycopg2:// -> postgresql://
    - postgres:// -> postgresql://
    - &amp; -> &
    - aspas/espaços acidentais
    """
    if url is None:
        return None

    url = str(url).strip().strip('"').strip("'").strip()

    # Corrige entidades HTML copiadas do navegador, por exemplo: &amp; vira &.
    url = html.unescape(url)

    # Corrige formatos de SQLAlchemy para formato aceito pelo psycopg2 puro.
    url = url.replace("postgresql+psycopg2://", "postgresql://")
    url = url.replace("postgres+psycopg2://", "postgresql://")

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    return url


def _connect_from_mapping(cfg):
    """
    Conecta usando dict de credenciais, aceitando formatos comuns:
    host/user/password/dbname/port/sslmode ou database/username.
    """
    if cfg is None:
        return None

    try:
        cfg = dict(cfg)
    except Exception:
        return None

    if "url" in cfg:
        return _connect_from_url(cfg.get("url"))

    kwargs = {}
    aliases = {
        "host": ["host", "hostname"],
        "dbname": ["dbname", "database", "db"],
        "user": ["user", "username"],
        "password": ["password", "pass"],
        "port": ["port"],
        "sslmode": ["sslmode"],
    }

    for destino, possiveis in aliases.items():
        for chave in possiveis:
            if chave in cfg and cfg[chave] not in [None, ""]:
                kwargs[destino] = cfg[chave]
                break

    if "host" not in kwargs or "dbname" not in kwargs or "user" not in kwargs:
        return None

    if "sslmode" not in kwargs:
        kwargs["sslmode"] = "require"

    return psycopg2.connect(**kwargs)


def _connect_from_url(url):
    """
    Conecta a partir de URL.

    Primeiro tenta usar a URL normalizada diretamente.
    Se falhar, quebra a URL em parâmetros com urlparse.
    """
    url = _normalizar_url(url)
    if not url:
        return None

    try:
        if "sslmode=" in url:
            return psycopg2.connect(url)
        return psycopg2.connect(url, sslmode="require")
    except Exception:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.hostname:
            raise

        dbname = parsed.path[1:] if parsed.path.startswith("/") else parsed.path
        kwargs = {
            "host": parsed.hostname,
            "dbname": unquote(dbname),
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "port": parsed.port or 5432,
            "sslmode": "require",
        }
        return psycopg2.connect(**kwargs)


def get_connection():
    """
    Formatos aceitos no Streamlit Secrets:

    1) DATABASE_URL = "postgresql+psycopg2://user:senha@host/db?sslmode=require&amp;channel_binding=require"
       ou
       DATABASE_URL = "postgresql://user:senha@host/db?sslmode=require&channel_binding=require"

    2) [database]
       url = "postgresql://user:senha@host/db?sslmode=require&channel_binding=require"

    3) [database]
       host = "..."
       dbname = "..."
       user = "..."
       password = "..."
       port = 5432
       sslmode = "require"

    4) [connections.postgresql]
       host = "..."
       database = "..."
       username = "..."
       password = "..."
       port = 5432
    """
    for key in ["DATABASE_URL", "POSTGRES_URL", "NEON_DATABASE_URL"]:
        value = _secrets_get(key)
        if value:
            conn = _connect_from_url(value)
            if conn is not None:
                return conn

    for bloco in [("database",), ("postgres",), ("postgresql",), ("connections", "postgresql"), ("connections", "neon")]:
        cfg = _secrets_get(*bloco)
        conn = _connect_from_mapping(cfg)
        if conn is not None:
            return conn

    for key in ["DATABASE_URL", "POSTGRES_URL", "NEON_DATABASE_URL"]:
        value = os.getenv(key)
        if value:
            conn = _connect_from_url(value)
            if conn is not None:
                return conn

    raise RuntimeError(
        "Conexão do banco não encontrada. Configure DATABASE_URL ou o bloco [database] em secrets."
    )


# ============================================================
# Inicialização / migração simples
# ============================================================

def init_consolidados_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS consolidados (
                    consolidado_id SERIAL PRIMARY KEY,
                    nome_arquivo TEXT NOT NULL,
                    arquivo_bytes BYTEA NOT NULL,
                    data_processada DATE NOT NULL,
                    ano INTEGER NOT NULL,
                    mes INTEGER NOT NULL,
                    data_geracao TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_consolidados_data
                ON consolidados (data_processada, ano, mes);
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_consolidados_geracao
                ON consolidados (data_geracao DESC);
                """
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _normalizar_data_processada(valor):
    if valor is None:
        raise ValueError("data_processada não informada.")

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    data = pd.to_datetime(valor, dayfirst=True, errors="coerce")
    if pd.isna(data):
        raise ValueError(f"data_processada inválida: {valor}")
    return data.date()


def _bytes_do_arquivo(arquivo):
    if arquivo is None:
        raise ValueError("arquivo_excel/arquivo_bytes não informado.")

    if isinstance(arquivo, bytes):
        return arquivo

    if isinstance(arquivo, bytearray):
        return bytes(arquivo)

    if isinstance(arquivo, BytesIO):
        pos = arquivo.tell()
        arquivo.seek(0)
        dados = arquivo.read()
        arquivo.seek(pos)
        return dados

    if hasattr(arquivo, "getvalue"):
        return arquivo.getvalue()

    if hasattr(arquivo, "read"):
        pos = None
        try:
            pos = arquivo.tell()
            arquivo.seek(0)
        except Exception:
            pass
        dados = arquivo.read()
        if pos is not None:
            try:
                arquivo.seek(pos)
            except Exception:
                pass
        return dados

    raise ValueError("Tipo de arquivo não suportado para salvamento no banco.")


# ============================================================
# Regra principal: substituir consolidado da mesma data
# ============================================================

def _excluir_mesma_data(cur, data_processada, ano, mes):
    """
    Remove consolidados antigos da mesma data antes de inserir o novo.
    Assim o sistema mantém apenas o consolidado mais recente para a data.
    """
    cur.execute(
        """
        DELETE FROM consolidados
        WHERE data_processada = %s
          AND ano = %s
          AND mes = %s;
        """,
        (data_processada, int(ano), int(mes)),
    )


def salvar_consolidado(nome_arquivo, arquivo_bytes, ano, mes, data_processada):
    init_consolidados_db()
    data_proc = _normalizar_data_processada(data_processada)
    dados = _bytes_do_arquivo(arquivo_bytes)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            _excluir_mesma_data(cur, data_proc, int(ano), int(mes))
            cur.execute(
                """
                INSERT INTO consolidados (
                    nome_arquivo,
                    arquivo_bytes,
                    data_processada,
                    ano,
                    mes,
                    data_geracao
                )
                VALUES (%s, %s, %s, %s, %s, NOW())
                RETURNING consolidado_id;
                """,
                (nome_arquivo, psycopg2.Binary(dados), data_proc, int(ano), int(mes)),
            )
            consolidado_id = cur.fetchone()[0]
        conn.commit()
        return consolidado_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def salvar_resultados_consolidados_no_banco(resultados):
    """
    Salva a lista de consolidados gerados pela página de Consolidação.

    Para cada data_processada, exclui o consolidado antigo da mesma data
    e grava o novo consolidado.
    """
    init_consolidados_db()
    ids_criados = []

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for resultado in resultados:
                data_proc = _normalizar_data_processada(resultado.get("data_processada"))
                ano = int(data_proc.year)
                mes = int(data_proc.month)

                nome_arquivo = resultado.get("nome_arquivo_final") or resultado.get("nome_arquivo")
                if not nome_arquivo:
                    nome_arquivo = f"Resumo Gerencial CN - {data_proc.strftime('%d.%m.%Y')}.xlsx"

                arquivo = resultado.get("arquivo_excel") or resultado.get("arquivo_bytes") or resultado.get("arquivo")
                dados = _bytes_do_arquivo(arquivo)

                _excluir_mesma_data(cur, data_proc, ano, mes)

                cur.execute(
                    """
                    INSERT INTO consolidados (
                        nome_arquivo,
                        arquivo_bytes,
                        data_processada,
                        ano,
                        mes,
                        data_geracao
                    )
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    RETURNING consolidado_id;
                    """,
                    (nome_arquivo, psycopg2.Binary(dados), data_proc, ano, mes),
                )
                ids_criados.append(cur.fetchone()[0])
        conn.commit()
        return ids_criados
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================
# Consultas usadas pelo Dashboard Consolidado
# ============================================================

def listar_consolidados():
    init_consolidados_db()
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    consolidado_id,
                    nome_arquivo,
                    data_processada,
                    ano,
                    mes,
                    data_geracao
                FROM consolidados
                ORDER BY data_processada DESC, data_geracao DESC, consolidado_id DESC;
                """
            )
            rows = cur.fetchall()
        return pd.DataFrame(rows)
    finally:
        conn.close()


def carregar_arquivo_consolidado(consolidado_id):
    init_consolidados_db()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT nome_arquivo, arquivo_bytes
                FROM consolidados
                WHERE consolidado_id = %s;
                """,
                (int(consolidado_id),),
            )
            row = cur.fetchone()

        if row is None:
            return None, None

        nome_arquivo, arquivo_bytes = row
        return nome_arquivo, bytes(arquivo_bytes)
    finally:
        conn.close()


def excluir_consolidado(consolidado_id):
    init_consolidados_db()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM consolidados WHERE consolidado_id = %s;", (int(consolidado_id),))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================
# Limpeza única de duplicados antigos já existentes
# ============================================================

def limpar_duplicados_consolidados():
    """
    Remove duplicados antigos já existentes no banco.
    Mantém apenas o mais recente por data_processada + ano + mes.
    Esta função NÃO é chamada automaticamente.
    """
    init_consolidados_db()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM consolidados c
                USING consolidados c2
                WHERE c.data_processada = c2.data_processada
                  AND c.ano = c2.ano
                  AND c.mes = c2.mes
                  AND (
                        c.data_geracao < c2.data_geracao
                        OR (c.data_geracao = c2.data_geracao AND c.consolidado_id < c2.consolidado_id)
                  );
                """
            )
            removidos = cur.rowcount
        conn.commit()
        return removidos
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
