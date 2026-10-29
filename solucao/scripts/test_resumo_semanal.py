#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes automáticos do resumo semanal. Usam bancos temporários criados na hora;
não tocam em mesa_certa.db nem em mesa_certa.original.db.

Rodar:  py -m unittest solucao/scripts/test_resumo_semanal.py -v   (na raiz do repositório)
"""
import datetime as dt
import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import resumo_semanal as rs  # noqa: E402

D = dt.datetime


class HorasUteis(unittest.TestCase):
    def test_mesmo_dia(self):
        self.assertAlmostEqual(rs.horas_uteis(D(2026, 10, 7, 9, 0), D(2026, 10, 7, 11, 30)), 2.5)

    def test_sexta_17h_ate_segunda_8h_vale_1h(self):
        self.assertAlmostEqual(rs.horas_uteis(D(2026, 10, 9, 17, 0), D(2026, 10, 12, 8, 0)), 1.0)

    def test_criado_no_sabado_conta_a_partir_de_segunda(self):
        self.assertAlmostEqual(rs.horas_uteis(D(2026, 10, 10, 12, 0), D(2026, 10, 12, 9, 0)), 1.0)

    def test_virada_de_dia(self):
        self.assertAlmostEqual(rs.horas_uteis(D(2026, 10, 7, 16, 0), D(2026, 10, 8, 10, 0)), 4.0)

    def test_fora_do_expediente_e_zero(self):
        self.assertEqual(rs.horas_uteis(D(2026, 10, 7, 19, 0), D(2026, 10, 7, 23, 0)), 0.0)
        self.assertEqual(rs.horas_uteis(D(2026, 10, 7, 10, 0), D(2026, 10, 7, 9, 0)), 0.0)

    def test_fim_de_semana_inteiro(self):
        self.assertEqual(rs.horas_uteis(D(2026, 10, 10, 0, 0), D(2026, 10, 11, 23, 59)), 0.0)


class Datas(unittest.TestCase):
    def test_periodo_padrao_segunda_08h(self):
        ini, fim = rs.periodo_padrao(D(2026, 10, 12, 8, 0))
        self.assertEqual((ini, fim), (D(2026, 10, 5), D(2026, 10, 12)))

    def test_periodo_padrao_meio_da_semana(self):
        ini, fim = rs.periodo_padrao(D(2026, 10, 14, 15, 0))
        self.assertEqual((ini, fim), (D(2026, 10, 5), D(2026, 10, 12)))

    def test_parse(self):
        self.assertEqual(rs.parse_data("2026-10-12 08:00"), D(2026, 10, 12, 8, 0))
        self.assertEqual(rs.parse_data("12/10/2026 08:00"), D(2026, 10, 12, 8, 0))
        with self.assertRaises(ValueError):
            rs.parse_data("ontem")


class Normalizacao(unittest.TestCase):
    def test_email_e_telefone(self):
        self.assertEqual(rs.norm_email("  Maria@Gmail.COM "), "maria@gmail.com")
        self.assertEqual(rs.norm_telefone("+55 47 97030-4750"), "47970304750")
        self.assertEqual(rs.norm_telefone("(47) 7030-4750"), "4770304750")
        self.assertEqual(rs.telefone_sem_nono_digito("47 97030 4750"), rs.telefone_sem_nono_digito("(47) 7030-4750"))


class Classificacao(unittest.TestCase):
    def c(self, msg, nome="Ana", email="ana@gmail.com", rest="Pizzaria", ass="nao_verificada"):
        return rs.classificar_pedido(nome, email, rest, msg, ass)

    def test_comercial(self):
        self.assertEqual(self.c("Quero uma demonstração do cardápio digital"), "comercial")
        self.assertEqual(self.c("Quero testar o sistema de vocês. Como começo?"), "comercial")
        self.assertEqual(self.c("Quanto custa?"), "comercial")

    def test_suporte_fornecedor_spam(self):
        self.assertEqual(self.c("Esqueci minha senha de acesso ao painel"), "suporte")
        self.assertEqual(self.c("Somos uma fornecedora de embalagens para delivery"), "fornecedor")
        self.assertEqual(self.c("Compre seguidores baratos!"), "spam")

    def test_teste_e_lixo(self):
        self.assertEqual(self.c("testando o formulário"), "teste")
        self.assertEqual(self.c("qualquer", nome="Fulano de Tal", email="dev.teste@mesacerta.com.br"), "teste")
        self.assertEqual(self.c("???", nome="x", email="user1@gmail.com", rest="."), "lixo_provavel")
        self.assertEqual(self.c("", nome="Henrique", email="u@mail.com", rest="."), "lixo_provavel")

    def test_assinatura_invalida_tem_precedencia(self):
        self.assertEqual(self.c("Quero uma demonstração", ass="invalida"), "assinatura_invalida")


def criar_banco(caminho: Path) -> None:
    con = sqlite3.connect(caminho)
    con.executescript("""
    CREATE TABLE negocios_crm (deal_id INTEGER PRIMARY KEY, criado_em TEXT NOT NULL, atualizado_em TEXT NOT NULL,
      nome TEXT, email TEXT, telefone TEXT, restaurante TEXT, etapa TEXT NOT NULL, origem TEXT, responsavel TEXT,
      primeiro_contato_em TEXT, atualizado_por TEXT);
    CREATE TABLE historico_etapas (deal_id INTEGER, etapa TEXT, em TEXT);
    CREATE TABLE pedidos_formulario (id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT, criado_em TEXT, nome TEXT,
      email TEXT, telefone TEXT, restaurante TEXT, mensagem TEXT, origem TEXT, recebido_em TEXT);
    """)
    negocios = [
        # id, criado, atualizado, nome, email, tel, rest, etapa, origem, resp, contato, por
        (1, "2026-10-05 09:00:00", "2026-10-05 10:00:00", "Ana", "ana@gmail.com", "11 90000 0001", "R1", "Contato", "Site", "sdr_1", "2026-10-05 10:00:00", "sdr_1"),   # 1h: no prazo
        (2, "2026-10-05 09:00:00", "2026-10-05 16:00:00", "Bia", "bia@gmail.com", "11 90000 0002", "R2", "Contato", "Site", "sdr_2", "2026-10-05 16:00:00", "sdr_3"),   # 7h: atrasado
        (3, "2026-10-06 09:00:00", "2026-10-06 09:00:00", "Caio", "caio@gmail.com", "11 90000 0003", "R3", "Novo", "Site", "sdr_2", None, "integracao"),                # sem contato, vencido
        (4, "2026-10-11 12:00:00", "2026-10-11 12:00:00", "Duda", "duda@gmail.com", "11 90000 0004", "R4", "Novo", "Site", "sdr_3", None, "integracao"),                # domingo: ainda no prazo
        (5, "2026-10-07 09:00:00", "2026-10-07 09:00:00", "Fulano de Tal", "teste@teste.com", "11 90000 0005", "asdf", "Novo", "Site", "sdr_1", None, "integracao"),     # teste
        (6, "2026-09-01 09:00:00", "2026-10-06 02:14:00", "Velho", "velho@gmail.com", "11 90000 0006", "R6", "Perdido", "Site", "sdr_1", None, "automacao_limpeza"),     # antigo
        (7, "2026-10-13 09:00:00", "2026-10-13 09:00:00", "Futuro", "futuro@gmail.com", "11 90000 0007", "R7", "Novo", "Site", "sdr_1", None, "integracao"),            # depois da referencia
    ]
    con.executemany("INSERT INTO negocios_crm VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", negocios)
    hist = [(1, "Novo", "2026-10-05 09:00:00"), (1, "Contato", "2026-10-05 10:00:00"),
            (2, "Novo", "2026-10-05 09:00:00"), (2, "Contato", "2026-10-05 16:00:00"),
            (3, "Novo", "2026-10-06 09:00:00"), (4, "Novo", "2026-10-11 12:00:00"), (5, "Novo", "2026-10-07 09:00:00"),
            (6, "Novo", "2026-09-01 09:00:00"), (6, "Perdido", "2026-10-06 02:14:00"), (7, "Novo", "2026-10-13 09:00:00")]
    con.executemany("INSERT INTO historico_etapas VALUES (?,?,?)", hist)
    # pedidos (UTC = Brasilia + 3h)
    ped = [
        ("e1", "2026-10-05T12:00:00Z", "Ana", "ana@gmail.com", "11 90000 0001", "R1", "Quero uma demonstração"),            # 09:00 BRT -> negocio 1
        ("e2", "2026-10-05T12:00:00Z", "Bia", "BIA@gmail.com ", "11 90000 0002", "R2", "Quero conhecer o sistema"),        # negocio 2 (e-mail com maiuscula/espaco)
        ("e3", "2026-10-06T12:00:00Z", "Caio", "caio@gmail.com", "11 90000 0003", "R3", "Gostaria de agendar uma demonstração"),
        ("e4", "2026-10-07T12:00:00Z", "Fulano de Tal", "teste@teste.com", "11 90000 0005", "asdf", "teste"),               # teste, tem negocio 5
        ("e5", "2026-10-08T12:00:00Z", "Eva", "eva@gmail.com", "11 90000 0009", "R9", "Quero contratar planos"),           # comercial SEM negocio
        ("e6", "2026-10-08T13:00:00Z", "Eva", "eva@gmail.com", "11 90000 0009", "R9", "Podem me ligar?"),                  # mesma pessoa pedindo de novo
        ("e7", "2026-10-09T12:00:00Z", "Gil", "gil@gmail.com", "11 90000 0010", "R10", "Esqueci minha senha"),             # suporte
        ("e8", "2026-10-04T12:00:00Z", "Velho", "velho@gmail.com", "11 90000 0006", "R6", "Quero ver uma demonstração"),   # fora do periodo (04/10)
    ]
    con.executemany("INSERT INTO pedidos_formulario (event_id,criado_em,nome,email,telefone,restaurante,mensagem) VALUES (?,?,?,?,?,?,?)", ped)
    con.commit()
    con.close()


class Indicadores(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = Path(cls.tmp.name) / "teste.db"
        criar_banco(cls.db)
        cls.hash_antes = hashlib.sha256(cls.db.read_bytes()).hexdigest()
        cls.ind = rs.gerar(str(cls.db), D(2026, 10, 12, 8, 0))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_periodo(self):
        r = self.ind["referencia"]
        self.assertEqual((r["periodo_inicio"], r["periodo_fim_exclusivo"]), ("2026-10-05 00:00:00", "2026-10-12 00:00:00"))

    def test_funil_ignora_negocio_criado_depois_da_referencia(self):
        f = self.ind["indicadores_comprovados"]["funil"]
        self.assertEqual(f["total"], 6)
        self.assertEqual(f["por_etapa"], {"Novo": 3, "Contato": 2, "Reunião marcada": 0, "Reunião realizada": 0, "Perdido": 1})

    def test_criados_e_atualizados(self):
        c = self.ind["indicadores_comprovados"]["negocios_criados_e_atualizados"]
        self.assertEqual(c["criados"], 5)           # 1,2,3,4,5
        self.assertEqual(c["atualizados"], 6)       # 1,2,3,4,5 + o antigo 6 (limpeza)
        self.assertEqual(c["atualizados_que_foram_criados_antes_do_periodo"], 1)
        self.assertEqual(c["atualizados_pela_automacao_de_limpeza"], 1)

    def test_pedidos_e_reconciliacao(self):
        e = self.ind["estimativas"]
        self.assertEqual(e["pedidos_do_periodo"]["pedidos_distintos"], 7)           # e8 (04/10) fica de fora
        self.assertEqual(e["pedidos_do_periodo"]["por_classe"]["comercial"], 5)
        rc = e["reconciliacao_pedidos_comerciais_com_o_crm"]
        self.assertEqual((rc["viraram_negocio"], rc["pessoa_ja_tinha_negocio"], rc["sem_correspondencia_no_crm"]), (3, 0, 2))
        self.assertEqual([a["event_id"] for a in rc["ausentes"]], ["e5", "e6"])
        self.assertEqual(e["pedidos_do_periodo"]["pessoas_distintas_entre_comerciais"], 4)   # Ana, Bia, Caio, Eva
        self.assertEqual(e["pedidos_do_periodo"]["emails_que_pediram_mais_de_uma_vez"], 1)
        self.assertEqual(e["pedidos_nao_comerciais_e_o_crm"]["teste"]["negocios_no_crm"], 1)

    def test_prazo_primeiro_contato(self):
        t = self.ind["estimativas"]["prazo_primeiro_contato_pedidos_comerciais"]["por_responsavel"]
        self.assertEqual(t["sdr_1"]["contato_no_prazo"], 1)
        self.assertEqual(t["sdr_2"]["contato_atrasado"], 1)
        self.assertEqual(t["sdr_2"]["sem_contato_prazo_vencido"], 1)
        self.assertEqual(t["TOTAL"]["decidiveis"], 3)
        self.assertNotIn("sdr_3", t)             # o negócio do sdr_3 não nasceu de pedido comercial
        todos = self.ind["indicadores_comprovados"]["prazo_primeiro_contato_todos_os_negocios_criados"]["por_responsavel"]
        self.assertEqual(todos["sdr_3"]["sem_contato_ainda_no_prazo"], 1)    # criado no domingo
        self.assertEqual(todos["TOTAL"]["negocios"], 5)

    def test_sem_retorno(self):
        s = self.ind["indicadores_comprovados"]["sem_retorno_na_referencia"]
        self.assertEqual(s["em_novo_sem_contato"], 3)       # 3, 4, 5
        self.assertEqual(s["com_prazo_vencido"], 2)         # 3 e 5; o 4 foi criado no domingo
        self.assertEqual(s["vencidos_por_responsavel"], {"sdr_2": 1, "sdr_1": 1})

    def test_contato_depois_da_referencia_nao_conta(self):
        con = rs.abrir_somente_leitura(self.db)
        try:
            neg = rs.carregar_negocios(con, D(2026, 10, 5, 9, 30))
        finally:
            con.close()
        n1 = next(n for n in neg if n["deal_id"] == 1)
        self.assertIsNone(n1["contato"])             # contato foi às 10:00, depois da referência 09:30
        self.assertEqual(n1["etapa_na_ref"], "Novo")

    def test_json_serializavel_e_com_as_quatro_secoes(self):
        json.dumps(self.ind, ensure_ascii=False)
        for k in ("indicadores_comprovados", "estimativas", "dados_incompletos", "limitacoes", "resumo_texto"):
            self.assertIn(k, self.ind)

    def test_somente_leitura(self):
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(), self.hash_antes)
        con = rs.abrir_somente_leitura(self.db)
        try:
            with self.assertRaises(sqlite3.OperationalError):
                con.execute("DELETE FROM negocios_crm")
        finally:
            con.close()
        self.assertEqual(hashlib.sha256(self.db.read_bytes()).hexdigest(), self.hash_antes)

    def test_aviso_de_banco_desatualizado(self):
        codigos = lambda ind: [d["codigo"] for d in ind["dados_incompletos"]]
        self.assertNotIn("banco_do_crm_desatualizado", codigos(self.ind))
        velho = rs.gerar(str(self.db), D(2026, 11, 30, 8, 0))
        self.assertIn("banco_do_crm_desatualizado", codigos(velho))
        self.assertIn("ATENÇÃO", velho["resumo_texto"])

    def test_banco_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            rs.gerar(str(Path(self.tmp.name) / "nao_existe.db"), D(2026, 10, 12, 8, 0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
