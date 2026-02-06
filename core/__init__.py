"""Core package for Zero-Loss Circuit Breaker."""
from .state import (
    TribunalState,
    CircuitBreakerThresholds,
    should_trigger_circuit_breaker,
    calculate_consensus
)
from .prompts import (
    SIGNAL_ANALYST_PROMPT,
    USER_ADVOCATE_PROMPT,
    RISK_OFFICER_PROMPT,
    JUDGE_PROMPT,
    AGENT_NAMES
)
from .graph import (
    build_tribunal_graph,
    compile_tribunal,
    run_tribunal
)

__all__ = [
    "TribunalState",
    "CircuitBreakerThresholds",
    "should_trigger_circuit_breaker",
    "calculate_consensus",
    "SIGNAL_ANALYST_PROMPT",
    "USER_ADVOCATE_PROMPT",
    "RISK_OFFICER_PROMPT",
    "JUDGE_PROMPT",
    "AGENT_NAMES",
    "build_tribunal_graph",
    "compile_tribunal",
    "run_tribunal"
]

