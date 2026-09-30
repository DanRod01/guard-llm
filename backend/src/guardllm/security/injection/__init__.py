"""Security package for Prompt Injection and Jailbreak mitigation."""

from guardllm.security.injection.detector import (
    InjectionDetector,
    injection_detector,
)

__all__ = ["InjectionDetector", "injection_detector"]
