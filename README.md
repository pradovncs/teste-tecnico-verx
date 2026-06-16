# CADESP CNPJ Crawler

Crawler que extrai dados da [Consulta Pública do CADESP](https://www.cadesp.fazenda.sp.gov.br/Pages/Cadastro/Consultas/ConsultaPublica/ConsultaPublica.aspx) (Cadastro de Contribuintes do ICMS — SEFAZ-SP), filtrando **por CNPJ** no dropdown de tipo de consulta.

O site é um **ASP.NET Web Forms** protegido por um firewall **F5 BIG-IP** (inspeção de fingerprint do navegador) e exige a resolução de um **captcha de imagem**. Por isso o projeto usa:

- **Playwright** (Chromium) para dirigir o navegador de forma o mais "stealth" possível e contornar o bloqueio do F5 BIG-IP. Quando o firewall bloqueia, a sessão é **recuperada** automaticamente trocando a impressão digital (User-Agent, viewport, locale e timezone) e tentando novamente com backoff.
- **AntiCaptcha** (`anticaptchaofficial`, tarefa *Image-to-Text*) para resolver o captcha.
- **BeautifulSoup + lxml** para parsear o resultado.

Teste técnico — **Desenvolvedor Python Sênior** na **Verx**.

---

## Como executar

**Pré-requisito:** uma chave de API do [Anti-Captcha](https://anti-captcha.com/). O navegador (Chromium) é instalado pelo próprio Playwright.

```bash
git clone https://github.com/pradovncs/teste-tecnico-verx.git
cd teste-tecnico-verx

# Com Poetry
poetry install
poetry run playwright install chromium
export ANTICAPTCHA_KEY="sua_chave_aqui"
poetry run python main.py --cnpj "11.222.333/0001-81"

# Com pip
pip install -r requirements.txt
playwright install chromium
export ANTICAPTCHA_KEY="sua_chave_aqui"
python main.py --cnpj "11.222.333/0001-81"
```

### Parâmetros

| Parâmetro | Obrigatório | Descrição |
|---|---|---|
| `--cnpj` | Sim | CNPJ a consultar (com ou sem máscara) |
| `--api-key` | Não | Chave da API do AntiCaptcha (padrão: variável `ANTICAPTCHA_KEY`) |
| `--output` | Não | Caminho do arquivo de saída `.csv`/`.json` (padrão: `output/cadesp.csv`) |
| `--no-headless` | Não | Abre o navegador com interface gráfica (depuração) |
| `--no-stealth` | Não | Desativa as contramedidas anti-detecção (depuração) |
| `--log-level` | Não | `DEBUG`, `INFO`, `WARNING`, `ERROR` (padrão: `INFO`) |

---

## Testes

```bash
poetry run pytest tests/ -v

# Com cobertura
poetry run pytest tests/ --cov=src --cov-report=term-missing
```

Os testes rodam sem abrir navegador real nem acessar a rede (Playwright e AntiCaptcha são mockados).

---

## Tecnologias

- **Python 3.10+**
- **Playwright** (Chromium) — automação stealth do navegador
- **anticaptchaofficial** — resolução do captcha de imagem
- **BeautifulSoup 4 + lxml** — parsing do HTML de resultado
- **Poetry** — dependências e virtualenv
- **pytest** — testes unitários

---

## Estrutura

```
src/
├── core/                  # Interfaces, exceções, config, modelos
│   ├── interfaces.py      # ABCs: IDriver, ICaptchaSolver, IParser, IExporter, ICrawler
│   ├── exceptions.py      # CrawlerError → Captcha/Consulta/Blocked/InvalidCNPJ/...
│   ├── config.py          # CrawlerConfig (dataclass frozen)
│   ├── models.py          # Contribuinte (dataclass)
│   └── cnpj.py            # Validação/normalização de CNPJ
├── captcha/
│   └── solver.py          # AntiCaptchaSolver (anticaptchaofficial)
├── scraping/              # Automação do navegador
│   ├── driver.py          # StealthBrowserDriver — Playwright stealth + recover()
│   ├── stealth.py         # Args, fingerprint e init script anti-detecção (F5 BIG-IP)
│   └── consulta.py        # CnpjConsulta — dropdown + CNPJ + captcha + submit
├── io/
│   ├── parser.py          # ConsultaParser — HTML → Contribuinte
│   └── exporter.py        # CSVExporter — CSV/JSON
└── crawler.py             # CadespCrawler — orquestra tudo

tests/                     # Testes (mocks, sem browser/rede real)
main.py                    # CLI
```

---

## Decisões Técnicas

### Stealth contra o F5 BIG-IP

O F5 BIG-IP ASM bloqueia automações detectando sinais como `navigator.webdriver`, ausência de plugins/idiomas e flags de automação do Chrome. As contramedidas em `scraping/stealth.py` e `scraping/driver.py`:

- Usam o **Chromium do Playwright**, controlado via CDP nativo (mais difícil de detectar que o Selenium) e sem a flag `enable-automation`.
- Aplicam `--disable-blink-features=AutomationControlled` e demais flags de launch.
- Injetam, via `add_init_script` (antes de qualquer script da página), um script que mascara `navigator.webdriver`, `languages` (pt-BR), `plugins`, `chrome.runtime` e o renderer WebGL.
- Definem User-Agent, viewport, locale (pt-BR) e timezone (America/Sao_Paulo) realistas por contexto e aplicam **atrasos aleatórios** e digitação caractere a caractere para imitar comportamento humano.

Quando o firewall ainda assim bloqueia, a resposta contém o texto *"The requested URL was rejected… Support ID"*; isso é detectado e levanta `BlockedError`. O crawler então **recupera a sessão** via `driver.recover()` — que recria o contexto do navegador com uma nova impressão digital (User-Agent, viewport, locale, timezone) e descarta cookies — e tenta novamente, com **backoff exponencial**, até `max_block_attempts` vezes.

### Captcha com AntiCaptcha

A imagem do captcha é capturada como screenshot do próprio elemento (`screenshot_as_png`) e enviada ao Anti-Captcha em base64 (`solve_and_return_solution_from_string`). Captchas recusados disparam `CaptchaError` e o crawler **tenta novamente** até `max_captcha_attempts` vezes, recarregando a página a cada tentativa.

### Arquitetura e OOP

Interfaces via ABCs (`IDriver`, `ICaptchaSolver`, `IParser`, `IExporter`, `ICrawler`) e injeção de dependências. O `CadespCrawler` recebe driver, solver, parser e exporter opcionais — se nada for passado, cria as implementações padrão. Isso permite testar todo o fluxo com mocks, sem navegador nem chamadas de rede.

### Exceções

```
CrawlerError
├── NavigationError
├── ParseError
├── ExportError
├── CaptchaError
├── ConsultaError
├── BlockedError
└── InvalidCNPJError
```

### Validação de CNPJ

O CNPJ é normalizado e validado pelo algoritmo oficial dos dígitos verificadores antes de qualquer interação com o site, evitando gastar captcha com entradas inválidas.

---

## Exemplo de Saída

```csv
"cnpj","inscricao_estadual","nome_empresarial","situacao_cadastral","municipio"
"11.222.333/0001-81","111.111.111.111","EMPRESA EXEMPLO LTDA","Ativo","SAO PAULO"
```
