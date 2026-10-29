#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resumo semanal da gestora comercial da Mesa Certa.

Calcula, a partir do SQLite, os indicadores da semana e devolve um JSON estruturado
mais um texto em linguagem simples. O banco é aberto SOMENTE para leitura
(`mode=ro`); o script não grava no banco, não chama o CRM e não dispara webhook.

Uso típico
----------
    py resumo_semanal.py --ref "2026-10-12 08:00"                       # semana anterior à data
    py resumo_semanal.py --db ..\\..\\mesa_certa.original.db --lote ..\\..\\webhook\\lote-webhook.jsonl --ref "2026-10-12 08:00"
    py resumo_semanal.py --servir --porta 8002                          # serviço local para o n8n

Toda data e hora de entrada e saída está em horário de Brasília (UTC-3, sem horário de
verão desde 2019). `pedidos_formulario.criado_em` e o lote do webhook estão em UTC e são
convertidos aqui. Nenhuma contagem é fixa: tudo vem dos dados.

Os indicadores saem separados em quatro grupos: comprovados (leitura direta dos dados),
estimativas (dependem de uma regra de classificação ou de cruzamento), dados incompletos
e limitações.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import hmac
import json
import math
import os
import re
import sqlite3
import statistics
import sys
import unicodedata
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERSAO = "1.0"
FMT_CRM = "%Y-%m-%d %H:%M:%S"          # CRM e histórico: horário de Brasília
FMT_UTC = "%Y-%m-%dT%H:%M:%SZ"         # formulário e webhook: UTC
UTC_MENOS_BRT = dt.timedelta(hours=3)
HORA_ABRE, HORA_FECHA = 8, 18          # horário comercial, segunda a sexta
PRAZO_HORAS_UTEIS = 4.0
TOLERANCIA_VINCULO_S = 60              # negócio criado até 60 s antes do pedido ainda conta como "criado por ele"
LIMITE_DADOS_ANTIGOS_H = 72            # acima disso o banco é considerado desatualizado em relação à referência
ETAPAS = ["Novo", "Contato", "Reunião marcada", "Reunião realizada", "Perdido"]
RAIZ = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------- datas e horas úteis


def parse_data(texto: str) -> dt.datetime:
    t = texto.strip()
    for f in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
              "%d/%m/%Y %H:%M", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(t, f)
        except ValueError:
            continue
    raise ValueError(f"data inválida: {texto!r} (use AAAA-MM-DD HH:MM, horário de Brasília)")


def agora_brasilia() -> dt.datetime:
    return (dt.datetime.now(dt.timezone.utc) - UTC_MENOS_BRT).replace(tzinfo=None, microsecond=0)


def periodo_padrao(ref: dt.datetime) -> tuple[dt.datetime, dt.datetime]:
    """Semana completa anterior à semana da referência: segunda 00:00 até a segunda 00:00 seguinte."""
    segunda = (ref - dt.timedelta(days=ref.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return segunda - dt.timedelta(days=7), segunda


def horas_uteis(a: dt.datetime, b: dt.datetime) -> float:
    """Horas entre a e b contando só segunda a sexta, 08:00 a 18:00. Zero se b <= a."""
    if b <= a:
        return 0.0
    total = 0.0
    dia = a.date()
    while dia <= b.date():
        if dia.weekday() < 5:
            abre = dt.datetime.combine(dia, dt.time(HORA_ABRE))
            fecha = dt.datetime.combine(dia, dt.time(HORA_FECHA))
            ini, fim = max(a, abre), min(b, fecha)
            if fim > ini:
                total += (fim - ini).total_seconds()
        dia += dt.timedelta(days=1)
    return total / 3600


def fmt(d: dt.datetime | None) -> str | None:
    return d.strftime(FMT_CRM) if d else None


def br(d: dt.datetime) -> str:
    return d.strftime("%d/%m")


# ---------------------------------------------------------------- normalização e classificação


def sem_acento(s: str | None) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower().strip()


def norm_email(s: str | None) -> str:
    return (s or "").strip().lower()


def norm_telefone(s: str | None) -> str:
    d = re.sub(r"\D", "", s or "")
    if len(d) >= 12 and d.startswith("55"):
        d = d[2:]
    return d


def telefone_sem_nono_digito(s: str | None) -> str:
    d = norm_telefone(s)
    return d[:2] + d[3:] if len(d) == 11 else d


_SUPORTE = ["esqueci minha senha", "parou de atualizar", "impressora", "sou cliente", "acesso foi bloqueado",
            "problema no pagamento", "altero o horario", "cancelar um pedido"]
_FORNECEDOR = ["fornecedora de embalagens", "trafego pago", "venda de insumos", "fotos profissionais",
               "agencia de marketing", "maquininhas"]
_SPAM = ["compre seguidores", "ganhe dinheiro"]
_TESTE = re.compile(r"(teste|fulano|asdf|mesacerta\.com|asdf@)", re.I)
_LIXO = {"", ".", "???", "123", "ghjkl", "aaaaaa", "asdf"}


def classificar_pedido(nome: str, email: str, restaurante: str | None, mensagem: str | None,
                       assinatura: str = "nao_verificada") -> str:
    """Regra de classificação (ESTIMATIVA: depende do texto). Precedência:
    assinatura inválida > spam > teste > lixo provável > suporte > fornecedor > comercial.
    "Quero testar o sistema" é pedido comercial: só conta como teste se nome, e-mail ou
    restaurante parecem de teste, ou se a mensagem começa com "teste"/"testando o formulário"."""
    if assinatura == "invalida":
        return "assinatura_invalida"
    m = sem_acento(mensagem)
    if any(k in m for k in _SPAM):
        return "spam"
    if (_TESTE.search(nome or "") or _TESTE.search(email or "") or _TESTE.search(restaurante or "")
            or m.startswith("teste") or m.startswith("testando o formulario")):
        return "teste"
    if m in _LIXO:
        return "lixo_provavel"
    if any(k in m for k in _SUPORTE):
        return "suporte"
    if any(k in m for k in _FORNECEDOR):
        return "fornecedor"
    return "comercial"


# ---------------------------------------------------------------- estatística simples


def wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    if n == 0:
        return None
    ph = k / n
    den = 1 + z * z / n
    centro = (ph + z * z / (2 * n)) / den
    meia = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return [round(100 * (centro - meia), 1), round(100 * (centro + meia), 1)]


def fisher_bilateral(a: int, b: int, c: int, d: int) -> float | None:
    n = a + b + c + d
    if n == 0 or (a + b) == 0 or (c + d) == 0:
        return None
    r1, c1 = a + b, a + c

    def pr(x: int) -> float:
        return math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)

    p0 = pr(a)
    return round(sum(pr(x) for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1) if pr(x) <= p0 + 1e-12), 3)


def pct(k: int, n: int) -> float | None:
    return round(100 * k / n, 1) if n else None


# ---------------------------------------------------------------- leitura dos dados (somente leitura)


def abrir_somente_leitura(caminho: str | os.PathLike) -> sqlite3.Connection:
    p = Path(caminho).resolve()
    if not p.exists():
        raise FileNotFoundError(f"banco não encontrado: {p}")
    con = sqlite3.connect(p.as_uri() + "?mode=ro", uri=True, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def carregar_negocios(con: sqlite3.Connection, ref: dt.datetime) -> list[dict]:
    """Negócios existentes na data de referência (criados até ela), com a etapa naquele momento."""
    ref_s = fmt(ref)
    linhas = con.execute(
        """SELECT deal_id, criado_em, atualizado_em, nome, email, telefone, restaurante, etapa, origem,
                  responsavel, primeiro_contato_em, atualizado_por
           FROM negocios_crm WHERE criado_em <= ?""", (ref_s,)).fetchall()
    etapa_na_ref = {r["deal_id"]: r["etapa"] for r in con.execute(
        """SELECT deal_id, etapa FROM (
               SELECT deal_id, etapa, ROW_NUMBER() OVER (PARTITION BY deal_id ORDER BY em DESC, rowid DESC) rn
               FROM historico_etapas WHERE em <= ?) WHERE rn = 1""", (ref_s,))}
    negocios = []
    for r in linhas:
        n = dict(r)
        n["criado"] = dt.datetime.strptime(n["criado_em"], FMT_CRM)
        n["atualizado"] = dt.datetime.strptime(n["atualizado_em"], FMT_CRM)
        pc = n["primeiro_contato_em"]
        n["contato"] = dt.datetime.strptime(pc, FMT_CRM) if pc else None
        if n["contato"] and n["contato"] > ref:
            n["contato"] = None                      # contato depois da referência não existia ainda
        n["responsavel"] = n["responsavel"] or "sem_responsavel"
        n["etapa_na_ref"] = etapa_na_ref.get(n["deal_id"], n["etapa"])
        n["sem_historico"] = n["deal_id"] not in etapa_na_ref
        n["email_n"] = norm_email(n["email"])
        n["tel_n"] = norm_telefone(n["telefone"])
        negocios.append(n)
    return negocios


def _evento(d: dict, fonte: str, assinatura: str, entregas: int) -> dict | None:
    try:
        brt = dt.datetime.strptime(d["criado_em"], FMT_UTC) - UTC_MENOS_BRT
    except (KeyError, ValueError, TypeError):
        brt = None
    return {"id": d.get("event_id"), "nome": d.get("nome") or "", "email": d.get("email") or "",
            "telefone": d.get("telefone") or "", "restaurante": d.get("restaurante") or "",
            "mensagem": d.get("mensagem") or "", "fonte": fonte, "assinatura": assinatura,
            "entregas": entregas, "brt": brt}


def carregar_eventos(con: sqlite3.Connection, lote: str | None, segredo: str | None) -> tuple[dict, dict]:
    """Une os pedidos gravados no banco com (opcionalmente) um arquivo de lote do webhook.
    Retorna (eventos por event_id, estatísticas do lote)."""
    eventos: dict[str, dict] = {}
    estat = {"lote_informado": bool(lote), "linhas": 0, "json_invalidos": 0, "assinatura_valida": 0,
             "assinatura_invalida": 0, "assinatura_nao_verificada": 0, "reenvios_excedentes": 0}
    if lote:
        cont: dict[str, dict] = {}
        for linha in Path(lote).read_text(encoding="utf-8").splitlines():
            if not linha.strip():
                continue
            estat["linhas"] += 1
            o = json.loads(linha)
            if segredo:
                calc = "sha256=" + hmac.new(segredo.encode(), o["corpo"].encode("utf-8"), hashlib.sha256).hexdigest()
                ok = hmac.compare_digest(calc, o["assinatura"])
                estat["assinatura_valida" if ok else "assinatura_invalida"] += 1
            else:
                ok = None
                estat["assinatura_nao_verificada"] += 1
            try:
                d = json.loads(o["corpo"])
            except ValueError:
                estat["json_invalidos"] += 1
                continue
            e = cont.setdefault(d["event_id"], {"d": d, "ok": [], "n": 0})
            e["ok"].append(ok)
            e["n"] += 1
        for eid, e in cont.items():
            if segredo:
                ass = "valida" if any(x for x in e["ok"] if x) else "invalida"
            else:
                ass = "nao_verificada"
            eventos[eid] = _evento(e["d"], "lote_webhook", ass, e["n"])
            estat["reenvios_excedentes"] += e["n"] - 1
    # pedidos já gravados no banco (o WF01 só grava depois de validar a assinatura)
    for r in con.execute("SELECT event_id, criado_em, nome, email, telefone, restaurante, mensagem FROM pedidos_formulario"):
        eventos[r["event_id"]] = _evento(dict(r), "pedidos_formulario", "validada_na_entrada", 1)
    for e in eventos.values():
        e["classe"] = classificar_pedido(e["nome"], e["email"], e["restaurante"], e["mensagem"], e["assinatura"])
        e["email_n"] = norm_email(e["email"])
        e["tel_n"] = norm_telefone(e["telefone"])
    return eventos, estat


def vincular(eventos: dict, negocios: list[dict]) -> None:
    """Para cada pedido, acha negócios com o mesmo e-mail ou telefone (normalizados)."""
    por_email, por_tel = collections.defaultdict(list), collections.defaultdict(list)
    for n in negocios:
        if n["email_n"]:
            por_email[n["email_n"]].append(n)
        if n["tel_n"]:
            por_tel[n["tel_n"]].append(n)
    for e in eventos.values():
        achados = {}
        for n in por_email.get(e["email_n"], []):
            achados[n["deal_id"]] = n
        for n in por_tel.get(e["tel_n"], []) if e["tel_n"] else []:
            achados[n["deal_id"]] = n
        e["via"] = ("email+telefone" if por_email.get(e["email_n"]) and e["tel_n"] and por_tel.get(e["tel_n"])
                    else "email" if por_email.get(e["email_n"]) else "telefone" if achados else "nenhum")
        e["depois"], e["antes"], e["atraso_s"] = [], [], []
        for n in achados.values():
            if e["brt"] is None:
                continue
            atraso = (n["criado"] - e["brt"]).total_seconds()
            if atraso >= -TOLERANCIA_VINCULO_S:
                e["depois"].append(n["deal_id"])
                e["atraso_s"].append(atraso)
            else:
                e["antes"].append(n["deal_id"])
        e["status"] = ("vinculado" if e["depois"] else "ja_tinha_negocio" if e["antes"] else "sem_correspondencia")


def classe_do_negocio(n: dict, classes_por_negocio: dict) -> str:
    cl = classes_por_negocio.get(n["deal_id"])
    if not cl:
        return "sem_pedido_manual" if n["origem"] == "Manual" else "sem_pedido"
    return "comercial" if "comercial" in cl else "nao_comercial:" + sorted(cl)[0]


def pessoas_unicas(eventos_lista: list[dict], tel_fn) -> int:
    pai = {e["id"]: e["id"] for e in eventos_lista}

    def raiz(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    visto: dict = {}
    for e in eventos_lista:
        for chave in (("e", e["email_n"]), ("t", tel_fn(e["telefone"]))):
            if not chave[1]:
                continue
            if chave in visto:
                pai[raiz(e["id"])] = raiz(visto[chave])
            else:
                visto[chave] = e["id"]
    return len({raiz(e["id"]) for e in eventos_lista})


# ---------------------------------------------------------------- indicadores


def grupo_sla(negocios: list[dict], ref: dt.datetime) -> dict:
    """Prazo de primeiro contato (horas úteis) para um conjunto de negócios, por responsável."""
    saida = {}
    for resp in sorted({n["responsavel"] for n in negocios}) + ["TOTAL"]:
        g = [n for n in negocios if resp == "TOTAL" or n["responsavel"] == resp]
        com = [n for n in g if n["contato"]]
        horas = sorted(horas_uteis(n["criado"], n["contato"]) for n in com)
        no_prazo = sum(1 for h in horas if h <= PRAZO_HORAS_UTEIS)
        sem = [n for n in g if not n["contato"]]
        perdidos = [n for n in sem if n["etapa_na_ref"] == "Perdido"]
        abertos = [n for n in sem if n["etapa_na_ref"] != "Perdido"]
        vencidos = [n for n in abertos if horas_uteis(n["criado"], ref) > PRAZO_HORAS_UTEIS]
        decidiveis = len(com) + len(vencidos)
        saida[resp] = {
            "negocios": len(g), "com_contato": len(com), "contato_no_prazo": no_prazo,
            "contato_atrasado": len(com) - no_prazo, "sem_contato_prazo_vencido": len(vencidos),
            "sem_contato_ainda_no_prazo": len(abertos) - len(vencidos),
            "perdido_sem_contato": len(perdidos), "decidiveis": decidiveis,
            "pct_no_prazo_entre_decidiveis": pct(no_prazo, decidiveis),
            "ic95_pct_no_prazo": wilson(no_prazo, decidiveis),
            "mediana_horas_uteis": round(statistics.median(horas), 2) if horas else None,
            "p90_horas_uteis": round(horas[max(int(len(horas) * 0.9) - 1, 0)], 2) if horas else None,
        }
    return saida


def comparar_responsaveis(sla: dict) -> dict:
    resp = [r for r in sla if r != "TOTAL" and sla[r]["decidiveis"] > 0]
    comp = {}
    for r in resp:
        ok, n = sla[r]["contato_no_prazo"], sla[r]["decidiveis"]
        ok2 = sum(sla[o]["contato_no_prazo"] for o in resp if o != r)
        n2 = sum(sla[o]["decidiveis"] for o in resp if o != r)
        comp[r] = {"p_fisher_contra_os_demais": fisher_bilateral(ok, n - ok, ok2, n2 - ok2)}
    comp["diferenca_estatisticamente_comprovada"] = any(
        (v["p_fisher_contra_os_demais"] is not None and v["p_fisher_contra_os_demais"] < 0.05)
        for k, v in comp.items() if k != "diferenca_estatisticamente_comprovada")
    return comp


def calcular(con: sqlite3.Connection, ref: dt.datetime, ini: dt.datetime, fim: dt.datetime,
             lote: str | None = None, segredo: str | None = None) -> dict:
    negocios = carregar_negocios(con, ref)
    eventos, estat_lote = carregar_eventos(con, lote, segredo)
    vincular(eventos, negocios)
    classes_por_negocio: dict[int, set] = collections.defaultdict(set)
    for e in eventos.values():
        for d in e["depois"]:
            classes_por_negocio[d].add(e["classe"])
    for n in negocios:
        n["tipo"] = classe_do_negocio(n, classes_por_negocio)

    # ---- funil
    contagem = collections.Counter(n["etapa_na_ref"] for n in negocios)
    funil = {e: contagem.get(e, 0) for e in ETAPAS}
    for e, q in contagem.items():
        if e not in funil:
            funil[e] = q
    divergentes = sum(1 for n in negocios if n["etapa"] != n["etapa_na_ref"])
    perdidos_automacao = sum(1 for n in negocios if n["etapa_na_ref"] == "Perdido" and n["atualizado_por"] == "automacao_limpeza")
    perdidos_sem_contato = sum(1 for n in negocios if n["etapa_na_ref"] == "Perdido" and not n["contato"])

    # ---- criados e atualizados
    criados = [n for n in negocios if ini <= n["criado"] < fim]
    atualizados = [n for n in negocios if ini <= n["atualizado"] < fim and n["atualizado"] <= ref]
    ids_hist = {r[0] for r in con.execute(
        "SELECT DISTINCT deal_id FROM historico_etapas WHERE em >= ? AND em < ?", (fmt(ini), fmt(min(fim, ref + dt.timedelta(seconds=1)))))}
    atualizados_por_dia = collections.Counter(n["atualizado"].strftime("%Y-%m-%d") for n in atualizados)
    criados_por_dia = collections.Counter(n["criado"].strftime("%Y-%m-%d") for n in criados)
    dias = [(ini + dt.timedelta(days=i)).strftime("%Y-%m-%d") for i in range((fim - ini).days)]

    # ---- pedidos e reconciliação (pedidos cuja hora de Brasília cai no período)
    no_periodo = [e for e in eventos.values() if e["brt"] and ini <= e["brt"] < fim and e["brt"] <= ref]
    por_classe = collections.Counter(e["classe"] for e in no_periodo)
    comerciais = [e for e in no_periodo if e["classe"] == "comercial"]
    status = collections.Counter(e["status"] for e in comerciais)
    ausentes = sorted((e for e in comerciais if e["status"] == "sem_correspondencia"), key=lambda x: x["brt"])
    atrasos = [a for e in comerciais if e["status"] == "vinculado" for a in [min(e["atraso_s"])]]
    por_email = collections.Counter(e["email_n"] for e in comerciais)
    nao_com = {}
    for cl in ("suporte", "fornecedor", "teste", "lixo_provavel", "spam", "assinatura_invalida"):
        sub = [e for e in no_periodo if e["classe"] == cl]
        ids = {d for e in sub for d in e["depois"]}
        nao_com[cl] = {"pedidos": len(sub), "pedidos_com_negocio_no_crm": sum(1 for e in sub if e["depois"]),
                       "negocios_no_crm": len(ids)}
    ultimo_registro_crm = max((max(n["criado"], min(n["atualizado"], ref)) for n in negocios), default=None)
    ultimo_pedido = max((e["brt"] for e in eventos.values() if e["brt"]), default=None)
    primeiro_pedido = min((e["brt"] for e in eventos.values() if e["brt"]), default=None)
    sem_pedido = [n for n in criados if n["tipo"] in ("sem_pedido", "sem_pedido_manual")]
    sem_pedido_fora_janela = [n for n in sem_pedido if n["origem"] != "Manual" and (ultimo_pedido is None or n["criado"] > ultimo_pedido)]

    # ---- prazo de primeiro contato
    sla_todos = grupo_sla(criados, ref)
    comerciais_neg = [n for n in criados if n["tipo"] == "comercial"]
    sla_com = grupo_sla(comerciais_neg, ref)
    autoria = [n for n in comerciais_neg if n["etapa_na_ref"] == "Contato" and n["contato"] and n["atualizado"] == n["contato"]]
    autor_igual = sum(1 for n in autoria if n["atualizado_por"] == n["responsavel"])

    # ---- sem retorno na data de referência
    novos = [n for n in negocios if n["etapa_na_ref"] == "Novo" and not n["contato"]]
    for n in novos:
        n["espera_h"] = horas_uteis(n["criado"], ref)
    vencidos = [n for n in novos if n["espera_h"] > PRAZO_HORAS_UTEIS]
    faixas = [(0, 4), (4, 8), (8, 20), (20, 40), (40, 100), (100, 10**6)]
    def item(n):
        return {"deal_id": n["deal_id"], "nome": n["nome"], "telefone": n["telefone"], "responsavel": n["responsavel"],
                "criado_em": n["criado_em"], "horas_uteis_de_espera": round(n["espera_h"], 1), "tipo": n["tipo"]}
    a_cobrar = sorted((n for n in vencidos if n["tipo"] in ("comercial", "sem_pedido", "sem_pedido_manual")),
                      key=lambda n: -n["espera_h"])

    comprovados = {
        "funil": {
            "descricao": "Negócios por etapa na data de referência (última etapa do histórico até a referência).",
            "total": sum(funil.values()), "por_etapa": funil,
            "reunioes_marcada_ou_realizada": funil.get("Reunião marcada", 0) + funil.get("Reunião realizada", 0),
            "perdidos_pela_automacao_de_limpeza": perdidos_automacao,
            "perdidos_sem_nenhum_contato": perdidos_sem_contato,
            "conferencia_etapa_atual_do_crm_diferente_da_etapa_na_referencia": divergentes,
        },
        "negocios_criados_e_atualizados": {
            "descricao": "Criados: data de criação no período. Atualizados: data da última atualização no período "
                         "(é a definição que reproduz a planilha da gestora).",
            "criados": len(criados), "criados_por_origem": dict(collections.Counter(n["origem"] for n in criados)),
            "criados_por_dia": {d: criados_por_dia.get(d, 0) for d in dias},
            "atualizados": len(atualizados),
            "atualizados_por_dia": {d: atualizados_por_dia.get(d, 0) for d in dias},
            "atualizados_que_foram_criados_antes_do_periodo": sum(1 for n in atualizados if n["criado"] < ini),
            "atualizados_pela_automacao_de_limpeza": sum(1 for n in atualizados if n["atualizado_por"] == "automacao_limpeza"),
            "negocios_com_mudanca_de_etapa_no_periodo": len(ids_hist),
        },
        "prazo_primeiro_contato_todos_os_negocios_criados": {
            "descricao": "Todos os negócios criados no período, sem separar teste, suporte ou fornecedor. "
                         f"Prazo: {PRAZO_HORAS_UTEIS:g} horas úteis (seg a sex, {HORA_ABRE}h às {HORA_FECHA}h, Brasília).",
            "por_responsavel": sla_todos,
        },
        "sem_retorno_na_referencia": {
            "descricao": "Negócios em Novo, sem primeiro contato até a referência.",
            "em_novo_sem_contato": len(novos), "com_prazo_vencido": len(vencidos),
            "ainda_no_prazo": len(novos) - len(vencidos),
            "vencidos_por_responsavel": dict(collections.Counter(n["responsavel"] for n in vencidos)),
            "vencidos_por_faixa_de_espera_horas_uteis": {f"{a}-{b if b < 10**6 else 'mais'}": sum(1 for n in vencidos if a < n["espera_h"] <= b)
                                                        for a, b in faixas},
            "vencidos_por_mes_de_criacao": dict(sorted(collections.Counter(n["criado_em"][:7] for n in vencidos).items())),
        },
    }
    estimativas = {
        "aviso": "Dependem da regra de classificação por texto e do cruzamento por e-mail/telefone. "
                 "Podem mudar se a regra mudar.",
        "pedidos_do_periodo": {
            "pedidos_distintos": len(no_periodo), "por_classe": dict(por_classe),
            "comerciais": len(comerciais),
            "pessoas_distintas_entre_comerciais": pessoas_unicas(comerciais, norm_telefone) if comerciais else 0,
            "pessoas_distintas_ignorando_nono_digito": pessoas_unicas(comerciais, telefone_sem_nono_digito) if comerciais else 0,
            "emails_que_pediram_mais_de_uma_vez": sum(1 for q in por_email.values() if q > 1),
        },
        "reconciliacao_pedidos_comerciais_com_o_crm": {
            "comerciais": len(comerciais),
            "viraram_negocio": status.get("vinculado", 0),
            "pessoa_ja_tinha_negocio": status.get("ja_tinha_negocio", 0),
            "sem_correspondencia_no_crm": status.get("sem_correspondencia", 0),
            "maior_atraso_entre_pedido_e_negocio_em_segundos": round(max(atrasos), 1) if atrasos else None,
            "ausentes": [{"event_id": e["id"], "recebido_em_brasilia": fmt(e["brt"]), "nome": e["nome"],
                          "telefone": e["telefone"], "email": e["email"].strip(), "fonte": e["fonte"],
                          "assinatura": e["assinatura"]} for e in ausentes],
        },
        "pedidos_nao_comerciais_e_o_crm": nao_com,
        "negocios_criados_sem_pedido_correspondente": {
            "total": len(sem_pedido), "origem_manual": sum(1 for n in sem_pedido if n["origem"] == "Manual"),
            "site_criados_depois_do_ultimo_pedido_conhecido": len(sem_pedido_fora_janela),
        },
        "prazo_primeiro_contato_pedidos_comerciais": {
            "descricao": "Só negócios criados no período que nasceram de um pedido classificado como comercial.",
            "por_responsavel": sla_com, "comparacao_entre_responsaveis": comparar_responsaveis(sla_com),
            "autoria_do_contato": {
                "negocios_em_que_o_ultimo_registro_e_o_contato": len(autoria),
                "autor_igual_ao_responsavel": autor_igual,
                "pct_autor_igual_ao_responsavel": pct(autor_igual, len(autoria)),
            },
        },
        "sem_retorno_por_tipo_de_negocio": {
            "vencidos_por_tipo": dict(collections.Counter(n["tipo"] for n in vencidos)),
            "vencidos_comerciais_por_responsavel": dict(collections.Counter(n["responsavel"] for n in vencidos if n["tipo"] == "comercial")),
            "para_cobrar_hoje_mais_antigos": [item(n) for n in a_cobrar[:15]],
            "para_cobrar_hoje_total": len(a_cobrar),
        },
    }
    incompletos = []

    def inc(codigo, descricao, quantidade=None):
        incompletos.append({"codigo": codigo, "descricao": descricao, "quantidade": quantidade})

    if ultimo_registro_crm is None or ref - ultimo_registro_crm > dt.timedelta(hours=LIMITE_DADOS_ANTIGOS_H):
        inc("banco_do_crm_desatualizado",
            f"A cópia do CRM neste banco só tem registros até {fmt(ultimo_registro_crm) or 'nunca'}, mais de "
            f"{LIMITE_DADOS_ANTIGOS_H // 24} dias antes da referência ({fmt(ref)}). O funil, o prazo e os sem retorno "
            "refletem o banco, não necessariamente o CRM de hoje.", None)
    if estat_lote["lote_informado"] and estat_lote["assinatura_nao_verificada"]:
        inc("assinatura_nao_verificada", "O lote foi lido sem o segredo HMAC: a assinatura dos pedidos do lote não foi conferida.",
            estat_lote["assinatura_nao_verificada"])
    if estat_lote["json_invalidos"]:
        inc("entregas_com_json_invalido", "Entregas do lote com corpo que não é JSON; ignoradas (o mesmo pedido costuma chegar inteiro em outra entrega).",
            estat_lote["json_invalidos"])
    if ultimo_pedido and ultimo_pedido < fim - dt.timedelta(hours=1):
        inc("pedidos_terminam_antes_do_fim_do_periodo",
            f"O último pedido conhecido é de {fmt(ultimo_pedido)}; pedidos depois disso não estão nos dados. "
            f"{len(sem_pedido_fora_janela)} negócios do site foram criados depois dele e ficam sem pedido para comparar.",
            len(sem_pedido_fora_janela))
    if primeiro_pedido and primeiro_pedido > ini:
        inc("pedidos_comecam_depois_do_inicio_do_periodo",
            f"O primeiro pedido conhecido é de {fmt(primeiro_pedido)}, depois do início do período.", None)
    antigos_sem_pedido = sum(1 for n in vencidos if n["tipo"] == "sem_pedido")
    if antigos_sem_pedido:
        inc("negocios_sem_pedido_para_classificar",
            "Negócios em Novo com prazo vencido que não têm pedido correspondente nos dados; não dá para saber se são comerciais.", antigos_sem_pedido)
    if divergentes:
        inc("etapa_do_crm_diferente_do_historico_na_referencia",
            "Negócios cuja etapa atual no CRM difere da etapa que o histórico mostra na data de referência "
            "(esperado se o banco foi atualizado depois da referência).", divergentes)
    sem_hist = sum(1 for n in negocios if n["sem_historico"])
    if sem_hist:
        inc("negocios_sem_historico", "Negócios sem linhas no histórico de etapas; usada a etapa atual do cadastro.", sem_hist)
    inc("contatos_depois_da_referencia", "Contatos feitos depois da data de referência não são conhecidos: "
        "um negócio 'sem contato' pode já ter sido atendido depois.", None)
    contatos_fora = sum(1 for n in negocios if n["contato"] and (n["contato"].weekday() >= 5 or not HORA_ABRE <= n["contato"].hour < HORA_FECHA))
    if contatos_fora:
        inc("contatos_registrados_fora_do_horario_comercial",
            "Primeiros contatos com hora fora de seg a sex 8h às 18h; contam até o fim do último período útil.", contatos_fora)

    limitacoes = [
        "O prazo é contado do cadastro do negócio no CRM até o campo 'primeiro_contato_em'; o banco não diz quem fez o contato nem por qual canal.",
        f"O responsável pelo negócio nem sempre é quem registrou o contato"
        + (f" (em {autor_igual} de {len(autoria)} negócios com autoria identificável, o autor é o próprio responsável)." if autoria else "."),
        "Com poucos negócios por pessoa, diferenças entre SDRs podem ser acaso; veja 'comparacao_entre_responsaveis' antes de cobrar alguém.",
        "Feriados não são descontados (suposição registrada em suposicoes.md).",
        "A classificação de pedidos (comercial, suporte, fornecedor, teste, lixo, spam) é uma regra por texto, nome e e-mail e não foi validada por pessoas.",
        "O cruzamento pedido x negócio usa e-mail ou telefone iguais; mesma pessoa com outro e-mail e outro telefone não é reconhecida.",
        "Um pedido 'sem correspondência' pode ter outra explicação além de falha de integração (cadastro manual com outros dados, por exemplo).",
        "A data de última atualização do negócio mostra só a alteração mais recente; ela serve para reproduzir a planilha da gestora, mas não conta pedidos.",
    ]
    return {
        "versao_script": VERSAO,
        "referencia": {
            "data_hora_brasilia": fmt(ref), "periodo_inicio": fmt(ini), "periodo_fim_exclusivo": fmt(fim),
            "fuso": "America/Sao_Paulo (UTC-3)", "gerado_em_brasilia": fmt(agora_brasilia()),
            "prazo_primeiro_contato_horas_uteis": PRAZO_HORAS_UTEIS,
            "horario_comercial": f"segunda a sexta, {HORA_ABRE}h às {HORA_FECHA}h",
        },
        "fontes": {
            "negocios_no_crm_ate_a_referencia": len(negocios), "ultimo_registro_do_crm_no_banco": fmt(ultimo_registro_crm),
            "pedidos_lidos": len(eventos),
            "pedidos_do_banco": sum(1 for e in eventos.values() if e["fonte"] == "pedidos_formulario"),
            "pedidos_so_do_lote": sum(1 for e in eventos.values() if e["fonte"] == "lote_webhook"),
            "lote": estat_lote, "primeiro_pedido_brasilia": fmt(primeiro_pedido), "ultimo_pedido_brasilia": fmt(ultimo_pedido),
        },
        "indicadores_comprovados": comprovados,
        "estimativas": estimativas,
        "dados_incompletos": incompletos,
        "limitacoes": limitacoes,
    }


# ---------------------------------------------------------------- texto em linguagem simples


def montar_resumo(ind: dict) -> str:
    ref, c, e = ind["referencia"], ind["indicadores_comprovados"], ind["estimativas"]
    ini = parse_data(ref["periodo_inicio"])
    fim = parse_data(ref["periodo_fim_exclusivo"]) - dt.timedelta(days=1)
    f, cr = c["funil"], c["negocios_criados_e_atualizados"]
    pe, rc = e["pedidos_do_periodo"], e["reconciliacao_pedidos_comerciais_com_o_crm"]
    sla, sr = e["prazo_primeiro_contato_pedidos_comerciais"], c["sem_retorno_na_referencia"]
    L = []
    L.append(f"Resumo da semana de {br(ini)} a {br(fim)} (posição em {parse_data(ref['data_hora_brasilia']).strftime('%d/%m às %H:%M')}, horário de Brasília)")
    L.append("")
    for d in ind["dados_incompletos"]:
        if d["codigo"] == "banco_do_crm_desatualizado":
            L.append("ATENÇÃO: " + d["descricao"])
            L.append("")
    L.append("1. COMO ESTÁ O FUNIL AGORA")
    L.append(f"   Você tem {f['total']} negócios: " + ", ".join(f"{f['por_etapa'][k]} em {k}" for k in f["por_etapa"]) + ".")
    L.append(f"   {f['reunioes_marcada_ou_realizada']} já viraram reunião (marcada ou realizada).")
    if f["perdidos_pela_automacao_de_limpeza"]:
        L.append(f"   Atenção: {f['perdidos_pela_automacao_de_limpeza']} dos perdidos foram movidos pela limpeza automática, sem ligação de ninguém.")
    L.append("")
    L.append("2. QUANTOS PEDIDOS CHEGARAM")
    L.append(f"   O CRM criou {cr['criados']} negócios novos na semana. O número de negócios 'atualizados' na semana é {cr['atualizados']}"
             + (f"; ele inclui {cr['atualizados_que_foram_criados_antes_do_periodo']} negócios antigos que só foram mexidos "
                f"({cr['atualizados_pela_automacao_de_limpeza']} deles pela limpeza automática). "
                "É por isso que ele fica bem acima dos pedidos reais." if cr["atualizados_que_foram_criados_antes_do_periodo"] else "."))
    if pe["pedidos_distintos"]:
        L.append(f"   Pelos pedidos do formulário: {pe['pedidos_distintos']} pedidos distintos, dos quais {pe['comerciais']} pedidos de demonstração "
                 f"(de {pe['pessoas_distintas_entre_comerciais']} pessoas; {pe['emails_que_pediram_mais_de_uma_vez']} pessoas pediram mais de uma vez). "
                 "O restante é suporte, fornecedor, teste, lixo ou pedido com assinatura inválida.")
    else:
        L.append("   Não há pedidos do formulário nos dados deste período.")
    L.append("")
    L.append("3. PEDIDOS QUE NÃO CHEGARAM AO CRM")
    if pe["comerciais"]:
        L.append(f"   Dos {rc['comerciais']} pedidos de demonstração, {rc['viraram_negocio']} viraram negócio, "
                 f"{rc['pessoa_ja_tinha_negocio']} eram de pessoas que já tinham negócio e {rc['sem_correspondencia_no_crm']} não aparecem no CRM.")
        for a in rc["ausentes"][:20]:
            L.append(f"   - {a['nome']}, tel. {a['telefone']}, pediu em {a['recebido_em_brasilia'][8:10]}/{a['recebido_em_brasilia'][5:7]} às {a['recebido_em_brasilia'][11:16]}")
        if len(rc["ausentes"]) > 20:
            L.append(f"   - e mais {len(rc['ausentes']) - 20}. Lista completa no arquivo da semana.")
    nc = e["pedidos_nao_comerciais_e_o_crm"]
    sujos = sum(v["negocios_no_crm"] for v in nc.values())
    if sujos:
        L.append(f"   Também há {sujos} negócios no CRM que nasceram de suporte, fornecedor, teste ou lixo e ocupam a fila do time.")
    L.append("")
    L.append("4. RETORNO EM ATÉ 4 HORAS ÚTEIS (seg a sex, 8h às 18h)")
    t = sla["por_responsavel"].get("TOTAL")
    if t and t["negocios"]:
        L.append(f"   Dos {t['negocios']} negócios de pedidos de demonstração criados na semana: {t['contato_no_prazo']} foram atendidos no prazo, "
                 f"{t['contato_atrasado']} atendidos fora do prazo, {t['sem_contato_prazo_vencido']} sem retorno e já vencidos, "
                 f"{t['sem_contato_ainda_no_prazo']} sem retorno mas ainda dentro do prazo.")
        if t["pct_no_prazo_entre_decidiveis"] is not None:
            L.append(f"   Entre os casos que já dá para julgar ({t['decidiveis']}), {t['pct_no_prazo_entre_decidiveis']:.0f}% foram no prazo. "
                     f"O tempo típico até a ligação foi de {str(t['mediana_horas_uteis']).replace('.', ',')} horas úteis (mediana).")
        for r, v in sla["por_responsavel"].items():
            if r != "TOTAL" and v["decidiveis"]:
                L.append(f"   - {r}: {v['contato_no_prazo']} de {v['decidiveis']} no prazo ({v['pct_no_prazo_entre_decidiveis']:.0f}%), {v['sem_contato_prazo_vencido']} sem retorno vencido.")
        comp = sla["comparacao_entre_responsaveis"]
        if comp["diferenca_estatisticamente_comprovada"]:
            L.append("   A diferença entre os SDRs é grande o bastante para não ser acaso.")
        else:
            L.append("   Com esses números não dá para afirmar que um SDR atrasa mais que os outros: a diferença pode ser acaso. "
                     "Também não sabemos quem fez cada ligação, só quem é o responsável pelo negócio.")
    else:
        L.append("   Não há negócios de pedidos de demonstração criados nesta semana.")
    L.append("")
    L.append("5. QUEM PRECISA DE RETORNO HOJE")
    L.append(f"   {sr['em_novo_sem_contato']} negócios estão em 'Novo' sem nenhum contato; {sr['com_prazo_vencido']} já passaram do prazo de 4 horas úteis"
             + (": " + ", ".join(f"{k} {v}" for k, v in sorted(sr['vencidos_por_responsavel'].items())) if sr["vencidos_por_responsavel"] else "") + ".")
    sp = e["sem_retorno_por_tipo_de_negocio"]
    if sp["para_cobrar_hoje_total"]:
        L.append(f"   Para cobrar hoje (pedidos comerciais ou sem pedido para classificar): {sp['para_cobrar_hoje_total']}. Os mais antigos:")
        for x in sp["para_cobrar_hoje_mais_antigos"][:5]:
            L.append(f"   - negócio {x['deal_id']}, {x['nome']}, {x['responsavel']}, esperando há {x['horas_uteis_de_espera']:.0f} horas úteis")
    L.append("")
    L.append("6. O QUE OS DADOS NÃO PERMITEM AFIRMAR")
    for d in ind["dados_incompletos"][:6]:
        qtd = d["quantidade"] if d["quantidade"] is not None and d["codigo"] != "pedidos_terminam_antes_do_fim_do_periodo" else None
        L.append(f"   - {d['descricao']}" + (f" Quantidade: {qtd}." if qtd is not None else ""))
    for lim in ind["limitacoes"][:4]:
        L.append(f"   - {lim}")
    L.append("")
    L.append("Números 'comprovados' vêm direto dos dados; os de pedidos, ausentes e prazo por pedido comercial são estimativas "
             "(dependem de uma regra de classificação). Detalhes no arquivo JSON.")
    return "\n".join(L)


# ---------------------------------------------------------------- execução


def gerar(db: str, ref: dt.datetime, ini: dt.datetime | None = None, fim: dt.datetime | None = None,
          lote: str | None = None, segredo: str | None = None) -> dict:
    p_ini, p_fim = periodo_padrao(ref)
    ini, fim = ini or p_ini, fim or p_fim
    if fim <= ini:
        raise ValueError("o fim do período deve ser depois do início")
    con = abrir_somente_leitura(db)
    try:
        ind = calcular(con, ref, ini, fim, lote, segredo)
    finally:
        con.close()
    ind["resumo_texto"] = montar_resumo(ind)
    return ind


def servir(args) -> None:
    """Serviço HTTP local, somente leitura, para o n8n (Execute Command vem desativado no n8n 2.x)."""
    segredo = os.environ.get(args.segredo_env) if args.lote else None

    class H(BaseHTTPRequestHandler):
        def _enviar(self, codigo, corpo):
            dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(dados)))
            self.end_headers()
            self.wfile.write(dados)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            if u.path == "/saude":
                return self._enviar(200, {"status": "ok", "versao": VERSAO})
            if u.path != "/resumo":
                return self._enviar(404, {"erro": "rota_inexistente"})
            q = urllib.parse.parse_qs(u.query)
            try:
                ref = parse_data(q["ref"][0]) if q.get("ref") else agora_brasilia()
            except ValueError as exc:
                return self._enviar(400, {"erro": f"ValueError: {exc}"})
            try:
                self._enviar(200, gerar(args.db, ref, lote=args.lote, segredo=segredo))
            except (ValueError, FileNotFoundError, sqlite3.Error, KeyError) as exc:
                self._enviar(500, {"erro": f"{type(exc).__name__}: {exc}"})

        def log_message(self, formato, *a):          # sem ruído com dados no console
            sys.stderr.write("[resumo_semanal] " + (formato % a) + "\n")

    srv = ThreadingHTTPServer(("127.0.0.1", args.porta), H)
    print(f"Resumo semanal em http://127.0.0.1:{args.porta}/resumo (somente leitura; Ctrl+C para parar)", flush=True)
    srv.serve_forever()


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Indicadores e resumo semanal da gestora (somente leitura).")
    ap.add_argument("--db", default=str(RAIZ / "mesa_certa.db"), help="SQLite a ler (padrão: mesa_certa.db do repositório).")
    ap.add_argument("--lote", help="Arquivo .jsonl do webhook para reproduzir períodos sem pedidos no banco.")
    ap.add_argument("--segredo-env", default="MESA_CERTA_HMAC_SECRET", help="Variável com o segredo HMAC (só para conferir o lote).")
    ap.add_argument("--ref", help="Data de referência em Brasília, ex.: '2026-10-12 08:00' (padrão: agora).")
    ap.add_argument("--inicio", help="Início do período (padrão: segunda 00:00 da semana anterior).")
    ap.add_argument("--fim", help="Fim exclusivo do período (padrão: segunda 00:00 da semana da referência).")
    ap.add_argument("--json-out", help="Grava o JSON completo neste arquivo.")
    ap.add_argument("--txt-out", help="Grava o resumo em texto neste arquivo.")
    ap.add_argument("--saida", choices=["json", "texto", "nenhuma"], default="json", help="O que imprimir (padrão: json).")
    ap.add_argument("--servir", action="store_true", help="Sobe um serviço HTTP local em 127.0.0.1.")
    ap.add_argument("--porta", type=int, default=8002)
    a = ap.parse_args(argv)
    if a.servir:
        servir(a)
        return 0
    try:
        ref = parse_data(a.ref) if a.ref else agora_brasilia()
        ini = parse_data(a.inicio) if a.inicio else None
        fim = parse_data(a.fim) if a.fim else None
        segredo = os.environ.get(a.segredo_env) if a.lote else None
        ind = gerar(a.db, ref, ini, fim, a.lote, segredo)
    except (ValueError, FileNotFoundError, sqlite3.Error) as exc:
        print(json.dumps({"erro": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False), file=sys.stderr)
        return 2
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(ind, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if a.txt_out:
        Path(a.txt_out).write_text(ind["resumo_texto"] + "\n", encoding="utf-8")
    if a.saida == "json":
        print(json.dumps(ind, ensure_ascii=False, indent=2))
    elif a.saida == "texto":
        print(ind["resumo_texto"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
