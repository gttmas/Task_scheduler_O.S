from core.tcb import TaskControlBlock


def get_edf_priority_key(tcb: TaskControlBlock) -> tuple:
    """
    Critério do EDF:
    1. Menor Prazo Absoluto (vence primeiro).
    2. Desempate: Menor Período.
    3. Desempate final: ID da tarefa.
    """
    return (tcb.prazo_absoluto, tcb.periodo, tcb.id)
