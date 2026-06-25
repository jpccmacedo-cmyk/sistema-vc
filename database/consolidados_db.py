import os
import html
from datetime import datetime, date
from io import BytesIO
from urllib.parse import urlparse, unquote

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

try:
    import streamlit as st
except Exception:
    st = None


# ============================================================
# Conexão com PostgreSQL / Neon
# ============================================================

def _secrets_get(*keys):
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
    if url is None:
        return None
    url = str(url).strip().strip('"').strip("'").strip()
    url = html.unescape(url)  # corrige &amp; para &
    url = url.replace("postgresql+psycopg2://", "postgresql://")
    url = url.replace("postgres+psycopg2://", "postgresql://")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def _connect_from_mapping(cfg):
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

    raise RuntimeError("Conexão do banco não encontrada. Configure DATABASE_URL ou [database] em secrets.")


# ============================================================
# Descoberta automática da tabela correta
# ============================================================

DEFAULT_SCHEMA = "public"
DEFAULT_TABLE = "consolidados"

COLUMN_CANDIDATES = {
    "id": ["consolidado_id", "id", "arquivo_id"],
    "nome": ["nome_arquivo", "arquivo_nome", "nome", "nome_final", "nome_arquivo_final", "filename"],
    "bytes": ["arquivo_bytes", "arquivo", "arquivo_excel", "conteudo_arquivo", "conteudo", "file_bytes", "dados", "blob"],
    "data": ["data_processada", "data", "data_ref", "data_referencia", "dt_processada"],
    "ano": ["ano", "year"],
    "mes": ["mes", "month"],
    "geracao": ["data_geracao", "created_at", "criado_em", "data_criacao", "updated_at", "dt_geracao"],
}


def _get_columns(conn, schema_name, table_name):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s;
            """,
            (schema_name, table_name),
        )
        return [row["column_name"] for row in cur.fetchall()]


def _row_count(conn, schema_name, table_name):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}.{}").format(sql.Identifier(schema_name), sql.Identifier(table_name)))
        return int(cur.fetchone()[0])


def _map_columns(columns):
    lower_to_real = {c.lower(): c for c in columns}
    mapping = {}
    for logical, candidates in COLUMN_CANDIDATES.items():
        for candidate in candidates:
            if candidate.lower() in lower_to_real:
                mapping[logical] = lower_to_real[candidate.lower()]
                break
    return mapping


def _is_compatible(mapping):
    return all(k in mapping for k in ["id", "nome", "bytes", "data", "ano", "mes"])


def _ensure_default_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS public.consolidados (
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
            ON public.consolidados (data_processada, ano, mes);
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_consolidados_geracao
            ON public.consolidados (data_geracao DESC);
            """
        )
    conn.commit()


def _descobrir_tabela_consolidados(conn):
    """
    Evita o problema de criar/usar uma tabela vazia se os dados antigos estiverem
    em outra tabela compatível. Procura tabelas com 'consolid' no nome e escolhe
    a compatível com mais registros.
    """
    table_override = None
    if st is not None:
        try:
            table_override = st.secrets.get("CONSOLIDADOS_TABLE")
        except Exception:
            table_override = None
    table_override = table_override or os.getenv("CONSOLIDADOS_TABLE")

    candidates = []
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT IN ('pg_catalog', 'information_schema')
              AND table_name ILIKE %s;
            """,
            ("%consolid%",),
        )
        rows = cur.fetchall()

    if table_override:
        if "." in str(table_override):
            schema_name, table_name = str(table_override).split(".", 1)
        else:
            schema_name, table_name = DEFAULT_SCHEMA, str(table_override)
        rows = [{"table_schema": schema_name, "table_name": table_name}] + rows

    for row in rows:
        schema_name = row["table_schema"]
        table_name = row["table_name"]
        try:
            columns = _get_columns(conn, schema_name, table_name)
            mapping = _map_columns(columns)
            compatible = _is_compatible(mapping)
            count = _row_count(conn, schema_name, table_name) if compatible else 0
            score = 0
            if compatible:
                score += 1000
            if count > 0:
                score += 100000 + count
            if table_name == DEFAULT_TABLE:
                score += 100
            if table_override and table_name == str(table_override).split(".")[-1]:
                score += 10000
            candidates.append({
                "schema": schema_name,
                "table": table_name,
                "columns": columns,
                "mapping": mapping,
                "compatible": compatible,
                "count": count,
                "score": score,
            })
        except Exception:
            continue

    compatible_candidates = [c for c in candidates if c["compatible"]]
    if compatible_candidates:
        compatible_candidates.sort(key=lambda c: c["score"], reverse=True)
        return compatible_candidates[0]

    _ensure_default_table(conn)
    columns = _get_columns(conn, DEFAULT_SCHEMA, DEFAULT_TABLE)
    return {
        "schema": DEFAULT_SCHEMA,
        "table": DEFAULT_TABLE,
        "columns": columns,
        "mapping": _map_columns(columns),
        "compatible": True,
        "count": _row_count(conn, DEFAULT_SCHEMA, DEFAULT_TABLE),
        "score": 0,
    }


def _ident(schema_name, table_name):
    return sql.SQL("{}.{}").format(sql.Identifier(schema_name), sql.Identifier(table_name))


# ============================================================
# Inicialização
# ============================================================

def init_consolidados_db():
    conn = get_connection()
    try:
        # Não força usar public.consolidados se existir outra tabela compatível com dados.
        _descobrir_tabela_consolidados(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================
# Utilitários
# ============================================================

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


def _excluir_mesma_data(cur, cfg, data_processada, ano, mes):
    m = cfg["mapping"]
    cur.execute(
        sql.SQL("DELETE FROM {} WHERE {} = %s AND {} = %s AND {} = %s").format(
            _ident(cfg["schema"], cfg["table"]),
            sql.Identifier(m["data"]),
            sql.Identifier(m["ano"]),
            sql.Identifier(m["mes"]),
        ),
        (data_processada, int(ano), int(mes)),
    )


def _insert_consolidado(cur, cfg, nome_arquivo, dados, data_proc, ano, mes):
    m = cfg["mapping"]
    cols = [m["nome"], m["bytes"], m["data"], m["ano"], m["mes"]]
    vals = [nome_arquivo, psycopg2.Binary(dados), data_proc, int(ano), int(mes)]

    if "geracao" in m:
        cols.append(m["geracao"])
        # usa NOW() direto no SQL para data de geração
        placeholders = [sql.Placeholder()] * 5 + [sql.SQL("NOW()")]
    else:
        placeholders = [sql.Placeholder()] * 5

    query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING {}").format(
        _ident(cfg["schema"], cfg["table"]),
        sql.SQL(", ").join(sql.Identifier(c) for c in cols),
        sql.SQL(", ").join(placeholders),
        sql.Identifier(m["id"]),
    )
    cur.execute(query, vals)
    return cur.fetchone()[0]


# ============================================================
# Salvamento com substituição por data
# ============================================================

def salvar_consolidado(nome_arquivo, arquivo_bytes, ano, mes, data_processada):
    data_proc = _normalizar_data_processada(data_processada)
    dados = _bytes_do_arquivo(arquivo_bytes)
    conn = get_connection()
    try:
        cfg = _descobrir_tabela_consolidados(conn)
        with conn.cursor() as cur:
            _excluir_mesma_data(cur, cfg, data_proc, int(ano), int(mes))
            consolidado_id = _insert_consolidado(cur, cfg, nome_arquivo, dados, data_proc, int(ano), int(mes))
        conn.commit()
        return consolidado_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def salvar_resultados_consolidados_no_banco(resultados):
    ids_criados = []
    conn = get_connection()
    try:
        cfg = _descobrir_tabela_consolidados(conn)
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

                # Regra principal: remove o antigo da mesma data e salva o novo.
                _excluir_mesma_data(cur, cfg, data_proc, ano, mes)
                ids_criados.append(_insert_consolidado(cur, cfg, nome_arquivo, dados, data_proc, ano, mes))
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
    conn = get_connection()
    try:
        cfg = _descobrir_tabela_consolidados(conn)
        m = cfg["mapping"]
        geracao_expr = sql.Identifier(m["geracao"]) if "geracao" in m else sql.SQL("NULL")
        query = sql.SQL(
            """
            SELECT
                {} AS consolidado_id,
                {} AS nome_arquivo,
                {} AS data_processada,
                {} AS ano,
                {} AS mes,
                {} AS data_geracao
            FROM {}
            ORDER BY {} DESC, {} DESC, {} DESC
            """
        ).format(
            sql.Identifier(m["id"]),
            sql.Identifier(m["nome"]),
            sql.Identifier(m["data"]),
            sql.Identifier(m["ano"]),
            sql.Identifier(m["mes"]),
            geracao_expr,
            _ident(cfg["schema"], cfg["table"]),
            sql.Identifier(m["data"]),
            geracao_expr,
            sql.Identifier(m["id"]),
        )
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()
        return pd.DataFrame(rows)
    finally:
        conn.close()


def carregar_arquivo_consolidado(consolidado_id):
    conn = get_connection()
    try:
        cfg = _descobrir_tabela_consolidados(conn)
        m = cfg["mapping"]
        query = sql.SQL("SELECT {}, {} FROM {} WHERE {} = %s").format(
            sql.Identifier(m["nome"]),
            sql.Identifier(m["bytes"]),
            _ident(cfg["schema"], cfg["table"]),
            sql.Identifier(m["id"]),
        )
        with conn.cursor() as cur:
            cur.execute(query, (int(consolidado_id),))
            row = cur.fetchone()
        if row is None:
            return None, None
        nome_arquivo, arquivo_bytes = row
        return nome_arquivo, bytes(arquivo_bytes)
    finally:
        conn.close()


def excluir_consolidado(consolidado_id):
    conn = get_connection()
    try:
        cfg = _descobrir_tabela_consolidados(conn)
        m = cfg["mapping"]
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("DELETE FROM {} WHERE {} = %s").format(
                    _ident(cfg["schema"], cfg["table"]),
                    sql.Identifier(m["id"]),
                ),
                (int(consolidado_id),),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================
# Diagnóstico e limpeza
# ============================================================

def diagnosticar_tabelas_consolidados():
    """Retorna tabelas candidatas e contagens para diagnóstico."""
    conn = get_connection()
    try:
        rows_out = []
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                  AND table_schema NOT IN ('pg_catalog', 'information_schema')
                  AND table_name ILIKE %s
                ORDER BY table_schema, table_name;
                """,
                ("%consolid%",),
            )
            tables = cur.fetchall()
        for t in tables:
            schema_name = t["table_schema"]
            table_name = t["table_name"]
            columns = _get_columns(conn, schema_name, table_name)
            mapping = _map_columns(columns)
            compatible = _is_compatible(mapping)
            count = _row_count(conn, schema_name, table_name) if compatible else None
            rows_out.append({
                "schema": schema_name,
                "tabela": table_name,
                "linhas": count,
                "compatível": compatible,
                "colunas": ", ".join(columns),
            })
        return pd.DataFrame(rows_out)
    finally:
        conn.close()


def limpar_duplicados_consolidados():
    conn = get_connection()
    try:
        cfg = _descobrir_tabela_consolidados(conn)
        m = cfg["mapping"]
        if "geracao" not in m:
            return 0
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    """
                    DELETE FROM {} c
                    USING {} c2
                    WHERE c.{} = c2.{}
                      AND c.{} = c2.{}
                      AND c.{} = c2.{}
                      AND (
                            c.{} < c2.{}
                            OR (c.{} = c2.{} AND c.{} < c2.{})
                      )
                    """
                ).format(
                    _ident(cfg["schema"], cfg["table"]),
                    _ident(cfg["schema"], cfg["table"]),
                    sql.Identifier(m["data"]), sql.Identifier(m["data"]),
                    sql.Identifier(m["ano"]), sql.Identifier(m["ano"]),
                    sql.Identifier(m["mes"]), sql.Identifier(m["mes"]),
                    sql.Identifier(m["geracao"]), sql.Identifier(m["geracao"]),
                    sql.Identifier(m["geracao"]), sql.Identifier(m["geracao"]),
                    sql.Identifier(m["id"]), sql.Identifier(m["id"]),
                )
            )
            removidos = cur.rowcount
        conn.commit()
        return removidos
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
