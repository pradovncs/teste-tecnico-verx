from unittest.mock import MagicMock

import pytest

from src.core.exceptions import BlockedError, CaptchaError, InvalidCNPJError
from src.scraping.consulta import CnpjConsulta

VALID = "11.222.333/0001-81"


def make_driver(html="<html><body>resultado</body></html>"):
    driver = MagicMock()
    driver.get_html.return_value = html
    driver.screenshot_element.return_value = b"imgbytes"
    driver.wait_for.return_value = MagicMock()
    driver.find.return_value = MagicMock()
    return driver


def make_solver(solution="ABCD"):
    solver = MagicMock()
    solver.solve.return_value = solution
    return solver


class TestRun:
    def test_invalid_cnpj_raises(self):
        consulta = CnpjConsulta(make_driver(), make_solver())
        with pytest.raises(InvalidCNPJError):
            consulta.run("00000000000000")

    def test_happy_path_returns_html(self):
        driver = make_driver("<html><body><div id='res'>ok</div></body></html>")
        solver = make_solver("WXYZ")
        consulta = CnpjConsulta(driver, solver)

        html = consulta.run(VALID)

        assert "ok" in html
        driver.select_option.assert_called_once()
        solver.solve.assert_called_once_with(b"imgbytes")

    def test_selects_cnpj_option(self):
        driver = make_driver()
        consulta = CnpjConsulta(driver, make_solver())
        consulta.run(VALID)
        args = driver.select_option.call_args[0]
        assert args[0] == CnpjConsulta.TIPO_SELECT
        assert args[1] == "CNPJ"

    def test_blocked_page_raises(self):
        blocked = "<html>The requested URL was rejected. Support ID is: 123</html>"
        consulta = CnpjConsulta(make_driver(blocked), make_solver())
        with pytest.raises(BlockedError):
            consulta.run(VALID)

    def test_empty_captcha_raises(self):
        consulta = CnpjConsulta(make_driver(), make_solver(solution=""))
        with pytest.raises(CaptchaError):
            consulta.run(VALID)

    def test_rejected_captcha_raises(self):
        html = "<html>Código de segurança inválido</html>"
        # primeira chamada (guard inicial) limpa, segunda (pós-submit) rejeita
        driver = make_driver()
        driver.get_html.side_effect = [
            "<html>ok</html>",  # guard inicial
            html,               # pós-submit
        ]
        consulta = CnpjConsulta(driver, make_solver())
        with pytest.raises(CaptchaError):
            consulta.run(VALID)
