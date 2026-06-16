import sys
import types
from unittest.mock import MagicMock

import pytest

from src.captcha.solver import AntiCaptchaSolver
from src.core.exceptions import CaptchaError


def _install_fake_anticaptcha(solution, error_code="ERROR"):
    """Instala um módulo falso 'anticaptchaofficial.imagecaptcha' em sys.modules."""
    fake_instance = MagicMock()
    fake_instance.solve_and_return_solution_from_string.return_value = solution
    fake_instance.error_code = error_code

    fake_cls = MagicMock(return_value=fake_instance)
    module = types.ModuleType("anticaptchaofficial.imagecaptcha")
    module.imagecaptcha = fake_cls

    pkg = types.ModuleType("anticaptchaofficial")
    sys.modules["anticaptchaofficial"] = pkg
    sys.modules["anticaptchaofficial.imagecaptcha"] = module
    return fake_instance


@pytest.fixture(autouse=True)
def _cleanup_modules():
    yield
    sys.modules.pop("anticaptchaofficial", None)
    sys.modules.pop("anticaptchaofficial.imagecaptcha", None)


class TestConstruction:
    def test_requires_api_key(self):
        with pytest.raises(CaptchaError):
            AntiCaptchaSolver(api_key=None)

    def test_accepts_api_key(self):
        solver = AntiCaptchaSolver(api_key="key")
        assert solver._api_key == "key"


class TestSolve:
    def test_empty_image_raises(self):
        solver = AntiCaptchaSolver(api_key="key")
        with pytest.raises(CaptchaError):
            solver.solve(b"")

    def test_returns_solution(self):
        instance = _install_fake_anticaptcha("ABCD")
        solver = AntiCaptchaSolver(api_key="key")
        assert solver.solve(b"imagedata") == "ABCD"
        instance.set_key.assert_called_once_with("key")
        instance.solve_and_return_solution_from_string.assert_called_once()

    def test_zero_solution_raises(self):
        _install_fake_anticaptcha(0, error_code="ERROR_KEY")
        solver = AntiCaptchaSolver(api_key="key")
        with pytest.raises(CaptchaError):
            solver.solve(b"imagedata")

    def test_strips_whitespace(self):
        _install_fake_anticaptcha("  ABCD  ")
        solver = AntiCaptchaSolver(api_key="key")
        assert solver.solve(b"x") == "ABCD"
