# Yahoo Finance Stock Crawler

Crawler que extrai dados de ações do [Yahoo Finance Equity Screener](https://finance.yahoo.com/research-hub/screener/equity/) filtrando por região.

O Yahoo Finance renderiza a tabela de ações via JavaScript, então um `requests.get()` na URL retorna HTML vazio. Por isso o projeto usa **Selenium** pra carregar a página e interagir com filtros, e **BeautifulSoup** pra extrair os dados do HTML renderizado.

Teste técnico — **Desenvolvedor Python Sênior** na **Verx**.

---

## Como executar

**Pré-requisito:** Google Chrome instalado (Selenium 4 gerencia o ChromeDriver automaticamente).

```bash
git clone [https://github.com/pradovncs/teste-tecnico-verx.git]
cd teste-tecnico-verx

# Com Poetry
poetry install
poetry run python main.py --region "Brazil"

# Com pip
pip install -r requirements.txt
python main.py --region "Brazil"
```

### Parâmetros

| Parâmetro | Obrigatório | Descrição |
|---|---|---|
| `--region` | Sim | Região pra filtrar (ex.: `"Brazil"`, `"Argentina"`, `"United States"`) |
| `--output` | Não | Caminho do CSV (padrão: `output/stocks.csv`) |
| `--log-level` | Não | `DEBUG`, `INFO`, `WARNING`, `ERROR` (padrão: `INFO`) |

---

## Testes

```bash
poetry run pytest tests/ -v

# Com cobertura
poetry run pytest tests/ --cov=src --cov-report=term-missing
```

118 testes cobrindo parsing, exportação, filtro de região, paginação, driver, exceções e o fluxo do crawler. Todos rodam sem abrir navegador (mocks do Selenium).

---

## Tecnologias

- **Python 3.10+**
- **Selenium 4** — automação do Chrome pra carregar páginas dinâmicas e interagir com filtros/paginação
- **BeautifulSoup 4 + lxml** — parsing do HTML renderizado
- **Poetry** — dependências e virtualenv
- **pytest** — testes unitários

---

## Estrutura

```
src/
├── core/                  # Interfaces, exceções, config, modelos
│   ├── interfaces.py      # ABCs: IDriver, IParser, IExporter, ICrawler
│   ├── exceptions.py      # CrawlerError → NavigationError, ParseError, etc.
│   ├── config.py          # CrawlerConfig (dataclass frozen)
│   └── models.py          # Stock (dataclass com validação)
├── scraping/              # Automação do navegador
│   ├── driver.py          # BrowserDriver — wrapper do Selenium
│   ├── consent_handler.py # Fecha banners de cookies
│   ├── region_filter.py   # Aplica filtro de região no screener
│   └── paginator.py       # Navega páginas + deduplicação
├── io/
│   ├── parser.py          # StockParser — HTML → lista de Stock
│   └── exporter.py        # CSVExporter — Stock → CSV
└── crawler.py             # YahooFinanceCrawler — orquestra tudo

tests/                     # 118 testes (mocks, sem browser real)
main.py                    # CLI
```

---

## Decisões Técnicas

### Por que Selenium + BeautifulSoup juntos?

O Yahoo Finance é uma SPA — a tabela de ações só aparece depois que o JavaScript executa. Um `requests.get()` na URL retorna HTML sem nenhum dado útil.

O **Selenium** resolve isso: abre o Chrome headless, espera renderizar, interage com o dropdown de região, clica em Apply, navega entre páginas. Mas usar Selenium puro pra extrair dados de tabelas é verboso (`find_elements` repetido pra cada célula, sem suporte a CSS selectors complexos).

Então depois que o Selenium carrega a página, pego o `page_source` e passo pro **BeautifulSoup** com parser `lxml`. O parsing fica mais limpo:

```python
html = driver.get_html()
soup = BeautifulSoup(html, "lxml")
rows = soup.select("table tbody tr")
```

Cada um faz o que faz melhor — Selenium navega, BS4 parseia.

### Arquitetura e OOP

O projeto usa interfaces via ABCs (`IDriver`, `IParser`, `IExporter`, `ICrawler`) e injeção de dependências. O `YahooFinanceCrawler` recebe driver, parser e exporter como parâmetros opcionais — se não passar nada, cria as implementações padrão. Isso facilita testar com mocks sem precisar abrir navegador.

As responsabilidades ficam separadas: `BrowserDriver` só navega, `StockParser` só extrai dados de HTML, `RegionFilter` só aplica filtro, `Paginator` só pagina e deduplica. O crawler orquestra.

### Exceções

Hierarquia com `CrawlerError` como base, permitindo `except CrawlerError` no CLI pra capturar qualquer erro de domínio:

```
CrawlerError
├── NavigationError
├── ParseError
├── ExportError
├── FilterError
└── PaginationError
```

### Waits explícitos

Substituí `time.sleep()` por `WebDriverWait` + Expected Conditions do Selenium. Em vez de esperar 5s fixos torcendo pra página ter carregado, o código espera até o elemento aparecer (ou desaparecer, no caso do banner de cookies). Mais rápido e confiável.

### Stock como dataclass

Modelo `Stock` é dataclass com validação no `__post_init__` — symbol e name não podem ser vazios. Garante tipagem, igualdade por valor nos testes e conversão pra dict via `to_dict()`.

---

## Exemplo de Saída

```csv
"symbol","name","price"
"PETR4.SA","Petróleo Brasileiro S.A. - Petrobras","38.50"
"VALE3.SA","Vale S.A.","62.30"
"ITUB4.SA","Itaú Unibanco Holding S.A.","8.05"
```
