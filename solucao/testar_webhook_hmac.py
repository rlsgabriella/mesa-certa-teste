#!/usr/bin/env python3
"""Gera uma assinatura HMAC-SHA256 valida e envia um evento ao webhook do n8n.

Por que este script existe
---------------------------
O HMAC e calculado sobre os BYTES EXATOS do corpo. Se o cliente assina uma
string e deixa alguma camada (ConvertTo-Json, Invoke-RestMethod, etc.)
re-serializar o JSON antes de enviar, os bytes mudam e a assinatura nao bate,
mesmo com o segredo certo. Este script evita isso: monta o corpo UMA vez como
string, assina ESSA string e envia EXATAMENTE os mesmos bytes.

Seguranca
---------
- O segredo vem da variavel de ambiente MESA_CERTA_HMAC_SECRET. Nunca e impresso
  nem gravado. Se faltar, o script aborta.
- A assinatura (hash) nao e segredo e pode ser exibida.

Nao desativa nem contorna a validacao: apenas produz uma assinatura correta.
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone


def montar_corpo_str(args) -> str:
    """Monta o corpo do evento como UMA string JSON. Essa string e,
    simultaneamente, o que assinamos e o que enviamos (bytes identicos)."""
    corpo = {
        "event_id": args.event_id,
        "criado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nome": args.nome,
        "email": args.email,
        "telefone": args.telefone,
        "restaurante": args.restaurante,
        "mensagem": args.mensagem,
        "origem": args.origem,
    }
    return json.dumps(corpo, ensure_ascii=False, separators=(",", ":"))


def assinar(corpo_bytes: bytes, segredo: str) -> str:
    return "sha256=" + hmac.new(
        segredo.encode("utf-8"), corpo_bytes, hashlib.sha256
    ).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Testa a validacao HMAC do webhook do n8n.")
    ap.add_argument(
        "--url",
        default="http://127.0.0.1:5678/webhook-test/mesa-certa/marketing",
        help="URL do webhook (use 127.0.0.1, nao localhost, no Windows).",
    )
    ap.add_argument("--event-id", default=f"evt_suporte_{uuid.uuid4().hex[:8]}",
                    help="event_id unico (padrao: gerado).")
    ap.add_argument("--nome", default="Joana Suporte")
    ap.add_argument("--email", default="joana.suporte@exemplo.com.br")
    ap.add_argument("--telefone", default="+55 11 98888-0001")
    ap.add_argument("--restaurante", default="Restaurante Boa Mesa")
    ap.add_argument(
        "--mensagem",
        default="Esqueci minha senha de acesso ao painel, ja sou cliente de voces.",
        help="Mensagem; o padrao e um pedido de SUPORTE (nao deve virar negocio).",
    )
    ap.add_argument("--origem", default="site")

    ap.add_argument("--alterar-corpo-apos-assinar", action="store_true",
                    help="Assina, depois altera o corpo -> deve dar invalida.")
    ap.add_argument("--segredo-errado", action="store_true",
                    help="Assina com segredo errado -> deve dar invalida.")
    ap.add_argument("--apenas-assinar", action="store_true",
                    help="So gera e mostra a assinatura; nao envia (teste local).")
    args = ap.parse_args()

    segredo = os.environ.get("MESA_CERTA_HMAC_SECRET")
    if not segredo:
        print("ERRO: variavel de ambiente MESA_CERTA_HMAC_SECRET nao definida.",
              file=sys.stderr)
        print('Defina com: $env:MESA_CERTA_HMAC_SECRET = "<segredo>"', file=sys.stderr)
        return 2

    corpo_str = montar_corpo_str(args)
    corpo_bytes = corpo_str.encode("utf-8")

    segredo_para_assinar = segredo + "_ERRADO" if args.segredo_errado else segredo
    assinatura = assinar(corpo_bytes, segredo_para_assinar)

    corpo_enviado = corpo_bytes
    if args.alterar_corpo_apos_assinar:
        corpo_obj = json.loads(corpo_str)
        corpo_obj["mensagem"] = corpo_obj["mensagem"] + " [ALTERADO]"
        corpo_enviado = json.dumps(
            corpo_obj, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")

    print(f"event_id        : {args.event_id}")
    print(f"bytes do corpo  : {len(corpo_enviado)}")
    print(f"X-Signature     : {assinatura}")
    print(f"segredo errado  : {args.segredo_errado}")
    print(f"corpo alterado  : {args.alterar_corpo_apos_assinar}")

    if args.apenas_assinar:
        print("\n[--apenas-assinar] Nao enviado. Assinatura gerada localmente.")
        return 0

    req = urllib.request.Request(
        args.url,
        data=corpo_enviado,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Signature": assinatura,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"\nHTTP {r.status}")
            print(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        print(f"\nHTTP {e.code}")
        print(e.read().decode("utf-8", errors="replace"))
    except urllib.error.URLError as e:
        print(f"\nFALHA DE CONEXAO: {e.reason}", file=sys.stderr)
        print("O n8n esta no ar e o workflow em modo de teste (Listen for Test Event)?",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
