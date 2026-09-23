# 🛡️ GuardLLM — Defensive Security Reverse Proxy for LLMs

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-ASGI-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic V2](https://img.shields.io/badge/Pydantic-V2%20(Rust%20Core)-e92063.svg)](https://docs.pydantic.dev/)
[![Package Manager](https://img.shields.io/badge/Package%20Manager-uv-purple.svg)](https://astral.sh/uv)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-black.svg)](https://docs.astral.sh/ruff/)
[![Type Checking](https://img.shields.io/badge/Types-Mypy%20Strict-blue.svg)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

O **GuardLLM** é um proxy reverso defensivo de segurança de alta performance projetado para inspecionar, sanitizar e auditar interações com Modelos de Linguagem (LLMs) em ambientes de produção. 

Ele atua como um **AI Security Gateway** intermediário entre as aplicações consumidoras e os provedores de inteligência artificial (como Google Gemini e OpenAI), mitigando riscos críticos do **OWASP Top 10 for LLMs** e assegurando conformidade estrita com normas de privacidade (**LGPD e GDPR**).

---

## 🏛️ Arquitetura do Repositório

O projeto segue os princípios de **Clean Architecture**, **Separation of Concerns (SoC)** e a metodologia **Twelve-Factor App**:

```text
guard-llm/
├── backend/
│   ├── pyproject.toml              # Manifesto do projeto, dependências e tooling
│   ├── uv.lock                     # Lockfile determinístico com integridade de hash
│   ├── .env.example                # Template seguro de variáveis de ambiente
│   ├── src/
│   │   └── guardllm/
│   │       ├── api/
│   │       │   └── v1/
│   │       │       ├── endpoints/  # Rotas HTTP versionadas (health, sanitize)
│   │       │       └── router.py   # Agregador central de rotas
│   │       ├── core/
│   │       │   └── config.py       # Pydantic-settings imutável e fail-fast
│   │       ├── schemas/            # Contratos de dados estritos (Pydantic V2)
│   │       ├── security/
│   │       │   └── sanitization/   # Motor de redação de PII (Mod 11 e Luhn)
│   │       └── main.py             # Entrypoint ASGI com gerenciamento de lifespan
│   └── tests/
│       ├── conftest.py             # Fixtures assíncronas em memória (ASGITransport)
│       ├── api/                    # Testes de integração de endpoints
│       └── security/               # Testes de algoritmos e proteção contra falsos positivos
└── frontend/                       # [Fase 6] Dashboard em Nuxt 3 + TypeScript
```

---

## 🚀 Roteiro de Desenvolvimento (Building in Public)

- [x] **Fase 1: Fundação do Core ASGI e Arquitetura**
  - Setup de dependências e lock determinístico com `uv`.
  - Configuração *fail-fast* via `pydantic-settings` e gerenciamento de *lifespan*.
  - Probes de saúde com `StrEnum` e timestamps conscientes em UTC (CWE-200 mitigation).
- [x] **Fase 2: Motor de Sanitização Bidirecional de PII**
  - Detecção e mascaramento de CPFs com validação matemática do **Módulo 11** da Receita Federal (zero falsos positivos em IDs).
  - Mascaramento de cartões de crédito via **Algoritmo de Luhn** (Módulo 10).
  - Assinaturas de segredos e chaves de nuvem (Google Gemini, OpenAI, AWS, GitHub).
  - Algoritmo de resolução de sobreposição de spans para preservação de contexto.
- [ ] **Fase 3: Detecção Heurística de Prompt Injection e Jailbreak** (OWASP LLM01).
- [ ] **Fase 4: Integração Segura com Google Gemini API** (Pipeline Fail-Closed).
- [ ] **Fase 5: Logs de Auditoria Estruturados para SIEM**.
- [ ] **Fase 6: Dashboard de Monitoramento em Nuxt 3 + Tailwind CSS**.

---

## 🛠️ Stack Tecnológica e Ferramentas

| Componente | Tecnologia | Decisão Técnica |
| :--- | :--- | :--- |
| **Linguagem & Runtime** | Python 3.11+ | Suporte nativo a `StrEnum`, `datetime.UTC` e alta performance assíncrona |
| **Framework Web** | FastAPI | Framework ASGI assíncrono para lidar com I/O-bound de alta latência de LLMs |
| **Validação de Schemas** | Pydantic V2 | Motor em Rust (`pydantic-core`) com `extra="forbid"` contra *parameter tampering* |
| **Gerenciador de Pacotes** | `uv` (Astral) | Resolução de dependências 10x-100x mais rápida e integridade de *supply chain* |
| **Qualidade & Linters** | Ruff & Mypy | Análise estática ultrarrápida e checagem de tipos em modo estrito (`strict = true`) |
| **Suíte de Testes** | Pytest-Asyncio | Testes de integração em memória via `httpx.ASGITransport` (execução em ~50ms) |

---

## ⚡ Começando (Quick Start)

### Pré-requisitos
- Python 3.11 ou superior
- [uv](https://astral.sh/uv) instalado no sistema

### 1. Clonar o repositório
```bash
git clone https://github.com/SEU_USUARIO/guard-llm.git
cd guard-llm/backend
```

### 2. Instalar dependências e sincronizar ambiente
```bash
uv sync --extra dev
```

### 3. Configurar variáveis de ambiente
```bash
cp .env.example .env
```

### 4. Executar os testes automatizados
```bash
uv run pytest
```

### 5. Executar verificações de tipo e estilo
```bash
uv run mypy src
uv run ruff check .
```

### 6. Subir o servidor de desenvolvimento
```bash
uv run uvicorn guardllm.main:app --reload --port 8000
```
- Acesse a documentação interativa: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Endpoint de saúde: `GET http://127.0.0.1:8000/api/v1/health`
- Endpoint de sanitização: `POST http://127.0.0.1:8000/api/v1/security/sanitize`

---

## 🔒 Postura de Segurança (AppSec Highlights)

- **Fail-Closed Design:** Em caso de exceção não tratada na camada de inspeção, o proxy bloqueia a requisição para evitar vazamento acidental.
- **Prevenção de Falsos Positivos:** Validações algorítmicas oficiais impedem que números de pedidos legítimos ou métricas sejam mascarados.
- **Zero Information Leakage:** A interface Swagger (`/docs`) é desativada automaticamente caso o ambiente seja configurado para `production`.
- **CORS Restritivo:** Lista de origens permitidas validada rigorosamente na inicialização.

---

## 📄 Licença
Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.
