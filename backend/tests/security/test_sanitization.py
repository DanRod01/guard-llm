from guardllm.schemas.sanitization import PIIType
from guardllm.security.sanitization.engine import SanitizerEngine


def test_sanitize_empty_string() -> None:
    engine = SanitizerEngine()
    result = engine.sanitize("")

    assert result.sanitized_text == ""
    assert not result.contains_pii
    assert len(result.entities_detected) == 0


def test_sanitize_valid_cpf() -> None:
    engine = SanitizerEngine()
    # CPF válido matematicamente pelo algoritmo da Receita Federal
    valid_cpf = "529.982.247-25"
    text = f"O CPF do usuário Daniel é {valid_cpf} para cadastro."

    result = engine.sanitize(text)

    assert result.contains_pii
    assert valid_cpf not in result.sanitized_text
    assert "[REDACTED_CPF]" in result.sanitized_text
    assert len(result.entities_detected) == 1
    assert result.entities_detected[0].entity_type == PIIType.CPF


def test_ignore_invalid_cpf_false_positive() -> None:
    engine = SanitizerEngine()
    # Sequência de dígitos repetidos ou soma inválida não deve ser mascarada
    fake_sequence = "111.111.111-11"
    order_id = "12345678901"
    text = f"Pedido #{order_id} e código de teste {fake_sequence}."

    result = engine.sanitize(text)

    assert not result.contains_pii
    assert result.sanitized_text == text
    assert len(result.entities_detected) == 0


def test_sanitize_emails() -> None:
    engine = SanitizerEngine()
    text = "Envie logs para sec@guardllm.io ou suporte.dev@empresa.com.br."

    result = engine.sanitize(text)

    assert result.contains_pii
    assert "sec@guardllm.io" not in result.sanitized_text
    assert "suporte.dev@empresa.com.br" not in result.sanitized_text
    assert result.sanitized_text.count("[REDACTED_EMAIL]") == 2
    assert len(result.entities_detected) == 2


def test_sanitize_credit_card_with_luhn() -> None:
    engine = SanitizerEngine()
    # Cartão de teste de 16 dígitos válido no Algoritmo de Luhn (Módulo 10)
    valid_card = "4532 0150 0000 0007"
    text = f"Pagamento autorizado no cartão {valid_card}."

    result = engine.sanitize(text)

    assert result.contains_pii
    assert valid_card not in result.sanitized_text
    assert "[REDACTED_CREDIT_CARD]" in result.sanitized_text


def test_sanitize_cloud_api_keys() -> None:
    engine = SanitizerEngine()
    gemini_key = "AIzaSy" + "A" * 33
    openai_key = "sk-proj-abc1234567890123456789012345"
    aws_key = "AKIAIOSFODNN7EXAMPLE"

    text = f"Chaves vazadas: Gemini={gemini_key}, OpenAI={openai_key}, AWS={aws_key}"

    result = engine.sanitize(text)

    assert result.contains_pii
    assert gemini_key not in result.sanitized_text
    assert openai_key not in result.sanitized_text
    assert aws_key not in result.sanitized_text
    assert result.sanitized_text.count("[REDACTED_API_KEY]") == 3


def test_mixed_sensitive_payload_preserves_context() -> None:
    engine = SanitizerEngine()
    valid_cpf = "529.982.247-25"
    email = "admin@guardllm.io"
    api_key = "AKIAIOSFODNN7EXAMPLE"

    prompt = (
        f"Analise o cliente Daniel (CPF: {valid_cpf}, email: {email}) "
        f"utilizando a credencial {api_key}."
    )

    result = engine.sanitize(prompt)

    expected = (
        "Analise o cliente Daniel (CPF: [REDACTED_CPF], email: [REDACTED_EMAIL]) "
        "utilizando a credencial [REDACTED_API_KEY]."
    )

    assert result.sanitized_text == expected
    assert len(result.entities_detected) == 3
