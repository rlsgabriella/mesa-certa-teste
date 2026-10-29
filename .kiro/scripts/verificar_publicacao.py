#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Checagem segura e não destrutiva de segredos e riscos de publicação em arquivos modificados.

Usada pelos hooks `PostFileSave` e `PostFileCreate` (.kiro/hooks/) e também à mão. SOMENTE LEITURA:
- abre arquivos apenas para leitura; o único subprocesso é `git status --porcelain` e `git check-ignore`;
- nunca grava, move ou apaga arquivos (o autoteste grava só em uma pasta temporária própria);
- nunca imprime o valor de um segredo: mostra arquivo, linha e o tipo do achado.

Uso:
    py .kiro/scripts/verificar_publicacao.py --stdin            # hook: lê o JSON do evento no stdin
    py .kiro/scripts/verificar_publicacao.py --git              # arquivos modificados ou novos segundo o git
    py .kiro/scripts/verificar_publicacao.py caminho1 caminho2  # arquivos específicos
    py .kiro/scripts/verificar_publicacao.py --autoteste        # testa o próprio verificador em pasta temporária

Códigos de saída: 0 sem alerta (pode haver aviso ou info); 1 há ALERTA (aviso ao usuário; o hook não bloqueia nada); 2 erro de uso.
Para ignorar uma linha de propósito, inclua o texto `verificar-publicacao: ignorar` nela.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
LIMITE_BYTES = 2 * 1024 * 1024
EXT_BINARIAS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".db", ".sqlite", ".zip", ".pyc", ".ico"}
NOMES_CREDENCIAL = {"credentials.json", "secrets.json"}
EXT_CREDENCIAL = {".pem", ".key", ".pfx", ".p12"}
MARCA_IGNORAR = "verificar-publicacao: ignorar"
VALORES_NEUTROS = {"false", "true", "crypto", "null", "none"}

PADROES = [
    ("Bearer com valor literal", re.compile(r"Bearer\s+(?![<{$(\[])[A-Za-z0-9._\-]{10,}")),
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("chave privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("chave de nuvem (AKIA)", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("atribuição de segredo com valor literal", re.compile(
        r"(?i)(password|passwd|senha|secret|segredo|api[_-]?key|token)[\"']?\s*[:=]\s*[\"']?(?![<{$(\[])[A-Za-z0-9_\-./+=]{16,}")),
]


# ------------------------------------------------------------------ git (somente leitura)

def _git(args: list[str], raiz: Path):
    try:
        return subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None


def ignorado_pelo_git(caminho: Path, raiz: Path):
    """True se ignorado, False se não ignorado, None se não deu para saber."""
    r = _git(["check-ignore", "-q", "--", str(caminho)], raiz)
    if r is None:
        return None
    return {0: True, 1: False}.get(r.returncode)


def arquivos_do_git(raiz: Path) -> list[Path]:
    r = _git(["status", "--porcelain", "-z", "-uall"], raiz)
    if r is None or r.returncode != 0:
        return []
    partes = r.stdout.split("\0")
    saida, i = [], 0
    while i < len(partes):
        e = partes[i]
        i += 1
        if len(e) < 4:
            continue
        status, nome = e[:2], e[3:]
        if "R" in status or "C" in status:
            i += 1                      # o próximo item é o nome antigo
        if "D" in status:
            continue
        p = raiz / nome
        if p.is_file():
            saida.append(p)
    return saida


# ------------------------------------------------------------------ segredos conhecidos

def segredos_conhecidos(raiz: Path) -> dict[str, tuple[str, Path | None]]:
    """Valores a procurar: variáveis do .env e o token de teste do crm-mock.py. Retorna {rótulo: (valor, arquivo de origem)}."""
    achados: dict[str, tuple[str, Path | None]] = {}
    env = raiz / ".env"
    if env.is_file():
        for linha in env.read_text(encoding="utf-8", errors="ignore").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            k, v = linha.split("=", 1)
            v = v.strip().strip("\"'")
            if len(v) >= 8 and v.lower() not in VALORES_NEUTROS and not v.startswith(("<", "$")):
                achados[f"variável {k.strip()} do .env"] = (v, env)
    mock = raiz / "solucao" / "crm-mock-teste" / "crm-mock.py"
    if mock.is_file():
        m = re.search(r"TOKEN\s*=\s*[\"']([^\"']{8,})[\"']", mock.read_text(encoding="utf-8", errors="ignore"))
        if m:
            achados["token de teste do crm-mock.py"] = (m.group(1), mock)
    return achados


# ------------------------------------------------------------------ varredura

def varrer(caminho: Path, segredos: dict, raiz: Path) -> list[tuple[str, int, str]]:
    """Devolve [(nível, linha, descrição)]. Nunca inclui valores."""
    nome, ext = caminho.name, caminho.suffix.lower()
    if nome == ".env" or (nome.startswith(".env.") and nome != ".env.example"):
        ign = ignorado_pelo_git(caminho, raiz)
        if ign is False:
            return [("ALERTA", 0, "arquivo .env NÃO está ignorado pelo git: risco de publicar segredos")]
        if ign is None:
            return [("AVISO", 0, "arquivo .env: não foi possível confirmar se o git o ignora")]
        return [("INFO", 0, "arquivo .env ignorado pelo git (conteúdo não varrido); não incluir na entrega")]
    achados: list[tuple[str, int, str]] = []
    if nome in NOMES_CREDENCIAL or ext in EXT_CREDENCIAL:
        ign = ignorado_pelo_git(caminho, raiz)
        if ign is not True:
            achados.append(("ALERTA", 0, "arquivo de credencial fora do .gitignore"))
    if ext in EXT_BINARIAS:
        if ext in {".db", ".sqlite"}:
            achados.append(("AVISO", 0, "banco binário modificado: confira se não leva dados que não devem ser publicados"))
        else:
            achados.append(("AVISO", 0, "imagem ou binário não verificado: confira à mão dados pessoais e segredos visíveis"))
        return achados
    try:
        if caminho.stat().st_size > LIMITE_BYTES:
            return achados + [("AVISO", 0, "arquivo grande não varrido")]
        bruto = caminho.read_bytes()
    except OSError:
        return achados + [("AVISO", 0, "arquivo ilegível")]
    if b"\0" in bruto[:4096]:
        return achados + [("AVISO", 0, "binário não verificado")]
    texto = bruto.decode("utf-8", errors="ignore")
    for n, linha in enumerate(texto.splitlines(), 1):
        if MARCA_IGNORAR in linha:
            continue
        vistos = set()
        for rotulo, (valor, origem) in segredos.items():
            if valor in linha and not (origem and origem.resolve() == caminho.resolve()) and rotulo not in vistos:
                achados.append(("ALERTA", n, f"contém o valor de {rotulo}"))
                vistos.add(rotulo)
        for rotulo, rx in PADROES:
            if rx.search(linha) and rotulo not in vistos:
                achados.append(("ALERTA", n, rotulo))
                vistos.add(rotulo)
    return achados


def caminhos_do_stdin(texto: str, raiz: Path) -> list[Path]:
    """Extrai do JSON do evento qualquer valor que aponte para um arquivo existente (o nome do campo não é fixo)."""
    try:
        dados = json.loads(texto)
    except ValueError:
        return []
    base = raiz
    if isinstance(dados, dict) and isinstance(dados.get("cwd"), str) and os.path.isdir(dados["cwd"]):
        base = Path(dados["cwd"])
    achados: list[Path] = []

    def visita(v):
        if isinstance(v, dict):
            for x in v.values():
                visita(x)
        elif isinstance(v, list):
            for x in v:
                visita(x)
        elif isinstance(v, str) and 0 < len(v) < 500 and "\n" not in v:
            c = Path(v) if os.path.isabs(v) else base / v
            try:
                if c.is_file() and c not in achados:
                    achados.append(c)
            except OSError:
                pass

    visita(dados)
    return achados


def verificar(caminhos: list[Path], raiz: Path) -> list[dict]:
    segredos = segredos_conhecidos(raiz)
    resultado = []
    for c in caminhos:
        for nivel, linha, desc in varrer(c, segredos, raiz):
            try:
                rel = str(c.resolve().relative_to(raiz.resolve()))
            except ValueError:
                rel = str(c)
            resultado.append({"nivel": nivel, "arquivo": rel.replace("\\", "/"), "linha": linha, "descricao": desc})
    return resultado


# ------------------------------------------------------------------ autoteste

def sha_pasta(pasta: Path) -> dict[str, str]:
    return {str(p.relative_to(pasta)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(pasta.rglob("*")) if p.is_file()}


def autoteste() -> int:
    falhas, linhas = 0, []

    def checa(descricao: str, ok: bool):
        nonlocal falhas
        falhas += 0 if ok else 1
        linhas.append(f"  [{'ok' if ok else 'FALHOU'}] {descricao}")

    with tempfile.TemporaryDirectory() as t:
        pasta = Path(t)
        valor_env = "".join(chr(97 + (i * 7) % 26) for i in range(18)) + "9Q"            # valor sintético
        (pasta / ".env").write_text(f"SEGREDO_DE_TESTE={valor_env}\nFLAG=false\n", encoding="utf-8")
        (pasta / "limpo.md").write_text("Use `Bearer <token>` e `segredo = os.environ.get('X')`.\nNada aqui.\n", encoding="utf-8")
        (pasta / "bearer.txt").write_text("Authorization: " + "Bear" + "er " + "a" * 24 + "\n", encoding="utf-8")
        (pasta / "jwt.json").write_text('{"t": "' + "ey" + "J" + "a" * 12 + "." + "b" * 12 + '"}\n', encoding="utf-8")
        (pasta / "chave.py").write_text("api_" + "key = '" + "Z" * 20 + "'\n", encoding="utf-8")
        (pasta / "vazamento.md").write_text(f"o valor é {valor_env} por engano\n", encoding="utf-8")
        (pasta / "ignorada.md").write_text("api_" + "key = '" + "Z" * 20 + "'  # " + MARCA_IGNORAR + "\n", encoding="utf-8")
        (pasta / "print.png").write_bytes(b"\x89PNG\r\n\x1a\n\0\0")
        antes = sha_pasta(pasta)
        r = verificar(sorted(p for p in pasta.iterdir() if p.is_file()), pasta)
        por_arq = {}
        for x in r:
            por_arq.setdefault(x["arquivo"], []).append(x)
        niveis = lambda a: {x["nivel"] for x in por_arq.get(a, [])}
        checa("texto limpo não gera alerta", "ALERTA" not in niveis("limpo.md"))
        checa("Bearer literal gera alerta", "ALERTA" in niveis("bearer.txt"))
        checa("JWT gera alerta", "ALERTA" in niveis("jwt.json"))
        checa("atribuição de chave gera alerta", "ALERTA" in niveis("chave.py"))
        checa("valor vindo do .env gera alerta", "ALERTA" in niveis("vazamento.md"))
        checa("linha marcada para ignorar não gera alerta", "ALERTA" not in niveis("ignorada.md"))
        checa("imagem vira aviso, não alerta", niveis("print.png") == {"AVISO"})
        checa(".env não tem o conteúdo varrido nem o valor impresso", all(valor_env not in json.dumps(x) for x in r))
        # stdin com campo de nome desconhecido
        payload = json.dumps({"hook_event_name": "PostFileSave", "cwd": str(pasta), "campo_qualquer": "bearer.txt", "outro": {"x": ["jwt.json"]}})
        achados = {p.name for p in caminhos_do_stdin(payload, pasta)}
        checa("caminhos extraídos do stdin sem depender do nome do campo", achados == {"bearer.txt", "jwt.json"})
        checa("stdin inválido não quebra", caminhos_do_stdin("não é json", pasta) == [])
        checa("nenhum arquivo foi alterado, criado ou apagado", sha_pasta(pasta) == antes)
    # o próprio script e a skill não devem acusar
    proprios = [Path(__file__), RAIZ / ".kiro" / "skills" / "auditoria-workflow-crm" / "scripts" / "inspecionar_workflow.py"]
    proprios = [p for p in proprios if p.is_file()]
    res = verificar(proprios, RAIZ)
    checa("scripts do pacote .kiro não têm alerta", not any(x["nivel"] == "ALERTA" for x in res))
    print("Autoteste do verificador:\n" + "\n".join(linhas))
    print(f"Resultado: {'APROVADO' if not falhas else str(falhas) + ' falha(s)'}")
    return 1 if falhas else 0


# ------------------------------------------------------------------ main

def main(argv=None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Procura segredos e riscos de publicação (somente leitura).")
    ap.add_argument("caminhos", nargs="*")
    ap.add_argument("--stdin", action="store_true", help="Lê o JSON do evento do hook no stdin.")
    ap.add_argument("--git", action="store_true", help="Varre arquivos modificados ou novos segundo o git.")
    ap.add_argument("--json", action="store_true", help="Saída em JSON.")
    ap.add_argument("--autoteste", action="store_true")
    a = ap.parse_args(argv)
    if a.autoteste:
        return autoteste()
    alvo: list[Path] = [Path(c) for c in a.caminhos]
    if a.stdin and not sys.stdin.isatty():
        alvo += caminhos_do_stdin(sys.stdin.read(), RAIZ)
    if a.git or not alvo:
        alvo += arquivos_do_git(RAIZ)
    alvo = [p for p in dict.fromkeys(alvo) if p.is_file()]
    achados = verificar(alvo, RAIZ)
    alertas = [x for x in achados if x["nivel"] == "ALERTA"]
    if a.json:
        print(json.dumps({"arquivos": len(alvo), "achados": achados}, ensure_ascii=False, indent=2))
    elif achados:
        ordem = {"ALERTA": 0, "AVISO": 1, "INFO": 2}
        for x in sorted(achados, key=lambda x: ordem[x["nivel"]]):
            onde = f"{x['arquivo']}:{x['linha']}" if x["linha"] else x["arquivo"]
            print(f"[{x['nivel']}] {onde}: {x['descricao']}", file=sys.stderr if alertas else sys.stdout)
    if not alertas and not a.json:
        print(f"verificar_publicacao: {len(alvo)} arquivo(s) verificado(s), sem alerta.")
    elif alertas and not a.json:
        print(f"verificar_publicacao: {len(alertas)} ALERTA(s) em {len(alvo)} arquivo(s). Nada foi alterado; revise antes de publicar.", file=sys.stderr)
    return 1 if alertas else 0


if __name__ == "__main__":
    raise SystemExit(main())
