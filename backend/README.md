# GuardLLM Backend — Defensive Security Reverse Proxy for LLMs

O backend do **GuardLLM** é construído em Python 3.11+, FastAPI e Pydantic V2, atuando como um gateway defensivo que higieniza entradas e saídas de Modelos de Linguagem (LLMs) e mitiga ativamente ataques do OWASP Top 10 for LLMs.

## Módulos Implementados

- **Core & Configuração (`guardllm.core`)**: Configurações imutáveis via `pydantic-settings`, validação estrita de CORS e gerenciamento de *lifespan*.
- **Mitigação de Prompt Injection (`guardllm.security.injection`)**: Normalização anti-obfuscação (remoção de caracteres invisíveis Unicode), motor multicategoria (System Override, DAN/Developer Mode, System Leak, Delimiter Hijack) e scoring probabilístico saturado.
- **Sanitização de PII (`guardllm.security.sanitization`)**: Validação matemática de CPFs (Módulo 11), cartões de crédito (Algoritmo de Luhn), segredos de nuvem (Gemini, OpenAI, AWS, GitHub) e resolução gananciosa de sobreposição de spans.
- **Integração Upstream (`guardllm.services.gemini`)**: Cliente assíncrono para a API REST do Google Gemini com *Connection Pooling*, autenticação segura via cabeçalhos e política *Fail-Closed*.
- **Orquestrador de Proxy (`guardllm.services.proxy`)**: Pipeline defensivo Dual-Gate (Inbound Injection Defense & PII Sanitization $\rightarrow$ Gemini Dispatch $\rightarrow$ Outbound Sanitization) com telemetria LLMOps completa (latência e tokens).
- **API v1 (`guardllm.api.v1`)**: Endpoints versionados para health checks (`/health`), sanitização direta (`/security/sanitize`), inspeção de injeção (`/security/injection/detect`) e proxy de chat (`/proxy/chat`).

## Verificações de Qualidade

```bash
uv run ruff check .
uv run mypy src tests
uv run pytest -v
```
