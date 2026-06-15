from dataclasses import asdict, dataclass, field
from typing import Dict


@dataclass
class Contribuinte:
    """Representa um contribuinte retornado pela Consulta Pública do CADESP.

    A página da SEFAZ-SP retorna os dados cadastrais em pares rótulo/valor.
    Os campos mais comuns são mapeados explicitamente; quaisquer outros campos
    extraídos do resultado ficam em ``extras`` para não perder informação.
    """

    cnpj: str
    inscricao_estadual: str = ""
    nome_empresarial: str = ""
    situacao_cadastral: str = ""
    extras: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.cnpj or not self.cnpj.strip():
            raise ValueError("CNPJ do contribuinte não pode ser vazio")

    def to_dict(self) -> dict:
        """Converte para um dicionário plano (extras achatados no topo)."""
        data = asdict(self)
        extras = data.pop("extras", {}) or {}
        # Campos mapeados têm precedência sobre extras de mesmo nome.
        merged = {**extras, **{k: v for k, v in data.items()}}
        return merged
