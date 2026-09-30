from fastapi import APIRouter, status

from guardllm.schemas.injection import InjectionDetectRequest, InjectionVerdict
from guardllm.security.injection.detector import injection_detector

router = APIRouter()


@router.post(
    "/detect",
    response_model=InjectionVerdict,
    status_code=status.HTTP_200_OK,
    summary="Inspeciona texto contra Prompt Injection e Jailbreak",
    description=(
        "Analisa o texto fornecido contra padrões de sobrescrita de sistema, "
        "jailbreaks (DAN, Developer Mode), vazamento de prompt e manipulação "
        "de delimitadores."
    ),
)
async def detect_prompt_injection(
    payload: InjectionDetectRequest,
) -> InjectionVerdict:
    """Endpoint síncrono/CPU-bound para auditoria avulsa de Prompt Injection."""
    return injection_detector.detect(
        text=payload.text,
        threshold=payload.threshold,
    )
