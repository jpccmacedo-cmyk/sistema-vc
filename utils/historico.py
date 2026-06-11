from pathlib import Path
from datetime import datetime
from io import BytesIO
import json
import re

PASTA_DADOS = Path("data")
PASTA_CONSOLIDADOS = PASTA_DADOS / "consolidados"
ARQUIVO_HISTORICO = PASTA_DADOS / "historico_consolidados.json"


def preparar_pastas_historico():
    PASTA_CONSOLIDADOS.mkdir(parents=True, exist_ok=True)


def limpar_nome_arquivo(nome: str) -> str:
    nome = str(nome).strip()
    nome = re.sub(r'[\\/:*?"<>|]', "", nome)
    return nome or f"consolidado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"


def carregar_historico_consolidados():
    preparar_pastas_historico()

    if not ARQUIVO_HISTORICO.exists():
        return []

    try:
        with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def salvar_historico_consolidados(historico):
    preparar_pastas_historico()

    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)


def registrar_arquivo_consolidado_bytes(
    nome_arquivo: str,
    conteudo_bytes: bytes,
    origem: str = "sistema"
):
    preparar_pastas_historico()

    historico = carregar_historico_consolidados()

    nome_limpo = limpar_nome_arquivo(nome_arquivo)
    caminho_saida = PASTA_CONSOLIDADOS / nome_limpo

    if caminho_saida.exists():
        stem = caminho_saida.stem
        suffix = caminho_saida.suffix
        caminho_saida = PASTA_CONSOLIDADOS / f"{stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
        nome_limpo = caminho_saida.name

    with open(caminho_saida, "wb") as f:
        f.write(conteudo_bytes)

    registro = {
        "nome_arquivo": nome_limpo,
        "caminho": str(caminho_saida),
        "data_geracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "origem": origem,
    }

    historico.append(registro)
    salvar_historico_consolidados(historico)

    return registro


def salvar_resultados_no_historico(resultados):
    registros = []

    for resultado in resultados:
        nome_arquivo = resultado["nome_arquivo_final"]
        arquivo_excel = resultado["arquivo_excel"]

        if isinstance(arquivo_excel, BytesIO):
            arquivo_excel.seek(0)
            conteudo = arquivo_excel.getvalue()
        else:
            arquivo_excel.seek(0)
            conteudo = arquivo_excel.read()

        registro = registrar_arquivo_consolidado_bytes(
            nome_arquivo=nome_arquivo,
            conteudo_bytes=conteudo,
            origem="consolidacao"
        )

        registros.append(registro)

    return registros


def remover_registro_historico(nome_arquivo: str):
    historico = carregar_historico_consolidados()

    novo = [
        item for item in historico
        if item.get("nome_arquivo") != nome_arquivo
    ]

    salvar_historico_consolidados(novo)
