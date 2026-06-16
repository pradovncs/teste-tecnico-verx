import logging
import random
import time
from typing import Any, List, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.core.interfaces import IDriver
from src.scraping import stealth

logger = logging.getLogger(__name__)


class StealthBrowserDriver(IDriver):
    """Wrapper do Selenium Chrome com medidas anti-detecção (F5 BIG-IP).

    Quando ``stealth=True`` tenta usar o ``undetected_chromedriver`` (que evita
    melhor os firewalls de bot). Se ele não estiver instalado, recai sobre o
    Selenium padrão aplicando as mesmas contramedidas de fingerprint.
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30,
        stealth_mode: bool = True,
        min_delay: float = 0.4,
        max_delay: float = 1.6,
    ) -> None:
        logger.info(
            "Inicializando StealthBrowserDriver headless=%s stealth=%s", headless, stealth_mode
        )
        self._timeout = timeout
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._driver = self._build_driver(headless, stealth_mode)
        if stealth_mode:
            self._apply_stealth()
        logger.info("StealthBrowserDriver inicializado")

    # ------------------------------------------------------------------ setup
    def _build_driver(self, headless: bool, stealth_mode: bool):
        """Cria a instância do WebDriver (undetected ou padrão)."""
        if stealth_mode:
            driver = self._try_undetected(headless)
            if driver is not None:
                self._undetected = True
                return driver

        self._undetected = False
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        for arg in stealth.stealth_arguments():
            options.add_argument(arg)
        options.add_experimental_option("excludeSwitches", stealth.excluded_switches())
        options.add_experimental_option("useAutomationExtension", False)
        return webdriver.Chrome(options=options)

    def _try_undetected(self, headless: bool):
        """Tenta criar um undetected_chromedriver; retorna None se indisponível."""
        try:
            import undetected_chromedriver as uc
        except ImportError:
            logger.info("undetected_chromedriver indisponível — usando Selenium padrão")
            return None
        try:
            options = uc.ChromeOptions()
            options.add_argument(f"--user-agent={stealth.DEFAULT_USER_AGENT}")
            options.add_argument("--lang=pt-BR")
            return uc.Chrome(options=options, headless=headless)
        except Exception as exc:  # pragma: no cover - depende do ambiente
            logger.warning("Falha ao iniciar undetected_chromedriver: %s", exc)
            return None

    def _apply_stealth(self) -> None:
        """Injeta o script de stealth via CDP, antes de qualquer página carregar."""
        try:
            self._driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument", {"source": stealth.STEALTH_JS}
            )
        except Exception as exc:  # pragma: no cover - depende do driver
            logger.debug("Não foi possível aplicar stealth via CDP: %s", exc)

    # ----------------------------------------------------------------- helpers
    def human_delay(self) -> None:
        """Aguarda um intervalo aleatório, imitando o tempo de reação humano."""
        time.sleep(random.uniform(self._min_delay, self._max_delay))

    # --------------------------------------------------------------- IDriver
    def open(self, url: str) -> None:
        """Navega até a URL informada."""
        logger.info("Navegando para url=%s", url)
        self._driver.get(url)

    def find(self, selector: str) -> Any:
        """Localiza um único elemento por seletor CSS."""
        return self._driver.find_element(By.CSS_SELECTOR, selector)

    def find_all(self, selector: str) -> List[Any]:
        """Localiza todos os elementos que casam com o seletor CSS."""
        elements = self._driver.find_elements(By.CSS_SELECTOR, selector)
        logger.debug("Encontrados %d elementos para selector=%s", len(elements), selector)
        return elements

    def wait_for(self, selector: str, timeout: Optional[int] = None) -> Any:
        """Aguarda um elemento estar presente no DOM."""
        t = timeout or self._timeout
        wait = WebDriverWait(self._driver, t)
        return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    def wait_for_invisible(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Aguarda um elemento ficar invisível ou sumir do DOM."""
        t = timeout or self._timeout
        wait = WebDriverWait(self._driver, t)
        return wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, selector)))

    def execute_script(self, script: str, *args: Any) -> Any:
        """Executa JavaScript no contexto da página."""
        return self._driver.execute_script(script, *args)

    def click_element(self, element: Any) -> None:
        """Clica em um elemento, com pequeno atraso humano antes."""
        self.human_delay()
        try:
            element.click()
        except Exception:
            self._driver.execute_script("arguments[0].click();", element)

    def type_text(self, element: Any, text: str) -> None:
        """Digita texto caractere a caractere, imitando a digitação humana."""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.18))

    def select_option(self, selector: str, value: str) -> None:
        """Seleciona uma opção de um ``<select>`` por valor ou texto visível."""
        element = self.wait_for(selector)
        select = Select(element)
        try:
            select.select_by_value(value)
        except Exception:
            select.select_by_visible_text(value)

    def screenshot_element(self, element: Any) -> bytes:
        """Retorna o PNG (bytes) de um único elemento (usado para o captcha)."""
        return element.screenshot_as_png

    def get_html(self) -> str:
        """Retorna o HTML completo da página."""
        html = self._driver.page_source
        logger.debug("page_source length=%d", len(html))
        return html

    def quit(self) -> None:
        """Encerra o navegador e a sessão."""
        logger.info("Encerrando navegador")
        self._driver.quit()

    def __enter__(self) -> "StealthBrowserDriver":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        self.quit()
        return False
