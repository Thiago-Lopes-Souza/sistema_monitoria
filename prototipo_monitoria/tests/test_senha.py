"""Testes do hash de senha (decisão D2)."""

import unittest
from unittest import mock

from monitorias.dominio import senha
from monitorias.dominio.excecoes import DadosInvalidos
from monitorias.dominio.senha import conferir_senha, gerar_hash_senha


@mock.patch.object(senha, "ITERACOES", 1_000)
class TestSenha(unittest.TestCase):

    def test_senha_certa_confere_e_errada_nao(self):
        senha_hash, sal = gerar_hash_senha("ana123")
        self.assertTrue(conferir_senha("ana123", senha_hash, sal))
        self.assertFalse(conferir_senha("ana124", senha_hash, sal))
        self.assertFalse(conferir_senha("", senha_hash, sal))

    def test_hash_nao_contem_a_senha_e_sal_muda_a_cada_vez(self):
        hash1, sal1 = gerar_hash_senha("ana123")
        hash2, sal2 = gerar_hash_senha("ana123")
        self.assertNotIn(b"ana123", hash1)
        self.assertNotEqual(sal1, sal2)
        self.assertNotEqual(hash1, hash2)
        self.assertEqual(len(sal1), senha.TAMANHO_SAL)

    def test_senha_vazia_e_recusada(self):
        for vazia in ("", "   "):
            with self.subTest(vazia=vazia):
                with self.assertRaises(DadosInvalidos):
                    gerar_hash_senha(vazia)


class TestIteracoesReais(unittest.TestCase):

    def test_valor_padrao_e_o_recomendado(self):
        self.assertGreaterEqual(senha.ITERACOES, 600_000)


if __name__ == "__main__":
    unittest.main()
