from fastapi import APIRouter, status

from guardllm.schemas.sanitization import SanitizationResult, SanitizeRequest
from guardllm.security.sanitization.engine import sanitizer_engine

router = APIRouter()


@router.post(
    "/sanitize",
    response_model=SanitizationResult,
    status_code=status.HTTP_200_OK,
    summary="Inspeciona e mascara dados sensíveis (PII e Segredos)",
    description=(
        "Analisa o texto fornecido, valida algoritmicamente CPFs (Mod 11) "
        "e Cartões (Luhn), e substitui segredos por tokens de mascaramento seguros."
    ),
)
async def sanitize_text(payload: SanitizeRequest) -> SanitizationResult:
    """Endpoint de sanitização de PII síncrono/CPU-bound em background."""
    return sanitizer_engine.sanitize(payload.text)
