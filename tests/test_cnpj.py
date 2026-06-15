import pytest

from src.core import cnpj as cnpj_mod
from src.core.exceptions import InvalidCNPJError

VALID = "11.222.333/0001-81"
VALID_DIGITS = "11222333000181"


class TestNormalize:
    def test_strips_mask(self):
        assert cnpj_mod.normalize(VALID) == VALID_DIGITS

    def test_handles_none(self):
        assert cnpj_mod.normalize(None) == ""

    def test_handles_empty(self):
        assert cnpj_mod.normalize("") == ""


class TestIsValid:
    def test_valid_cnpj(self):
        assert cnpj_mod.is_valid(VALID) is True
        assert cnpj_mod.is_valid(VALID_DIGITS) is True

    def test_invalid_check_digits(self):
        assert cnpj_mod.is_valid("11222333000182") is False

    def test_wrong_length(self):
        assert cnpj_mod.is_valid("123") is False

    def test_all_same_digits(self):
        assert cnpj_mod.is_valid("00000000000000") is False


class TestValidate:
    def test_returns_digits(self):
        assert cnpj_mod.validate(VALID) == VALID_DIGITS

    def test_raises_on_invalid(self):
        with pytest.raises(InvalidCNPJError):
            cnpj_mod.validate("11222333000182")


class TestFormatMask:
    def test_formats_digits(self):
        assert cnpj_mod.format_mask(VALID_DIGITS) == VALID

    def test_returns_input_when_not_14_digits(self):
        assert cnpj_mod.format_mask("123") == "123"
