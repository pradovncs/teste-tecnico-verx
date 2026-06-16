"""Utilitários para deixar o navegador o mais "stealth" possível com Playwright.

O site do CADESP fica atrás de um firewall F5 BIG-IP que inspeciona
fingerprints de navegador (presença de ``navigator.webdriver``, ausência de
plugins, ordem de headers, etc.). As funções abaixo aplicam contramedidas
clássicas: removem flags de automação, definem um User-Agent realista,
idioma pt-BR e injetam um script que mascara propriedades delatoras.

Quando o firewall ainda assim bloqueia, ``random_fingerprint`` permite recriar
o contexto do navegador com uma nova identidade (User-Agent, viewport, locale e
timezone), o que costuma ser suficiente para passar por um bloqueio do BIG-IP.
"""

import random

# User-Agent realista de Chrome estável em Windows (padrão).
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# Conjunto de User-Agents de Chrome recentes em sistemas diferentes, usado para
# rotacionar a identidade do navegador quando o F5 BIG-IP bloqueia uma sessão.
USER_AGENTS = (
    DEFAULT_USER_AGENT,
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
)

# Resoluções comuns de desktop para variar o viewport entre tentativas.
VIEWPORTS = (
    {"width": 1920, "height": 1080},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
)

# Locale e timezone brasileiros (o site é em pt-BR / America/Sao_Paulo).
DEFAULT_LOCALE = "pt-BR"
DEFAULT_TIMEZONE = "America/Sao_Paulo"

# Script injetado antes de qualquer script da página (via add_init_script) para
# esconder os sinais mais comuns usados por sistemas anti-bot como o BIG-IP.
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = window.chrome || { runtime: {} };
const _query = window.navigator.permissions && window.navigator.permissions.query;
if (_query) {
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : _query(parameters)
    );
}
const _getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function (parameter) {
    if (parameter === 37445) { return 'Intel Inc.'; }
    if (parameter === 37446) { return 'Intel Iris OpenGL Engine'; }
    return _getParameter.apply(this, [parameter]);
};
"""


def stealth_arguments(user_agent: str = DEFAULT_USER_AGENT) -> list:
    """Retorna a lista de argumentos de linha de comando do Chrome stealth."""
    return [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-infobars",
        "--window-size=1920,1080",
        "--start-maximized",
        "--lang=pt-BR",
        f"--user-agent={user_agent}",
    ]


def excluded_switches() -> list:
    """Switches do Chrome a serem omitidos para esconder a automação."""
    return ["enable-automation"]


def playwright_args() -> list:
    """Argumentos de launch do Chromium para o Playwright (anti-detecção).

    Diferente do Selenium, o Playwright já roda sem a barra "controlado por
    software automatizado" e define o User-Agent/locale por contexto. Aqui
    ficam apenas as flags de linha de comando úteis para o BIG-IP.
    """
    return [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-infobars",
        "--disable-features=IsolateOrigins,site-per-process",
        "--window-size=1920,1080",
        "--lang=pt-BR",
    ]


def default_headers(locale: str = DEFAULT_LOCALE) -> dict:
    """Headers HTTP "humanos" para reforçar a identidade do navegador."""
    return {
        "Accept-Language": f"{locale},pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }


def random_fingerprint() -> dict:
    """Sorteia uma identidade de navegador para um novo contexto Playwright.

    Usado tanto na criação inicial do contexto quanto na recuperação após um
    bloqueio do F5 BIG-IP, quando trocar de fingerprint costuma liberar o
    acesso. Retorna um dicionário com ``user_agent``, ``viewport``, ``locale``
    e ``timezone_id``.
    """
    return {
        "user_agent": random.choice(USER_AGENTS),
        "viewport": random.choice(VIEWPORTS),
        "locale": DEFAULT_LOCALE,
        "timezone_id": DEFAULT_TIMEZONE,
    }
