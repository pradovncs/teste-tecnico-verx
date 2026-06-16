"""Utilitários para deixar o navegador o mais "stealth" possível.

O site do CADESP fica atrás de um firewall F5 BIG-IP que inspeciona
fingerprints de navegador (presença de ``navigator.webdriver``, ausência de
plugins, ordem de headers, etc.). As funções abaixo aplicam contramedidas
clássicas: removem flags de automação, definem um User-Agent realista,
idioma pt-BR e injetam um script que mascara propriedades delatoras.
"""

# User-Agent realista de Chrome estável em Windows.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# Script injetado antes de qualquer script da página (via CDP) para esconder
# os sinais mais comuns usados por sistemas anti-bot.
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
