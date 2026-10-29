#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida o resumo semanal contra a apuração histórica de 29/10/2026 (referência: 12/10/2026 08:00).

- Copia mesa_certa.original.db para uma pasta temporária e roda os cálculos sobre a CÓPIA, em modo somente leitura.
- Confere que o original e a cópia não mudaram (SHA-256 antes e depois).
- Compara cada indicador com o valor apurado antes, por consulta direta ao banco e ao lote.
- NÃO ajusta nenhum número: se divergir, mostra a diferença e sai com código 1.

Os valores esperados abaixo são a referência da validação (não entram no cálculo do resumo).
Segredo HMAC: lido da variável MESA_CERTA_HMAC_SECRET, só para conferir as assinaturas do lote.

Rodar na raiz do repositório:  py solucao\\scripts\\validar_resumo_historico.py [--saida-dir solucao\\evidencias]
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import resumo_semanal as rs  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
REF = "2026-10-12 08:00"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida-dir", help="Pasta para gravar o JSON, o texto e o relatório de validação.")
    a = ap.parse_args()
    segredo = os.environ.get("MESA_CERTA_HMAC_SECRET")
    if not segredo:
        print("ERRO: defina MESA_CERTA_HMAC_SECRET na sessão (o segredo não é impresso).", file=sys.stderr)
        return 2
    original = RAIZ / "mesa_certa.original.db"
    lote = RAIZ / "webhook" / "lote-webhook.jsonl"
    h_orig_antes = sha(original)
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "mesa_certa_copia.db"
        shutil.copyfile(original, copia)
        h_copia_antes = sha(copia)
        ind = rs.gerar(str(copia), rs.parse_data(REF), lote=str(lote), segredo=segredo)
        h_copia_depois = sha(copia)
    h_orig_depois = sha(original)

    c, e = ind["indicadores_comprovados"], ind["estimativas"]
    sla = e["prazo_primeiro_contato_pedidos_comerciais"]["por_responsavel"]["TOTAL"]
    rc = e["reconciliacao_pedidos_comerciais_com_o_crm"]
    # (descrição, esperado, obtido, de onde veio o esperado)
    itens = [
        ("Funil: total de negócios", 391, c["funil"]["total"], "contagem em negocios_crm (apuração de 29/10)"),
        ("Funil: Novo", 106, c["funil"]["por_etapa"]["Novo"], "idem"),
        ("Funil: Contato", 133, c["funil"]["por_etapa"]["Contato"], "idem"),
        ("Funil: Reunião marcada", 43, c["funil"]["por_etapa"]["Reunião marcada"], "idem"),
        ("Funil: Reunião realizada", 37, c["funil"]["por_etapa"]["Reunião realizada"], "idem"),
        ("Funil: Perdido", 72, c["funil"]["por_etapa"]["Perdido"], "idem"),
        ("Negócios atualizados na semana (planilha: 187)", 187, c["negocios_criados_e_atualizados"]["atualizados"], "planilha-chefia.csv"),
        ("Negócios criados na semana", 142, c["negocios_criados_e_atualizados"]["criados"], "criado_em na semana"),
        ("Pedidos comerciais identificados no lote", 136, e["pedidos_do_periodo"]["comerciais"], "classificação da análise de 29/10"),
        ("Pedidos comerciais sem correspondência no CRM", 12, rc["sem_correspondencia_no_crm"], "idem"),
        ("Negócios sem contato com prazo vencido (Novo)", 68, c["sem_retorno_na_referencia"]["com_prazo_vencido"], "idem"),
        ("Pedidos distintos na semana (inclui 3 com assinatura inválida)", 175, e["pedidos_do_periodo"]["pedidos_distintos"], "event_id distintos, semana em Brasília"),
        ("Pessoas distintas entre os comerciais", 111, e["pedidos_do_periodo"]["pessoas_distintas_entre_comerciais"], "união por e-mail/telefone"),
        ("Comerciais que viraram negócio", 99, rc["viraram_negocio"], "análise de 29/10"),
        ("Comerciais de quem já tinha negócio", 25, rc["pessoa_ja_tinha_negocio"], "idem"),
        ("Negócios de não comerciais no CRM (suporte+fornecedor+teste+spam+lixo)", 27,
         sum(v["negocios_no_crm"] for v in e["pedidos_nao_comerciais_e_o_crm"].values()), "idem"),
        ("Prazo: negócios de pedido comercial criados na semana", 99, sla["negocios"], "idem"),
        ("Prazo: contato dentro de 4 h úteis", 46, sla["contato_no_prazo"], "idem"),
        ("Prazo: contato atrasado", 16, sla["contato_atrasado"], "idem"),
        ("Prazo: sem contato e vencido", 13, sla["sem_contato_prazo_vencido"], "idem"),
        ("Sem retorno vencido que são pedidos comerciais", 47, e["sem_retorno_por_tipo_de_negocio"]["vencidos_por_tipo"].get("comercial", 0), "idem"),
        ("Assinaturas inválidas no lote", 3, ind["fontes"]["lote"]["assinatura_invalida"], "conferência HMAC"),
        ("Entregas do lote com JSON inválido", 2, ind["fontes"]["lote"]["json_invalidos"], "leitura do lote"),
    ]
    linhas, divergencias = [], 0
    for desc, esperado, obtido, origem in itens:
        ok = esperado == obtido
        divergencias += 0 if ok else 1
        linhas.append({"indicador": desc, "esperado": esperado, "obtido": obtido, "confere": ok, "origem_do_esperado": origem})
    integridade = {
        "original_inalterado": h_orig_antes == h_orig_depois, "copia_inalterada": h_copia_antes == h_copia_depois,
        "copia_identica_ao_original": h_orig_antes == h_copia_antes, "sha256_original": h_orig_antes,
    }
    # a mediana difere da apuração anterior (2,15) só pela definição: média dos dois valores centrais
    nota = ("Mediana de horas úteis até o contato: este script usa a mediana estatística (média dos dois valores centrais "
            f"quando o total é par): {sla['mediana_horas_uteis']}. A apuração de 29/10 usou o valor central superior (2,15). "
            "Não é divergência de dados, só de definição.")

    print(f"Validação do resumo semanal, referência {REF} (Brasília)\n")
    print(f"{'Indicador':<72} {'Esperado':>9} {'Obtido':>9}  Confere")
    for l in linhas:
        print(f"{l['indicador']:<72} {l['esperado']:>9} {l['obtido']:>9}  {'sim' if l['confere'] else 'NÃO'}")
    print("\nIntegridade:", json.dumps(integridade, ensure_ascii=False))
    print("Nota:", nota)
    print(f"\nResultado: {len(linhas) - divergencias} de {len(linhas)} conferem; {divergencias} divergem.")

    if a.saida_dir:
        d = Path(a.saida_dir)
        d.mkdir(parents=True, exist_ok=True)
        (d / "resumo-semanal-2026-10-12.json").write_text(json.dumps(ind, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (d / "resumo-semanal-2026-10-12.txt").write_text(ind["resumo_texto"] + "\n", encoding="utf-8")
        md = ["# Validação do resumo semanal: referência 12/10/2026 08:00 (Brasília)", "",
              "Script: `solucao/scripts/resumo_semanal.py`, executado em modo somente leitura sobre uma **cópia** de "
              "`mesa_certa.original.db` com o lote `webhook/lote-webhook.jsonl`. Nenhum número foi ajustado.", "",
              f"**Resultado: {len(linhas) - divergencias} de {len(linhas)} indicadores conferem; {divergencias} divergem.**", "",
              "| Indicador | Esperado | Obtido | Confere |", "|---|---:|---:|:---:|"]
        md += [f"| {l['indicador']} | {l['esperado']} | {l['obtido']} | {'sim' if l['confere'] else '**NÃO**'} |" for l in linhas]
        md += ["", "## Integridade", "",
               f"- Original inalterado: {integridade['original_inalterado']}; cópia inalterada: {integridade['copia_inalterada']}; "
               f"cópia idêntica ao original: {integridade['copia_identica_ao_original']}.",
               f"- SHA-256 do original: `{integridade['sha256_original']}`.", "", "## Nota", "", nota, "",
               "Arquivos gerados: `resumo-semanal-2026-10-12.json` (completo) e `resumo-semanal-2026-10-12.txt` (texto para a gestora)."]
        (d / "validacao-resumo-semanal-2026-10-12.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"\nArquivos gravados em {d}")
    return 1 if divergencias or not all(integridade[k] for k in ("original_inalterado", "copia_inalterada", "copia_identica_ao_original")) else 0


if __name__ == "__main__":
    raise SystemExit(main())
