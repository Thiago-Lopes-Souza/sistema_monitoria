# sistema_monitoria

Um sistema desenvolvido em Python para consulta e agendamento de monitorias por matéria, do curso de Engenharia de Sistemas da UFMG.

**O sistema fica na pasta [`prototipo_monitoria/`](prototipo_monitoria/).** Entre nela antes de rodar qualquer comando:

```
cd prototipo_monitoria
python -m monitorias.persistencia.seed_demo   # prepara a base de dados (uma vez)
python -m monitorias                          # inicia o menu
python -m unittest discover -s tests -v       # roda os testes
```

As instruções completas (versão do Python, senhas de demonstração, dados fictícios e cenários) estão em
[`prototipo_monitoria/README.md`](prototipo_monitoria/README.md).

Fora do ZIP de entrega:
- `EVIDENCIAS.md`: verificação da versão final (cenários, testes, defeitos e pendências);
- `docs/`: persistência, diagramas e as evidências do protótipo.

O ZIP enviado contém **só** a pasta `prototipo_monitoria/`, sem a base `.db`.
