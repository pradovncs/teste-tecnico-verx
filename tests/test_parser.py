import os

from src.io.parser import ConsultaParser

MOCK_DIR = os.path.join(os.path.dirname(__file__), "mocks")


def _load(name):
    with open(os.path.join(MOCK_DIR, name), encoding="utf-8") as f:
        return f.read()


class TestParse:
    def test_parses_table_result(self):
        parser = ConsultaParser()
        result = parser.parse(_load("resultado.html"))

        assert len(result) == 1
        c = result[0]
        assert c.cnpj == "11.222.333/0001-81"
        assert c.inscricao_estadual == "111.111.111.111"
        assert c.nome_empresarial == "EMPRESA EXEMPLO LTDA"
        assert c.situacao_cadastral == "Ativo"

    def test_extras_captured(self):
        parser = ConsultaParser()
        c = parser.parse(_load("resultado.html"))[0]
        assert c.extras.get("municipio") == "SAO PAULO"

    def test_not_found_returns_empty(self):
        html = "<html><body>Nenhum registro foi encontrado.</body></html>"
        assert ConsultaParser().parse(html) == []

    def test_empty_html_returns_empty(self):
        assert ConsultaParser().parse("<html></html>") == []

    def test_parses_aspnet_label_spans(self):
        html = """
        <html><body>
          <span id="ctl00_conteudoPrincipal_lblCNPJ">11.222.333/0001-81</span>
          <span id="ctl00_conteudoPrincipal_lblNomeEmpresarial">ACME SA</span>
        </body></html>
        """
        c = ConsultaParser().parse(html)[0]
        assert c.cnpj == "11.222.333/0001-81"
        assert c.nome_empresarial == "ACME SA"

    def test_result_without_cnpj_ignored(self):
        html = "<table><tr><th>Município:</th><td>SP</td></tr></table>"
        assert ConsultaParser().parse(html) == []
