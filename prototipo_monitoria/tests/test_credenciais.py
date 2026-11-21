"""Testes da geração e verificação de senhas (com hashes e sal)."""

import unittest
from monitorias.dominio.credenciais import gerar_hash_senha, verificar_senha

class TestCredenciais(unittest.TestCase):

    def test_senha_correta(self):
        senha_hash, sal = gerar_hash_senha("monitor123")
        self.assertTrue(verificar_senha("monitor123", senha_hash, sal))

    def test_senha_incorreta(self):
        senha_hash, sal = gerar_hash_senha("monitor123")
        self.assertFalse(verificar_senha("senha_errada", senha_hash, sal))

    def test_senha_diferencia_maiusculas(self):
        senha_hash, sal = gerar_hash_senha("Monitor123")
        self.assertFalse(verificar_senha("monitor123", senha_hash, sal))

    def test_mesma_senha_gera_sais_e_hashes_diferentes(self):
        hash1, sal1 = gerar_hash_senha("monitor123")
        hash2, sal2 = gerar_hash_senha("monitor123")

        self.assertNotEqual(sal1, sal2)
        self.assertNotEqual(hash1, hash2)
        self.assertTrue(verificar_senha("monitor123", hash1, sal1))
        self.assertTrue(verificar_senha("monitor123", hash2, sal2))

    def test_sal_errado_rejeita_senha_correta(self):
        senha_hash, _ = gerar_hash_senha("monitor123")
        _, outro_sal = gerar_hash_senha("monitor123")
        self.assertFalse(verificar_senha("monitor123", senha_hash, outro_sal))

    def test_hash_e_sal_sao_bytes_do_tamanho_esperado(self):
        senha_hash, sal = gerar_hash_senha("monitor123")
        self.assertIsInstance(senha_hash, bytes)
        self.assertIsInstance(sal, bytes)
        self.assertEqual(len(senha_hash), 32)  # SHA-256
        self.assertEqual(len(sal), 16)

    def test_senha_com_acentos(self):
        senha_hash, sal = gerar_hash_senha("MonitorÁrvore#2026")
        self.assertTrue(
            verificar_senha("MonitorÁrvore#2026", senha_hash, sal)
        )

    def test_gerar_hash_rejeita_senha_vazia(self):
        with self.assertRaises(ValueError):
            gerar_hash_senha("")

    def test_gerar_hash_rejeita_entrada_nao_textual(self):
        for entrada in (None, 123):
            with self.subTest(entrada=entrada):
                with self.assertRaises(ValueError):
                    gerar_hash_senha(entrada)

    def test_verificar_senha_nao_textual_retorna_false(self):
        senha_hash, sal = gerar_hash_senha("monitor123")
        self.assertFalse(verificar_senha(None, senha_hash, sal))


if __name__ == "__main__":
    unittest.main()
