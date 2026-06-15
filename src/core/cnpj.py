import re

from src.core.exceptions import InvalidCNPJError

_NON_DIGIT = re.compile(r"\D")


def normalize(cnpj: str) -> str:
    """Remove qualquer caractere não numérico do CNPJ.

    Args:
        cnpj: CNPJ em qualquer formato (com ou sem máscara).

    Returns:
        String contendo apenas os 14 dígitos do CNPJ.
    """
    return _NON_DIGIT.sub("", cnpj or "")


def _check_digit(digits: str, weights: list) -> int:
    """Calcula um dígito verificador de CNPJ a partir dos pesos informados."""
    total = sum(int(d) * w for d, w in zip(digits, weights))
    rest = total % 11
    return 0 if rest < 2 else 11 - rest


def is_valid(cnpj: str) -> bool:
    """Valida um CNPJ usando o algoritmo oficial dos dígitos verificadores."""
    digits = normalize(cnpj)
    if len(digits) != 14 or len(set(digits)) == 1:
        return False

    first = _check_digit(digits[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    second = _check_digit(digits[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return digits[12] == str(first) and digits[13] == str(second)


def validate(cnpj: str) -> str:
    """Normaliza e valida o CNPJ, retornando os 14 dígitos.

    Raises:
        InvalidCNPJError: Se o CNPJ for inválido.
    """
    digits = normalize(cnpj)
    if not is_valid(digits):
        raise InvalidCNPJError(f"CNPJ inválido: {cnpj!r}")
    return digits


def format_mask(cnpj: str) -> str:
    """Formata os dígitos do CNPJ com a máscara ``00.000.000/0000-00``."""
    d = normalize(cnpj)
    if len(d) != 14:
        return cnpj
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
