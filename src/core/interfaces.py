from abc import ABC, abstractmethod
from typing import Any, List, Optional


class IDriver(ABC):
    """Interface para drivers de automação do navegador."""

    @abstractmethod
    def open(self, url: str) -> None:
        ...

    @abstractmethod
    def find(self, selector: str) -> Any:
        ...

    @abstractmethod
    def find_all(self, selector: str) -> List[Any]:
        ...

    @abstractmethod
    def wait_for(self, selector: str, timeout: Optional[int] = None) -> Any:
        ...

    @abstractmethod
    def wait_for_invisible(self, selector: str, timeout: Optional[int] = None) -> bool:
        ...

    @abstractmethod
    def execute_script(self, script: str, *args: Any) -> Any:
        ...

    @abstractmethod
    def click_element(self, element: Any) -> None:
        ...

    @abstractmethod
    def type_text(self, element: Any, text: str) -> None:
        ...

    @abstractmethod
    def select_option(self, selector: str, value: str) -> None:
        ...

    @abstractmethod
    def screenshot_element(self, element: Any) -> bytes:
        ...

    @abstractmethod
    def get_html(self) -> str:
        ...

    @abstractmethod
    def quit(self) -> None:
        ...

    @abstractmethod
    def __enter__(self) -> "IDriver":
        ...

    @abstractmethod
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        ...


class ICaptchaSolver(ABC):
    """Interface para serviços de resolução de captcha de imagem."""

    @abstractmethod
    def solve(self, image_bytes: bytes) -> str:
        ...


class IParser(ABC):
    """Interface para parsers do resultado da consulta."""

    @abstractmethod
    def parse(self, html: str) -> list:
        ...


class IExporter(ABC):
    """Interface para exportadores de dados."""

    @abstractmethod
    def export(self, data: list, filepath: str) -> None:
        ...


class ICrawler(ABC):
    """Interface para o crawler."""

    @abstractmethod
    def crawl(self, cnpj: str, output_path: Optional[str] = None) -> list:
        ...
