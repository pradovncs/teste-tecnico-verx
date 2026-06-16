import pytest

from src.core.models import Contribuinte


class TestContribuinte:
    def test_creates_with_required_cnpj(self):
        c = Contribuinte(cnpj="11222333000181")
        assert c.cnpj == "11222333000181"
        assert c.inscricao_estadual == ""
        assert c.extras == {}

    def test_empty_cnpj_raises(self):
        with pytest.raises(ValueError):
            Contribuinte(cnpj="")

    def test_whitespace_cnpj_raises(self):
        with pytest.raises(ValueError):
            Contribuinte(cnpj="   ")

    def test_to_dict_flattens_extras(self):
        c = Contribuinte(
            cnpj="11222333000181",
            nome_empresarial="ACME",
            extras={"municipio": "SAO PAULO"},
        )
        data = c.to_dict()
        assert data["cnpj"] == "11222333000181"
        assert data["nome_empresarial"] == "ACME"
        assert data["municipio"] == "SAO PAULO"
        assert "extras" not in data

    def test_mapped_fields_take_precedence_over_extras(self):
        c = Contribuinte(cnpj="1", nome_empresarial="REAL", extras={"nome_empresarial": "FAKE"})
        assert c.to_dict()["nome_empresarial"] == "REAL"
