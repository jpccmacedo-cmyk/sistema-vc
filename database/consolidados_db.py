import os
from datetime import datetime, date
from io import BytesIO

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

try:
    import streamlit as st
except Exception:  # permite importar fora do Streamlit
    st = None


# ============================================================
# Conexão com PostgreSQL / Neon
# ============================================================

def _get_database_url():
    """
    Procura a URL do banco em st.secrets ou variáveis de ambiente.

    Formatos aceitos no Streamlit Secrets:

    DATABASE_URL = "postgresql://..."

    ou

    [database]
    url = "postgresql://..."
    """
    if st is not None:
        try:
            if "DATABASE_URL" in st.secrets:
                return st.secrets["DATABASE_URL"]
        except Exception:
            pass

        try:
            if "database" in st.secrets and "url" in st.secrets["database"]:
                return st.secrets["database"]["url"]
        except Exception:
            pass

    for var in ["DATABASE_URL", "POSTGRES_URL", "NEON_DATABASE_URL"]:
        valor = os.getenv(var)
        if valor:
            return valor

    raise RuntimeError(
        "DATABASE_URL não encontrada. Configure a conexão do Neon em st.secrets ou variável de ambiente."
    )


def get_connection():
    url = _get_database_url()
    # Neon normalmente exige SSL. Se a URL já tiver sslmode, o psycopg2 respeita.
    if "sslmode=" not in url:
        return psycopg2.connect(url, sslmode="require")
    return psycopg2.connect(url)


# ============================================================
# Inicialização / migração simples
# ============================================================

def init_consolidados_db():
    """
    Cria a tabela de consolidados caso não exista.

    Regra atual:
    - A tabela pode receber vários meses/datas.
    - Para a mesma data_processada + ano + mes, a função de salvamento apaga o antigo
      e mantém somente o consolidado mais recente.
    """
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
    Essa é a regra que garante que o sistema considere apenas o mais recente.
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
    """
    Salva um único consolidado.

    Antes de salvar, exclui qualquer consolidado antigo com a mesma:
    - data_processada;
    - ano;
    - mes.
    """
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
                (
                    nome_arquivo,
                    psycopg2.Binary(dados),
                    data_proc,
                    int(ano),
                    int(mes),
                ),
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
    Salva a lista de consolidados gerados na página de Consolidação.

    Espera itens no formato gerado por processar_data/processar_multiplas_datas:

    {
        "arquivo_excel": BytesIO,
        "nome_arquivo_final": "Resumo Gerencial CN - 24.06.2026.xlsx",
        "data_processada": date(2026, 6, 24),
        ...
    }

    Para cada resultado, exclui o consolidado anterior da mesma data e salva o novo.
    Retorna a lista de IDs criados.
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

                # Ponto principal da correção:
                # remove o antigo da mesma data antes de gravar o novo.
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
                    (
                        nome_arquivo,
                        psycopg2.Binary(dados),
                        data_proc,
                        ano,
                        mes,
                    ),
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
            cur.execute(
                """
                DELETE FROM consolidados
                WHERE consolidado_id = %s;
                """,
                (int(consolidado_id),),
            )
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

    Mantém apenas o registro mais recente para cada combinação:
    data_processada + ano + mes.

    Você pode chamar essa função uma vez, por exemplo em uma página admin,
    ou executar manualmente em um script separado.
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
