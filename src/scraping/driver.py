import logging
import random
import time
from typing import Any, List, Optional

from playwright.sync_api import sync_playwright

from src.core.interfaces import IDriver
from src.scraping import stealth

logger = logging.getLogger(__name__)


class StealthBrowserDriver(IDriver):
    """Wrapper do Playwright com medidas anti-detecção (F5 BIG-IP).

    Usa o Chromium do Playwright dirigido via CDP nativo (mais difícil de
    detectar que o Selenium) e injeta, antes de qualquer script da página, um
    script que mascara os sinais clássicos de automação. Cada sessão roda em um
    *browser context* isolado, com User-Agent, viewport, locale e timezone
    realistas.

    Quando o BIG-IP bloqueia mesmo assim, ``recover`` recria o contexto com uma
    nova impressão digital, o que costuma ser suficiente para liberar o acesso.
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30,
        stealth_mode: bool = True,
        min_delay: float = 0.4,
        max_delay: float = 1.6,
        browser: str = "chromium",
    ) -> None:
        logger.info(
            "Inicializando StealthBrowserDriver (Playwright) headless=%s stealth=%s browser=%s",
            headless,
            stealth_mode,
            browser,
        )
        self._timeout = timeout
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._headless = headless
        self._stealth = stealth_mode
        self._browser_name = browser

        self._playwright = sync_playwright().start()
        self._browser = self._launch_browser()
        self._context = None
        self._page = None
        self._new_context()
        logger.info("StealthBrowserDriver inicializado")

    # ------------------------------------------------------------------ setup
    def _launch_browser(self):
        """Inicia o navegador do Playwright com flags anti-detecção."""
        browser_type = getattr(self._playwright, self._browser_name)
        args = stealth.playwright_args() if self._stealth else []
        return browser_type.launch(headless=self._headless, args=args)

    def _new_context(self, fingerprint: Optional[dict] = None) -> None:
        """(Re)cria o contexto e a página com uma identidade de navegador.

        Fecha o contexto anterior (se houver), descartando cookies e estado, e
        abre um novo com fingerprint sorteado — base da recuperação de bloqueio.
        """
        if self._context is not None:
            try:
                self._context.close()
            except Exception:  # pragma: no cover - melhor esforço
                pass

        fp = fingerprint or (stealth.random_fingerprint() if self._stealth else {})
        context_kwargs: dict = {}
        if fp:
            context_kwargs = {
                "user_agent": fp["user_agent"],
                "locale": fp["locale"],
                "viewport": fp["viewport"],
                "timezone_id": fp["timezone_id"],
                "extra_http_headers": stealth.default_headers(fp["locale"]),
            }
            logger.debug("Novo contexto com fingerprint=%s", fp["user_agent"])

        self._context = self._browser.new_context(**context_kwargs)
        self._context.set_default_timeout(self._timeout * 1000)
        if self._stealth:
            self._context.add_init_script(stealth.STEALTH_JS)
        self._page = self._context.new_page()

    # ----------------------------------------------------------------- helpers
    def human_delay(self) -> None:
        """Aguarda um intervalo aleatório, imitando o tempo de reação humano."""
        time.sleep(random.uniform(self._min_delay, self._max_delay))

    def _timeout_ms(self, timeout: Optional[int]) -> int:
        """Converte um timeout em segundos para milissegundos (padrão Playwright)."""
        return int((timeout or self._timeout) * 1000)

    # --------------------------------------------------------------- IDriver
    def open(self, url: str) -> None:
        """Navega até a URL informada, aguardando o DOM carregar."""
        logger.info("Navegando para url=%s", url)
        self._page.goto(url, wait_until="domcontentloaded")

    def find(self, selector: str) -> Any:
        """Localiza um único elemento por seletor CSS (ou ``None``)."""
        return self._page.query_selector(selector)

    def find_all(self, selector: str) -> List[Any]:
        """Localiza todos os elementos que casam com o seletor CSS."""
        elements = self._page.query_selector_all(selector)
        logger.debug("Encontrados %d elementos para selector=%s", len(elements), selector)
        return elements

    def wait_for(self, selector: str, timeout: Optional[int] = None) -> Any:
        """Aguarda um elemento estar presente no DOM e o retorna."""
        return self._page.wait_for_selector(
            selector, timeout=self._timeout_ms(timeout), state="attached"
        )

    def wait_for_invisible(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Aguarda um elemento ficar invisível ou sumir do DOM."""
        self._page.wait_for_selector(
            selector, timeout=self._timeout_ms(timeout), state="hidden"
        )
        return True

    def execute_script(self, script: str, *args: Any) -> Any:
        """Executa JavaScript no contexto da página.

        ``script`` deve ser uma expressão de função JS no formato do Playwright
        (por exemplo ``"el => el.click()"``); ``args`` é passado como argumento.
        """
        if args:
            return self._page.evaluate(script, list(args) if len(args) > 1 else args[0])
        return self._page.evaluate(script)

    def click_element(self, element: Any) -> None:
        """Clica em um elemento, com pequeno atraso humano antes."""
        self.human_delay()
        try:
            element.click()
        except Exception:
            element.click(force=True)

    def type_text(self, element: Any, text: str) -> None:
        """Digita texto caractere a caractere, imitando a digitação humana."""
        element.fill("")
        for char in text:
            element.type(char)
            time.sleep(random.uniform(0.05, 0.18))

    def select_option(self, selector: str, value: str) -> None:
        """Seleciona uma opção de um ``<select>`` por valor ou texto visível."""
        try:
            self._page.select_option(selector, value=value)
        except Exception:
            self._page.select_option(selector, label=value)

    def screenshot_element(self, element: Any) -> bytes:
        """Retorna o PNG (bytes) de um único elemento (usado para o captcha)."""
        return element.screenshot(type="png")

    def get_html(self) -> str:
        """Retorna o HTML completo da página."""
        html = self._page.content()
        logger.debug("page content length=%d", len(html))
        return html

    def recover(self) -> None:
        """Recria o contexto com nova impressão digital para contornar o BIG-IP.

        Chamado pelo crawler quando o F5 BIG-IP bloqueia a requisição: descarta
        cookies/estado e troca User-Agent, viewport, locale e timezone, antes de
        uma nova tentativa de navegação.
        """
        logger.info("Recuperando de bloqueio: recriando contexto com novo fingerprint")
        self.human_delay()
        self._new_context()

    def quit(self) -> None:
        """Encerra o navegador, o contexto e o processo do Playwright."""
        logger.info("Encerrando navegador")
        for closer in (self._context, self._browser):
            if closer is not None:
                try:
                    closer.close()
                except Exception:  # pragma: no cover - melhor esforço
                    pass
        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:  # pragma: no cover - melhor esforço
                pass

    def __enter__(self) -> "StealthBrowserDriver":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        self.quit()
        return False
