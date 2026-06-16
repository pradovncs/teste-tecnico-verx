import base64
import logging
from typing import Optional

from src.core.exceptions import CaptchaError
from src.core.interfaces import ICaptchaSolver

logger = logging.getLogger(__name__)


class AntiCaptchaSolver(ICaptchaSolver):
    """Resolve captchas de imagem usando o serviço Anti-Captcha.

    Utiliza o pacote oficial ``anticaptchaofficial`` (tarefa ``ImageToText``).
    A importação do pacote é adiada para o momento do uso, de modo que o
    restante do projeto (e os testes) não dependa dele estar instalado.
    """

    def __init__(self, api_key: Optional[str], soft_id: int = 0, verbose: bool = False) -> None:
        if not api_key:
            raise CaptchaError(
                "Chave da API do AntiCaptcha não informada "
                "(use --api-key ou a variável de ambiente ANTICAPTCHA_KEY)"
            )
        self._api_key = api_key
        self._soft_id = soft_id
        self._verbose = verbose

    def _build_solver(self):
        """Instancia o solver do anticaptchaofficial (import adiado)."""
        try:
            from anticaptchaofficial.imagecaptcha import imagecaptcha
        except ImportError as exc:  # pragma: no cover - depende do ambiente
            raise CaptchaError(
                "Pacote 'anticaptchaofficial' não instalado. "
                "Instale com: pip install anticaptchaofficial"
            ) from exc

        solver = imagecaptcha()
        solver.set_verbose(1 if self._verbose else 0)
        solver.set_key(self._api_key)
        if self._soft_id:
            solver.set_soft_id(self._soft_id)
        return solver

    def solve(self, image_bytes: bytes) -> str:
        """Resolve um captcha de imagem e retorna o texto reconhecido.

        Args:
            image_bytes: Conteúdo binário da imagem do captcha.

        Returns:
            Texto do captcha conforme resolvido pelo serviço.

        Raises:
            CaptchaError: Se a imagem for vazia ou o serviço falhar.
        """
        if not image_bytes:
            raise CaptchaError("Imagem do captcha vazia")

        solver = self._build_solver()
        body = base64.b64encode(image_bytes).decode("ascii")

        logger.info("Enviando captcha (%d bytes) para o AntiCaptcha", len(image_bytes))
        solution = solver.solve_and_return_solution_from_string(body)

        if not solution or solution == 0:
            error = getattr(solver, "error_code", "desconhecido")
            raise CaptchaError(f"AntiCaptcha falhou ao resolver o captcha: {error}")

        text = str(solution).strip()
        logger.info("Captcha resolvido (%d caracteres)", len(text))
        return text
