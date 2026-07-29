from app.gemini_client import GeminiPermanentError, GeminiTransientError, classify_gemini_exception


def test_invalid_api_key_is_permanent():
    classified = classify_gemini_exception(Exception("API key not valid 400"))
    assert isinstance(classified, GeminiPermanentError)


def test_timeout_is_transient():
    classified = classify_gemini_exception(Exception("timeout 504"))
    assert isinstance(classified, GeminiTransientError)
