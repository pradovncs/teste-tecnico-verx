import logging
import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from src.core.exceptions import ParseError
from src.core.interfaces import IParser
from src.core.models import Contribuinte

logger = logging.getLogger(__name__)

# Rótulos do CADESP -> atributos mapeados do modelo Contribuinte.
_FIELD_MAP = {
    "cnpj": "cnpj",
    "ie": "inscricao_estadual",
    "inscricaoestadual": "inscricao_estadual",
    "nomeempresarial": "nome_empresarial",
    "razaosocial": "nome_empresarial",
    "situacaocadastralvigente": "situacao_cadastral",
    "situacaocadastral": "situacao_cadastral",
    "situacao": "situacao_cadastral",
}

_NOT_FOUND_MARKERS = (
    "não foi encontrado",
    "nao foi encontrado",
    "nenhum registro",
    "não há dados",
)

_KEY_RE = re.compile(r"[^a-z0-9]")


def _normalize_label(label: str) -> str:
    """Normaliza um rótulo (sem acento aproximado, sem pontuação, minúsculo)."""
    text = label.strip().lower()
    replacements = {
        "ã": "a", "á": "a", "â": "a", "à": "a",
        "é": "e", "ê": "e", "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u", "ç": "c",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return _KEY_RE.sub("", text)


class ConsultaParser(IParser):
    """Extrai os dados cadastrais do HTML de resultado do CADESP."""

    def parse(self, html: str) -> List[Contribuinte]:
        """Converte o HTML de resultado numa lista de ``Contribuinte``.

        Args:
            html: HTML da página após a consulta.

        Returns:
            Lista com o contribuinte encontrado, ou lista vazia se não houver.

        Raises:
            ParseError: Se o HTML não puder ser analisado.
        """
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception as exc:
            raise ParseError(f"Falha ao analisar o HTML: {exc}") from exc

        text = soup.get_text(" ", strip=True).lower()
        if any(marker in text for marker in _NOT_FOUND_MARKERS):
            logger.info("Consulta sem resultados para o CNPJ informado")
            return []

        pairs = self._extract_pairs(soup)
        if not pairs:
            logger.info("Nenhum par rótulo/valor extraído do resultado")
            return []

        contribuinte = self._build_contribuinte(pairs)
        if contribuinte is None:
            return []
        return [contribuinte]

    def _extract_pairs(self, soup) -> Dict[str, str]:
        """Coleta pares rótulo->valor de tabelas e de spans de label do ASP.NET."""
        pairs: Dict[str, str] = {}

        # 1) Linhas de tabela com duas células (rótulo | valor).
        for row in soup.select("table tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) == 2:
                label = cells[0].get_text(" ", strip=True).rstrip(":")
                value = cells[1].get_text(" ", strip=True)
                if label and value:
                    pairs.setdefault(_normalize_label(label), value)

        # 2) Pares <dt>/<dd>.
        for dt in soup.find_all("dt"):
            dd = dt.find_next_sibling("dd")
            if dd:
                label = dt.get_text(" ", strip=True).rstrip(":")
                value = dd.get_text(" ", strip=True)
                if label and value:
                    pairs.setdefault(_normalize_label(label), value)

        # 3) Spans gerados pelo ASP.NET (id "...lblNomeEmpresarial" etc.).
        for span in soup.select('span[id*="lbl"], span[id*="Lbl"]'):
            span_id = span.get("id", "")
            key = span_id.split("_")[-1]
            key = re.sub(r"^lbl", "", key, flags=re.IGNORECASE)
            value = span.get_text(" ", strip=True)
            if key and value:
                pairs.setdefault(_normalize_label(key), value)

        logger.info("Extraídos %d pares rótulo/valor", len(pairs))
        return pairs

    def _build_contribuinte(self, pairs: Dict[str, str]) -> Optional[Contribuinte]:
        """Monta o modelo Contribuinte a partir dos pares extraídos."""
        mapped: Dict[str, str] = {}
        extras: Dict[str, str] = {}

        for key, value in pairs.items():
            attr = _FIELD_MAP.get(key)
            if attr:
                mapped.setdefault(attr, value)
            else:
                extras[key] = value

        cnpj = mapped.get("cnpj", "")
        if not cnpj:
            logger.warning("Resultado sem CNPJ identificável — ignorando")
            return None

        return Contribuinte(
            cnpj=cnpj,
            inscricao_estadual=mapped.get("inscricao_estadual", ""),
            nome_empresarial=mapped.get("nome_empresarial", ""),
            situacao_cadastral=mapped.get("situacao_cadastral", ""),
            extras=extras,
        )
