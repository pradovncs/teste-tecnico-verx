import logging

from src.core.cnpj import format_mask, validate
from src.core.exceptions import BlockedError, CaptchaError, ConsultaError
from src.core.interfaces import ICaptchaSolver, IDriver

logger = logging.getLogger(__name__)

# Mensagens típicas exibidas pelo firewall F5 BIG-IP ASM ao bloquear um request.
_BLOCK_MARKERS = (
    "the requested url was rejected",
    "support id is",
    "please consult with your administrator",
)


class CnpjConsulta:
    """Preenche e submete a Consulta Pública do CADESP filtrando por CNPJ.

    Fluxo:
      1. Seleciona "CNPJ" no dropdown de tipo de consulta.
      2. Digita o CNPJ no campo de texto.
      3. Captura a imagem do captcha e resolve via ``ICaptchaSolver``.
      4. Preenche o captcha e clica em Consultar.
      5. Detecta bloqueio do F5 BIG-IP ou erro de captcha para nova tentativa.
    """

    # IDs do ASP.NET WebForms (id usa "_", name usa "$").
    TIPO_SELECT = "#ctl00_conteudoPrincipal_ddlTipoConsulta"
    CNPJ_INPUT = "#ctl00_conteudoPrincipal_txtCpfCnpj"
    CNPJ_INPUT_ALT = "#ctl00_conteudoPrincipal_txtConsulta"
    CAPTCHA_IMG = "#ctl00_conteudoPrincipal_imgCaptcha"
    CAPTCHA_INPUT = "#ctl00_conteudoPrincipal_txtCaptcha"
    SUBMIT_BTN = "#ctl00_conteudoPrincipal_btnConsultar"
    RESULT_SELECTOR = "#ctl00_conteudoPrincipal_pnlResultado"
    ERROR_SELECTOR = "#ctl00_conteudoPrincipal_lblMensagem"

    TIPO_CNPJ_VALUE = "CNPJ"

    def __init__(self, driver: IDriver, solver: ICaptchaSolver) -> None:
        self._driver = driver
        self._solver = solver

    def run(self, cnpj: str) -> str:
        """Executa a consulta para o CNPJ e retorna o HTML do resultado.

        Args:
            cnpj: CNPJ a consultar (com ou sem máscara).

        Returns:
            HTML da página após a consulta ser submetida com sucesso.

        Raises:
            InvalidCNPJError: Se o CNPJ for inválido.
            BlockedError: Se o F5 BIG-IP bloquear a requisição.
            ConsultaError / CaptchaError: Se a consulta/captcha falhar.
        """
        digits = validate(cnpj)
        logger.info("Consultando CNPJ=%s", format_mask(digits))

        self._check_blocked()
        self._select_tipo_cnpj()
        self._fill_cnpj(digits)
        self._solve_and_fill_captcha()
        self._submit()

        html = self._driver.get_html()
        self._check_blocked(html)
        self._check_captcha_rejected(html)
        return html

    # ----------------------------------------------------------------- steps
    def _select_tipo_cnpj(self) -> None:
        """Seleciona a opção CNPJ no dropdown de tipo de consulta."""
        try:
            self._driver.select_option(self.TIPO_SELECT, self.TIPO_CNPJ_VALUE)
            self._driver.human_delay()
            logger.info("Tipo de consulta definido como CNPJ")
        except Exception as exc:
            raise ConsultaError(f"Falha ao selecionar tipo CNPJ: {exc}") from exc

    def _fill_cnpj(self, digits: str) -> None:
        """Digita o CNPJ no campo de texto da consulta."""
        try:
            field = self._first_present([self.CNPJ_INPUT, self.CNPJ_INPUT_ALT])
            self._driver.type_text(field, digits)
            self._driver.human_delay()
            logger.info("CNPJ preenchido")
        except Exception as exc:
            raise ConsultaError(f"Falha ao preencher o CNPJ: {exc}") from exc

    def _solve_and_fill_captcha(self) -> None:
        """Captura a imagem do captcha, resolve e preenche o campo."""
        try:
            img = self._driver.wait_for(self.CAPTCHA_IMG, timeout=15)
            image_bytes = self._driver.screenshot_element(img)
        except Exception as exc:
            raise CaptchaError(f"Imagem do captcha não encontrada: {exc}") from exc

        solution = self._solver.solve(image_bytes)
        if not solution:
            raise CaptchaError("Solver retornou um captcha vazio")

        field = self._driver.wait_for(self.CAPTCHA_INPUT, timeout=10)
        self._driver.type_text(field, solution)
        self._driver.human_delay()
        logger.info("Captcha preenchido")

    def _submit(self) -> None:
        """Clica no botão Consultar e aguarda o resultado ou a mensagem."""
        try:
            btn = self._driver.wait_for(self.SUBMIT_BTN, timeout=10)
            self._driver.click_element(btn)
            logger.info("Consulta submetida")
            self._wait_result()
        except (BlockedError, CaptchaError, ConsultaError):
            raise
        except Exception as exc:
            raise ConsultaError(f"Falha ao submeter a consulta: {exc}") from exc

    def _wait_result(self) -> None:
        """Aguarda o painel de resultado ou a mensagem de erro aparecer."""
        try:
            self._driver.wait_for(
                f"{self.RESULT_SELECTOR}, {self.ERROR_SELECTOR}", timeout=20
            )
        except Exception:
            logger.warning("Tempo esgotado aguardando resultado/mensagem da consulta")

    # ----------------------------------------------------------------- guards
    def _check_blocked(self, html: str = None) -> None:
        """Levanta BlockedError se a página for um bloqueio do F5 BIG-IP."""
        content = (html if html is not None else self._driver.get_html()).lower()
        if any(marker in content for marker in _BLOCK_MARKERS):
            raise BlockedError(
                "Requisição bloqueada pelo firewall F5 BIG-IP (Support ID na resposta)"
            )

    def _check_captcha_rejected(self, html: str) -> None:
        """Levanta CaptchaError se o site indicar que o captcha está incorreto."""
        lowered = html.lower()
        if "código de segurança" in lowered and (
            "inválido" in lowered or "incorreto" in lowered or "não confere" in lowered
        ):
            raise CaptchaError("O CADESP recusou o captcha informado")

    def _first_present(self, selectors):
        """Retorna o primeiro elemento presente dentre os seletores informados."""
        last_exc = None
        for selector in selectors:
            try:
                return self._driver.wait_for(selector, timeout=8)
            except Exception as exc:  # noqa: PERF203 - tentativa sequencial
                last_exc = exc
        raise ConsultaError(f"Nenhum campo encontrado em {selectors}: {last_exc}")
