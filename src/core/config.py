import logging
import os
from dataclasses import dataclass, field
from typing import Optional

BASE_URL = (
    "https://www.cadesp.fazenda.sp.gov.br/"
    "Pages/Cadastro/Consultas/ConsultaPublica/ConsultaPublica.aspx"
)


@dataclass(frozen=True)
class CrawlerConfig:
    """Configuração imutável do crawler do CADESP (SEFAZ-SP)."""

    base_url: str = BASE_URL
    timeout: int = 30
    output_path: str = field(default_factory=lambda: os.path.join("output", "cadesp.csv"))
    headless: bool = True

    # AntiCaptcha — a chave pode vir do ambiente para não ficar versionada.
    anticaptcha_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("ANTICAPTCHA_KEY")
    )
    # Quantas vezes tentar resolver o captcha antes de desistir.
    max_captcha_attempts: int = 3

    # Stealth — desligar para depuração.
    stealth: bool = True
    # Atraso "humano" (segundos) mínimo/máximo entre interações.
    min_delay: float = 0.4
    max_delay: float = 1.6


# Constantes de conveniência
_DEFAULT = CrawlerConfig()
TIMEOUT = _DEFAULT.timeout
OUTPUT_PATH = _DEFAULT.output_path
HEADLESS = _DEFAULT.headless

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(level: str = "INFO") -> None:
    """Configura o logging estruturado da aplicação."""
    log_level = os.environ.get("LOG_LEVEL", level).upper()
    logging.basicConfig(
        format=LOG_FORMAT,
        level=getattr(logging, log_level, logging.INFO),
    )
