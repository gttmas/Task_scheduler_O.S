"""
Pacote de Algoritmos de Escalonamento de Tempo Real.

Módulo de exportação de interfaces do pacote.
"""

from .schedulers import run_scheduler, SCHEDULER_REGISTRY
from .schedulers import get_rm_priority_key
from .schedulers import get_edf_priority_key

__all__ = [
    "run_scheduler",
    "register_scheduler",
    "SCHEDULER_REGISTRY",
    "get_rm_priority_key",
    "get_edf_priority_key",
]