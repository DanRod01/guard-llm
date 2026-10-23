from fastapi import APIRouter, Query, status

from guardllm.schemas.audit import AuditEventsListResponse, AuditStats
from guardllm.services.audit import audit_logger

router = APIRouter()


@router.get(
    "/events",
    response_model=AuditEventsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar Eventos Recentes de Auditoria",
    description=(
        "Retorna os eventos mais recentes armazenados no ring buffer de telemetria."
    ),
)
async def list_audit_events(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Quantidade máxima de eventos a retornar",
    ),
) -> AuditEventsListResponse:
    """Retorna eventos recentes ordenados do mais novo ao mais antigo."""
    events = audit_logger.get_recent_events(limit=limit)
    return AuditEventsListResponse(total=len(events), events=events)


@router.get(
    "/stats",
    response_model=AuditStats,
    status_code=status.HTTP_200_OK,
    summary="Métricas Consolidadas de Telemetria e Segurança",
    description=(
        "Calcula métricas agregadas de requisições, injeções, PIIs e latência "
        "para o Dashboard."
    ),
)
async def get_audit_stats() -> AuditStats:
    """Retorna as métricas agregadas de segurança e desempenho para o Dashboard."""
    return audit_logger.get_stats()


@router.delete(
    "/events",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Limpar Histórico Local de Auditoria",
    description=("Limpa o buffer circular em memória (útil para reinício de sessões)."),
)
async def clear_audit_events() -> None:
    """Limpa os eventos armazenados no ring buffer em memória."""
    audit_logger.clear()
