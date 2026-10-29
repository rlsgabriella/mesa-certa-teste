#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeção estática, somente leitura, de um workflow exportado do n8n (JSON).

Apoia a skill `auditoria-workflow-crm`. Não executa o workflow, não chama CRM nem n8n, não grava nada.
Não imprime valores de segredo: só o tipo do achado e o nome do nó.

Uso:
    py inspecionar_workflow.py solucao/workflows/wf01-recebimento-cadastro-leads.json [outros.json] [--json] [--strict]

Saída: inventário (nós, gatilhos, credenciais por referência), alcance do grafo, saídas de erro, respostas ao
remetente, chamadas HTTP, SQL com ou sem proteção contra duplicidade, Code nodes, referências a nós inexistentes e
sinais de segredo. Achados: [ALERTA] pede ação, [AVISO] pede conferência, [INFO] é contexto.
`--strict` sai com código 1 se houver ALERTA.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

PADROES_SEGREDO = [
    ("Bearer literal", re.compile(r"Bearer\s+(?![<{$])[A-Za-z0-9._\-]{10,}")),
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("chave privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("atribuição de segredo", re.compile(
        r"(?i)(password|passwd|senha|secret|segredo|api[_-]?key|token)[\"']?\s*[:=]\s*[\"']?(?![<{$(\[])[A-Za-z0-9_\-./+=]{16,}")),
]
REF_NO = re.compile(r"\$\(\s*['\"]([^'\"]+)['\"]\s*\)")
TIPOS_SQL_HINT = ("sqlite", "postgres", "mysql", "mssql", "sql")


def textos(valor, caminho=""):
    """Percorre o JSON devolvendo (caminho, texto) de todo valor string."""
    if isinstance(valor, str):
        yield caminho, valor
    elif isinstance(valor, dict):
        for k, v in valor.items():
            yield from textos(v, f"{caminho}.{k}" if caminho else k)
    elif isinstance(valor, list):
        for i, v in enumerate(valor):
            yield from textos(v, f"{caminho}[{i}]")


def alcance(inicios, conexoes):
    visto, pilha = set(), list(inicios)
    while pilha:
        n = pilha.pop()
        if n in visto:
            continue
        visto.add(n)
        for saida in conexoes.get(n, {}).get("main", []):
            for d in saida or []:
                pilha.append(d["node"])
    return visto


def sql_statements(consulta: str):
    return [s.strip() for s in re.split(r";\s*", consulta) if s.strip()]


def inspecionar(wf: dict) -> dict:
    nos = {n["name"]: n for n in wf.get("nodes", [])}
    con = wf.get("connections", {})
    achados: list[tuple[str, str, str]] = []

    def a(nivel, titulo, detalhe=""):
        achados.append((nivel, titulo, detalhe))

    tipos = collections.Counter(n["type"] for n in nos.values())
    gatilhos = [n for n in nos.values() if n["type"].endswith("Trigger") or n["type"].endswith(".webhook")]
    if not gatilhos:
        a("ALERTA", "Workflow sem gatilho")
    for g in gatilhos:
        p = g.get("parameters", {})
        if g["type"].endswith(".webhook"):
            raw = bool(p.get("options", {}).get("rawBody"))
            a("INFO", f"Webhook '{g['name']}'", f"método {p.get('httpMethod', 'GET')}, caminho {p.get('path')}, responseMode {p.get('responseMode', 'onReceived')}, rawBody {'sim' if raw else 'NÃO'}")
            if not raw:
                a("AVISO", "Webhook sem corpo bruto (rawBody)", "assinatura calculada sobre JSON reserializado pode não bater")
        elif g["type"].endswith("manualTrigger"):
            a("AVISO", f"Gatilho manual '{g['name']}'", "o workflow não roda sozinho; a rotina depende de alguém clicar em executar")
        else:
            a("INFO", f"Gatilho '{g['name']}'", g["type"].split(".")[-1])

    # credenciais por referência
    creds = collections.defaultdict(list)
    for n in nos.values():
        for tipo, ref in (n.get("credentials") or {}).items():
            creds[f"{tipo} ({ref.get('name', '?')}, id {ref.get('id', '?')})"].append(n["name"])
    # pinData e nós desabilitados
    pin = list((wf.get("pinData") or {}).keys())
    if pin:
        a("ALERTA", "pinData presente", f"nós com dados fixos de teste: {', '.join(pin)}")
    desab = [n["name"] for n in nos.values() if n.get("disabled")]
    if desab:
        a("AVISO", "Nós desabilitados", ", ".join(desab))
    if wf.get("active"):
        a("INFO", "Workflow ativo")

    # grafo
    for src, d in con.items():
        if src not in nos:
            a("ALERTA", "Conexão com origem inexistente", src)
        for saida in d.get("main", []):
            for dest in saida or []:
                if dest["node"] not in nos:
                    a("ALERTA", "Conexão para nó inexistente", f"{src} -> {dest['node']}")
    ini = [g["name"] for g in gatilhos]
    visto = alcance(ini, con)
    soltos = [n for n in nos if n not in visto and not nos[n]["type"].endswith("stickyNote")]
    if soltos:
        a("AVISO", "Nós inalcançáveis a partir do gatilho", ", ".join(soltos))

    # saídas de erro, retry
    for n in nos.values():
        if n.get("onError") == "continueErrorOutput":
            saidas = con.get(n["name"], {}).get("main", [])
            if len(saidas) < 2 or not saidas[1]:
                a("ALERTA", f"'{n['name']}' tem saída de erro habilitada e sem destino", "falha seria engolida")
        if n.get("onError") == "continueRegularOutput":
            a("AVISO", f"'{n['name']}' continua mesmo com erro", "a falha segue como se fosse sucesso")
        if n["type"].endswith("httpRequest") and not n.get("retryOnFail"):
            a("AVISO", f"'{n['name']}' (HTTP) sem retry configurado", "429/500/timeout dependem de outro tratamento")

    # respostas ao remetente
    http_ext = [n["name"] for n in nos.values() if n["type"].endswith("httpRequest")]
    for n in nos.values():
        if n["type"].endswith("respondToWebhook"):
            cod = n.get("parameters", {}).get("options", {}).get("responseCode", 200)
            apos = [h for h in http_ext if h in alcance([n["name"]], con) and h != n["name"]]
            a("INFO", f"Resposta '{n['name']}'", f"HTTP {cod}; chamadas HTTP depois dela: {', '.join(apos) if apos else 'nenhuma'}")
    codigos = {n.get("parameters", {}).get("options", {}).get("responseCode", 200) for n in nos.values() if n["type"].endswith("respondToWebhook")}
    if any(g["type"].endswith(".webhook") for g in gatilhos) and codigos and not any(str(c).startswith("4") for c in codigos):
        a("AVISO", "Nenhuma resposta 4xx para entrada inválida", "o remetente pode reenviar indefinidamente")

    # HTTP / CRM
    for n in nos.values():
        if not n["type"].endswith("httpRequest"):
            continue
        p = n.get("parameters", {})
        host = urlparse(str(p.get("url", ""))).netloc or "(expressão)"
        auth = p.get("authentication", "none")
        a("INFO", f"HTTP '{n['name']}'", f"{p.get('method', 'GET')} {host}, autenticação {auth}")
        cab = (p.get("headerParameters") or {}).get("parameters", [])
        for h in cab:
            if str(h.get("name", "")).lower() == "authorization" and not str(h.get("value", "")).startswith("="):
                a("ALERTA", f"'{n['name']}' com cabeçalho Authorization literal", "usar credencial do n8n")
        if auth == "none" and host not in ("(expressão)",) and "127.0.0.1" not in host and "localhost" not in host:
            a("AVISO", f"'{n['name']}' chama {host} sem autenticação")

    # SQL
    for n in nos.values():
        p = n.get("parameters", {})
        q = p.get("query")
        if not isinstance(q, str) or not (any(t in n["type"].lower() for t in TIPOS_SQL_HINT) or "select" in q.lower()):
            continue
        for s in sql_statements(q):
            tipo = s.split()[0].upper()
            if tipo == "INSERT":
                if not re.search(r"NOT\s+EXISTS|ON\s+CONFLICT|OR\s+IGNORE|OR\s+REPLACE", s, re.I):
                    a("ALERTA", f"'{n['name']}': INSERT sem proteção contra duplicidade", "repetir o evento grava duas vezes")
                else:
                    a("INFO", f"'{n['name']}': INSERT idempotente")
            elif tipo in ("UPDATE", "DELETE"):
                if not re.search(r"\bWHERE\b", s, re.I):
                    a("ALERTA", f"'{n['name']}': {tipo} sem WHERE")
                elif tipo == "UPDATE" and not re.search(r"estado|status", s.split("WHERE", 1)[-1], re.I):
                    a("AVISO", f"'{n['name']}': UPDATE sem condição de estado", "reexecutar pode sobrescrever")
                else:
                    a("INFO", f"'{n['name']}': {tipo} com condição")
            if "$" in s and not p.get("options", {}).get("queryReplacement") and re.search(r"\$\d", s):
                a("AVISO", f"'{n['name']}': parâmetros $n sem valores em queryReplacement")

    # Code nodes
    for n in nos.values():
        if n["type"].endswith(".code"):
            js = str(n.get("parameters", {}).get("jsCode", "")) + str(n.get("parameters", {}).get("pythonCode", ""))
            usa = []
            if "$env" in js:
                usa.append("$env")
            if "console.log" in js:
                usa.append("console.log")
            if "require(" in js:
                usa.append("require")
            if usa:
                a("INFO", f"Code '{n['name']}' usa {', '.join(usa)}")
            if "$env" in js and "console.log" in js:
                a("AVISO", f"Code '{n['name']}' registra saída junto de variável de ambiente", "conferir se algo derivado do segredo vai para o log")

    # referências a nós inexistentes
    for caminho, t in textos(wf.get("nodes", [])):
        for ref in REF_NO.findall(t):
            if ref not in nos:
                a("ALERTA", "Expressão referencia nó inexistente", f"'{ref}' em {caminho[:60]}")

    # sinais de segredo no JSON inteiro (sem imprimir o valor)
    for caminho, t in textos(wf):
        for nome, rx in PADROES_SEGREDO:
            if rx.search(t):
                a("ALERTA", f"Possível segredo no JSON: {nome}", f"em {caminho[:70]} (valor omitido)")

    return {
        "nome": wf.get("name"), "id": wf.get("id"), "ativo": bool(wf.get("active")), "nos": len(nos),
        "tipos": dict(tipos), "credenciais": {k: v for k, v in creds.items()}, "achados": achados,
    }


def imprimir(arquivo: str, r: dict) -> None:
    print(f"== {arquivo}\n   {r['nome']} | nós: {r['nos']} | ativo: {r['ativo']} | id: {r['id']}")
    print("   tipos:", ", ".join(f"{k.split('.')[-1]} x{v}" for k, v in sorted(r["tipos"].items())))
    if r["credenciais"]:
        print("   credenciais (só referência):")
        for k, v in r["credenciais"].items():
            print(f"     - {k}: {', '.join(v)}")
    ordem = {"ALERTA": 0, "AVISO": 1, "INFO": 2}
    for nivel, titulo, detalhe in sorted(r["achados"], key=lambda x: ordem[x[0]]):
        print(f"   [{nivel}] {titulo}" + (f": {detalhe}" if detalhe else ""))
    cont = collections.Counter(x[0] for x in r["achados"])
    print(f"   resumo: {cont.get('ALERTA', 0)} alerta(s), {cont.get('AVISO', 0)} aviso(s), {cont.get('INFO', 0)} info\n")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Inspeção estática e somente leitura de workflows n8n exportados.")
    ap.add_argument("arquivos", nargs="+")
    ap.add_argument("--json", action="store_true", help="Saída em JSON.")
    ap.add_argument("--strict", action="store_true", help="Código 1 se houver ALERTA.")
    a = ap.parse_args(argv)
    saida, alerta = {}, False
    for f in a.arquivos:
        try:
            wf = json.loads(Path(f).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"ERRO ao ler {f}: {exc}", file=sys.stderr)
            return 2
        r = inspecionar(wf)
        saida[f] = r
        alerta = alerta or any(x[0] == "ALERTA" for x in r["achados"])
        if not a.json:
            imprimir(f, r)
    if a.json:
        print(json.dumps(saida, ensure_ascii=False, indent=2))
    return 1 if (a.strict and alerta) else 0


if __name__ == "__main__":
    raise SystemExit(main())
