import argparse
import logging
import sys

from src.core.config import CrawlerConfig, setup_logging
from src.core.exceptions import CrawlerError
from src.crawler import CadespCrawler

logger = logging.getLogger(__name__)


def main():
    """Ponto de entrada CLI do crawler do CADESP (consulta por CNPJ)."""
    default = CrawlerConfig()

    parser = argparse.ArgumentParser(
        description="Crawler do CADESP (SEFAZ-SP) — consulta pública por CNPJ"
    )
    parser.add_argument(
        "--cnpj",
        required=True,
        help="CNPJ a consultar (com ou sem máscara)",
    )
    parser.add_argument(
        "--api-key",
        default=default.anticaptcha_key,
        help="Chave da API do AntiCaptcha (padrão: variável ANTICAPTCHA_KEY)",
    )
    parser.add_argument(
        "--output",
        default=default.output_path,
        help=f"Arquivo de saída CSV/JSON (padrão: {default.output_path})",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Executa o navegador com interface gráfica (útil para depurar)",
    )
    parser.add_argument(
        "--no-stealth",
        action="store_true",
        help="Desativa as medidas anti-detecção (apenas para depuração)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Nível de log (padrão: INFO)",
    )

    args = parser.parse_args()
    setup_logging(args.log_level)

    config = CrawlerConfig(
        anticaptcha_key=args.api_key,
        headless=not args.no_headless,
        stealth=not args.no_stealth,
    )

    logger.info("Iniciando crawler do CADESP cnpj=%s output=%s", args.cnpj, args.output)

    try:
        crawler = CadespCrawler(config=config)
        results = crawler.crawl(cnpj=args.cnpj, output_path=args.output)

        logger.info("Concluído — %d registro(s) encontrados", len(results))
        if results:
            print(f"Encontrado(s) {len(results)} registro(s) para o CNPJ {args.cnpj}")
            print(f"Saída salva em: {args.output}")
        else:
            print(f"Nenhum registro encontrado para o CNPJ {args.cnpj}")
    except CrawlerError as exc:
        logger.error("Consulta falhou: %s", exc)
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
