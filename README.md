# 🛡️ GuardLLM — Defensive Security Reverse Proxy for LLMs

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-ASGI-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic V2](https://img.shields.io/badge/Pydantic-V2%20(Rust%20Core)-e92063.svg)](https://docs.pydantic.dev/)
[![Package Manager](https://img.shields.io/badge/Package%20Manager-uv-purple.svg)](https://astral.sh/uv)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-black.svg)](https://docs.astral.sh/ruff/)
[![Type Checking](https://img.shields.io/badge/Types-Mypy%20Strict-blue.svg)](https://mypy-lang.org/)
[![Tests Passing](https://img.shields.io/badge/Tests-23%20passed%20(0.18s)-brightgreen.svg)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

O **GuardLLM** é um proxy reverso defensivo de alta performance e segurança de ponta a ponta projetado para inspecionar, sanitizar e auditar interações com Modelos de Linguagem (LLMs) em produção. 

Atuando como um **AI Security Gateway** intermediário entre clientes e provedores de IA (como Google Gemini e OpenAI), o GuardLLM neutraliza riscos críticos do **OWASP Top 10 for LLMs** (em especial **LLM06: Sensitive Information Disclosure**) e garante conformidade estrita com normas globais de privacidade (**LGPD e GDPR**).

---

## 🏛️ Arquitetura do Repositório

O projeto segue princípios estritos de **Clean Architecture**, **Separation of Concerns (SoC)** e a metodologia **Twelve-Factor App**:

```text
guard-llm/
├── backend/
│   ├── pyproject.toml              # Dependências, tooling (Ruff, Mypy, Pytest) e empacotamento
│   ├── uv.lock                     # Lockfile determinístico com integridade de hash
│   ├── .env.example                # Template seguro de variáveis de ambiente
│   ├── src/
│   │   └── guardllm/
│   │       ├── api/
│   │       │   └── v1/
│   │       │       ├── endpoints/  # Rotas HTTP versionadas (health, sanitization, proxy)
│   │       │       └── router.py   # Agregador central de rotas v1
│   │       ├── core/
│   │       │   └── config.py       # Pydantic-settings imutável e fail-fast
│   │       ├── schemas/            # Contratos Pydantic V2 (Rust Core, extra="forbid", frozen)
│   │       │   ├── health.py
│   │       │   ├── sanitization.py
│   │       │   └── proxy.py        # Modelos para chat, auditoria e telemetria LLMOps
│   │       ├── security/
│   │       │   └── sanitization/   # Motor de redação de PII (Módulo 11 e Luhn)
│   │       │       ├── engine.py   # SanitizerEngine com resolução de sobreposição de spans
│   │       │       └── rules.py    # Algoritmos de checksum e assinaturas regex pré-compiladas
│   │       ├── services/           # Camada de integração com provedores e orquestração
│   │       │   ├── gemini.py       # Cliente HTTP assíncrono com pooling e headers seguros
│   │       │   └── proxy.py        # ProxyService: orquestrador do pipeline Dual-Gate
│   │       └── main.py             # Entrypoint ASGI com gerenciamento de lifespan
│   └── tests/
│       ├── conftest.py             # Fixtures assíncronas em memória (httpx.ASGITransport)
│       ├── api/                    # Testes de integração de endpoints (/health, /sanitize, /proxy)
│       ├── security/               # Testes dos algoritmos matemáticos e mitigação de falsos positivos
│       └── services/               # Testes unitários do cliente Gemini e orquestrador do proxy
└── frontend/                       # [Fase 6] Dashboard de Monitoramento em Nuxt 3 + TypeScript
```

---

## 🔄 Fluxo de Segurança: O Padrão Dual-Gate (Inbound & Outbound)

O GuardLLM implementa uma proteção bidirecional rigorosa:

```
[ Aplicação Consumidora / Chatbot ]
              │
              ▼ (Prompt com possíveis PIIs / Chaves)
    ┌────────────────────────────────────────────────────────┐
    │ 1. INBOUND SECURITY GATE                               │
    │    - Regex pré-compilada para extração de candidatos   │
    │    - Validação algorítmica: Módulo 11 (CPF)            │
    │    - Validação algorítmica: Algoritmo de Luhn (Cartão) │
    │    - Detecção de segredos (Gemini, OpenAI, AWS, GitHub)│
    │    - Desempate ganancioso de spans sobrepostos         │
    │    - Substituição por tokens seguros [REDACTED_...]    │
    └────────────────────────────────────────────────────────┘
              │ (Prompt Sanitizado)
              ▼
    ┌────────────────────────────────────────────────────────┐
    │ 2. RESILIENT LLM DISPATCH (Google Gemini API)          │
    │    - Connection Pooling com httpx.AsyncClient          │
    │    - Autenticação via cabeçalho x-goog-api-key         │
    │    - Controle de timeout (30s) e fail-closed           │
    │    - Fechamento gracioso de conexões no lifespan       │
    └────────────────────────────────────────────────────────┘
              │ (Resposta bruta gerada pelo modelo)
              ▼
    ┌────────────────────────────────────────────────────────┐
    │ 3. OUTBOUND SECURITY GATE                              │
    │    - Inspeciona o texto retornado contra alucinações   │
    │    - Mascara PIIs antes da entrega final ao usuário    │
    │    - Agrega telemetria LLMOps (tokens e latência)      │
    └────────────────────────────────────────────────────────┘
              │
              ▼
[ Resposta Higienizada + Metadados de Auditoria ]
```

---

## 🚀 Roteiro de Desenvolvimento (Building in Public)

- [x] **Fase 1: Fundação do Core ASGI e Arquitetura**
  - Setup de dependências e lock determinístico com `uv`.
  - Configuração *fail-fast* via `pydantic-settings` e gerenciamento de *lifespan*.
  - Probes de saúde com `StrEnum` e timestamps conscientes em UTC (mitigação CWE-200).
- [x] **Fase 2: Motor de Sanitização Bidirecional de PII**
  - Detecção e mascaramento de CPFs com validação matemática do **Módulo 11** da Receita Federal (zero falsos positivos em IDs numéricos).
  - Mascaramento de cartões de crédito via **Algoritmo de Luhn** (Módulo 10 - ISO/IEC 7812).
  - Assinaturas de segredos e chaves de nuvem (Google Gemini, OpenAI, AWS IAM, GitHub Tokens).
  - Algoritmo de resolução de sobreposição de spans com ordenação gananciosa e reconstrução linear $O(N)$.
- [x] **Fase 3: Proxy Reversivo Assíncrono com Dual-Gate & Integração Gemini**
  - Orquestrador de proxy com proteção de entrada (*Inbound Gate*) e saída (*Outbound Gate*).
  - Cliente assíncrono para Google Gemini com *Connection Pooling* persistente via `httpx`.
  - Autenticação estrita via cabeçalho HTTP (`x-goog-api-key`), eliminando vazamentos em URLs/logs.
  - Arquitetura *Fail-Closed* com mapeamento semântico de erros (HTTP 502, 503 e 504).
  - Observabilidade LLMOps: métricas de latência em milissegundos e consumo de tokens (`prompt`, `candidate`, `total`).
  - Suíte de 23 testes automatizados passando em 0.18s.
- [ ] **Fase 4: Detecção Semântica de Prompt Injection e Jailbreak (OWASP LLM01)**.
- [ ] **Fase 5: Logs de Auditoria Estruturados para SIEM e OpenTelemetry**.
- [ ] **Fase 6: Dashboard de Monitoramento em Nuxt 3 + Tailwind CSS**.

---

## 🛠️ Stack Tecnológica e Ferramentas

| Componente | Tecnologia | Decisão Técnica |
| :--- | :--- | :--- |
| **Linguagem & Runtime** | Python 3.11+ | Suporte nativo a `StrEnum`, `datetime.UTC` e concorrência assíncrona moderna |
| **Framework Web** | FastAPI | Framework ASGI assíncrono de alto rendimento para I/O-bound de LLMs |
| **Validação de Schemas** | Pydantic V2 | Motor em Rust (`pydantic-core`) com `extra="forbid"` contra *parameter tampering* |
| **Gerenciador de Pacotes** | `uv` (Astral) | Resolução de dependências ultrarrápida e integridade determinística de *supply chain* |
| **Qualidade & Linters** | Ruff & Mypy Strict | Análise estática instantânea e tipagem estrita com 100% de cobertura |
| **Cliente HTTP** | `httpx` | Conexões assíncronas com pooling persistente e controle granular de timeouts |
| **Suíte de Testes** | Pytest-Asyncio | Testes assíncronos em memória via `ASGITransport` e mocks determinísticos (0.18s) |

---

## ⚡ Começando (Quick Start)

### Pré-requisitos
- Python 3.11 ou superior
- [uv](https://astral.sh/uv) instalado no sistema

### 1. Clonar o repositório
```bash
git clone https://github.com/DanRod01/guard-llm.git
cd guard-llm/backend
```

### 2. Instalar dependências e sincronizar ambiente
```bash
uv sync --extra dev
```

### 3. Configurar variáveis de ambiente
```bash
cp .env.example .env
# Defina sua GEMINI_API_KEY no arquivo .env
```

### 4. Executar verificações de qualidade
```bash
uv run ruff check .
uv run mypy src tests
uv run pytest
```

### 5. Subir o servidor de desenvolvimento
```bash
uv run uvicorn guardllm.main:app --reload --port 8000
```
- Documentação Interativa Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (desativada automaticamente em produção)
- Probe de Saúde: `GET http://127.0.0.1:8000/api/v1/health`
- Endpoint de Sanitização Direta: `POST http://127.0.0.1:8000/api/v1/security/sanitize`
- **Endpoint de Proxy Defensivo**: `POST http://127.0.0.1:8000/api/v1/proxy/chat`

---

## 📡 Exemplo de Uso do Proxy Defensivo

### Requisição com Dados Sensíveis no Prompt
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/proxy/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "O cliente Daniel (email: daniel@guardllm.io, CPF: 529.982.247-25) solicitou suporte.",
    "sanitize_outbound": true
  }'
```

### Resposta Entregue pelo GuardLLM
O prompt chega ao Google Gemini já higienizado (`"O cliente Daniel (email: [REDACTED_EMAIL], CPF: [REDACTED_CPF]) solicitou suporte."`), e a resposta final retorna com auditoria de segurança completa:

```json
{
  "output_text": "Entendido. Como posso auxiliar o cliente com sua solicitação?",
  "security": {
    "inbound_audit": {
      "sanitized": true,
      "entities_redacted": [
        {
          "entity_type": "EMAIL",
          "masked_value": "[REDACTED_EMAIL]",
          "start_index": 26,
          "end_index": 45
        },
        {
          "entity_type": "CPF",
          "masked_value": "[REDACTED_CPF]",
          "start_index": 52,
          "end_index": 66
        }
      ],
      "original_length": 87,
      "sanitized_length": 76
    },
    "outbound_audit": {
      "sanitized": false,
      "entities_redacted": [],
      "original_length": 62,
      "sanitized_length": 62
    },
    "model_used": "gemini-1.5-flash",
    "latency_ms": 342.15,
    "prompt_tokens": 18,
    "candidate_tokens": 14,
    "total_tokens": 32
  }
}
```

---

## 🔒 Postura de Segurança (AppSec Highlights)

- **Fail-Closed por Padrão**: Falhas em credenciais ou componentes de segurança interrompem a chamada antes de qualquer exposição de dados.
- **Header-Based Auth**: Tokens de API nunca trafegam em parâmetros de URL (`query strings`), prevenindo gravação em logs de tráfego e proxies de borda.
- **Connection Pooling Persistente**: Reutilização de conexões TCP/TLS com o provedor de LLM, economizando centenas de milissegundos por requisição.
- **Prevenção de Falsos Positivos**: Algoritmos matemáticos oficiais (Módulo 11 e Luhn) evitam redação acidental de IDs numéricos e códigos de produto.
- **CORS Restritivo e Modelos Imutáveis**: Pydantic V2 configurado com `extra="forbid"` impede ataques de injeção de parâmetros arbitrários (*mass assignment*).

---

## 📄 Licença
Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.
