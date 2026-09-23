import re

# Padrões Regex pré-compilados na inicialização para máxima performance
EMAIL_PATTERN: re.Pattern[str] = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# CPF com máscara (000.000.000-00) ou apenas 11 dígitos numéricos
CPF_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})\b"
)

# Possíveis números de cartão de crédito (13 a 19 dígitos)
CREDIT_CARD_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{1,7})\b"
)

# Assinaturas conhecidas de chaves de API e segredos de nuvem
API_KEY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bAIzaSy[A-Za-z0-9_-]{33}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}\b"),
]


def validate_cpf_checksum(raw_cpf: str) -> bool:
    """Valida se uma sequência obedece ao algoritmo oficial de Módulo 11 do CPF.

    Evita falsos positivos em IDs de pedidos, timestamps ou códigos numéricos.
    """
    digits = [int(c) for c in raw_cpf if c.isdigit()]
    if len(digits) != 11:
        return False

    # Descarta sequências com todos os dígitos iguais (ex: 111.111.111-11)
    if len(set(digits)) == 1:
        return False

    # Primeiro dígito verificador
    sum1 = sum(digits[i] * (10 - i) for i in range(9))
    remainder1 = (sum1 * 10) % 11
    expected_d1 = 0 if remainder1 == 10 else remainder1
    if digits[9] != expected_d1:
        return False

    # Segundo dígito verificador
    sum2 = sum(digits[i] * (11 - i) for i in range(10))
    remainder2 = (sum2 * 10) % 11
    expected_d2 = 0 if remainder2 == 10 else remainder2
    return digits[10] == expected_d2


def validate_luhn_checksum(raw_card: str) -> bool:
    """Valida se uma sequência numérica satisfaz o Algoritmo de Luhn (Módulo 10).

    Padrão utilizado por bandeiras de cartão (Visa, Mastercard, Amex, Elo).
    """
    digits = [int(c) for c in raw_card if c.isdigit()]
    if not (13 <= len(digits) <= 19):
        return False

    checksum = 0
    reverse_digits = digits[::-1]

    for index, digit in enumerate(reverse_digits):
        if index % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit

    return checksum % 10 == 0
