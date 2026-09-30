import re
from dataclasses import dataclass

from guardllm.schemas.injection import InjectionCategory

# Caracteres invisíveis (Zero-Width) frequentemente usados para bypass de filtros
ZERO_WIDTH_CHARS_PATTERN: re.Pattern[str] = re.compile(
    r"[\u200B\u200C\u200D\u200E\u200F\uFEFF\u00AD]"
)


@dataclass(frozen=True)
class InjectionRule:
    """Regra heurística de detecção com peso calibrado de risco."""

    pattern_id: str
    category: InjectionCategory
    regex: re.Pattern[str]
    weight: float


def normalize_text(text: str) -> str:
    """Desobfusca e normaliza o texto removendo caracteres invisíveis e espaços."""
    # 1. Remove caracteres invisíveis e formatadores ocultos
    cleaned = ZERO_WIDTH_CHARS_PATTERN.sub("", text)
    # 2. Colapsa espaços repetidos e quebras de linha artificiais
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


# Conjunto rigoroso de regras de detecção de injeção direta (OWASP LLM01)
INJECTION_RULES: list[InjectionRule] = [
    # 1. SYSTEM OVERRIDE (Tentativas de cancelar diretrizes de sistema)
    InjectionRule(
        pattern_id="OVERRIDE_IGNORE_INSTRUCTIONS_EN",
        category=InjectionCategory.SYSTEM_OVERRIDE,
        regex=re.compile(
            r"\b(?:ignore|disregard|forget|bypass|override)\b.*?"
            r"\b(?:all|previous|above|initial|prior)\b.*?"
            r"\b(?:instructions?|prompts?|rules?|guidelines?|directions?|constraints?)\b",
            re.IGNORECASE,
        ),
        weight=0.85,
    ),
    InjectionRule(
        pattern_id="OVERRIDE_IGNORE_INSTRUCTIONS_PT",
        category=InjectionCategory.SYSTEM_OVERRIDE,
        regex=re.compile(
            r"\b(?:ignore|desconsidere|esque[cç]a|anule)\b.*?"
            r"\b(?:todas\s+as|suas|quaisquer)\b.*?"
            r"\b(?:instru[cç][oõ]es|regras|diretrizes|orienta[cç][oõ]es)\b",
            re.IGNORECASE,
        ),
        weight=0.85,
    ),
    InjectionRule(
        pattern_id="OVERRIDE_NEW_SYSTEM_ROLE",
        category=InjectionCategory.SYSTEM_OVERRIDE,
        regex=re.compile(
            r"\b(?:you\s+must\s+now\s+follow|new\s+system\s+directive|"
            r"from\s+now\s+on\s+you\s+only)\b",
            re.IGNORECASE,
        ),
        weight=0.75,
    ),
    # 2. ROLEPLAY JAILBREAK (Modo DAN, Developer Mode, Persona sem filtros)
    InjectionRule(
        pattern_id="JAILBREAK_DAN_PERSONA",
        category=InjectionCategory.ROLEPLAY_JAILBREAK,
        regex=re.compile(
            r"\b(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be|voc[eê]\s+agora\s+[eé])\b.*?"
            r"\b(?:DAN|do\s+anything\s+now|evil\s*bot|jailbroken|sem\s+filtros)\b",
            re.IGNORECASE,
        ),
        weight=0.90,
    ),
    InjectionRule(
        pattern_id="JAILBREAK_DEVELOPER_MODE",
        category=InjectionCategory.ROLEPLAY_JAILBREAK,
        regex=re.compile(
            r"\b(?:developer\s+mode\s+(?:enabled|active|ativado|habilitado)|"
            r"modo\s+desenvolvedor\s+(?:ativado|ligado))\b",
            re.IGNORECASE,
        ),
        weight=0.90,
    ),
    InjectionRule(
        pattern_id="JAILBREAK_FILTER_REMOVAL",
        category=InjectionCategory.ROLEPLAY_JAILBREAK,
        regex=re.compile(
            r"\b(?:bypass|disable|turn\s+off|desative)\b.*?"
            r"\b(?:safety|ethical|content|seguran[cç]a|filtros?)\b.*?"
            r"\b(?:filters?|protocols?|guidelines?|regras?)\b",
            re.IGNORECASE,
        ),
        weight=0.85,
    ),
    # 3. SYSTEM PROMPT LEAK (Tentativas de extrair regras internas corporativas)
    InjectionRule(
        pattern_id="LEAK_SYSTEM_PROMPT_EN",
        category=InjectionCategory.SYSTEM_LEAK,
        regex=re.compile(
            r"\b(?:repeat|reveal|output|display|show|print)\b.*?"
            r"\b(?:verbatim|exact|initial|system)\b.*?"
            r"\b(?:prompt|instructions?|context|guidelines?)\b",
            re.IGNORECASE,
        ),
        weight=0.80,
    ),
    InjectionRule(
        pattern_id="LEAK_SYSTEM_PROMPT_PT",
        category=InjectionCategory.SYSTEM_LEAK,
        regex=re.compile(
            r"\b(?:repita|mostre|revele|imprima|exiba)\b.*?"
            r"\b(?:palavra\s+por\s+palavra|exatamente|seu|o)\b.*?"
            r"\b(?:prompt\s+de\s+sistema|instru[cç][oõ]es\s+iniciais|prompt\s+inicial)\b",
            re.IGNORECASE,
        ),
        weight=0.80,
    ),
    # 4. DELIMITER & BOUNDARY HIJACKING (Manipulação de tags de controle)
    InjectionRule(
        pattern_id="DELIMITER_STRUCTURAL_TAGS",
        category=InjectionCategory.DELIMITER_HIJACK,
        regex=re.compile(
            r"(?:<\|im_start\|>|<\|im_end\|>|<\|system\|>|<<SYS>>|<\/s>|\[INST\]|\[SYSTEM\])",
            re.IGNORECASE,
        ),
        weight=0.95,
    ),
    InjectionRule(
        pattern_id="DELIMITER_ARTIFICIAL_BOUNDARIES",
        category=InjectionCategory.DELIMITER_HIJACK,
        regex=re.compile(
            r"(?:---END\s+OF\s+SYSTEM\s+PROMPT---|---BEGIN\s+SYSTEM\s+INSTRUCTIONS---|===SYSTEM===)",
            re.IGNORECASE,
        ),
        weight=0.90,
    ),
]
