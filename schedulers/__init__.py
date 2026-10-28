from typing import List, Callable, Dict
from core.tcb import TaskControlBlock
from core.cpu import CPU
from .edf import get_edf_priority_key

# Tabela para mapear o nome do algoritmo à sua função de prioridade.
# Quando seu amigo fizer o RM, basta adicionar: "RM": get_rm_priority_key
SCHEDULER_REGISTRY: Dict[str, Callable[[TaskControlBlock], tuple]] = {
    "EDF": get_edf_priority_key,
}


def run_scheduler(
    tcbs: List[TaskControlBlock],
    cpus: List[CPU],
    ready_queue: List[TaskControlBlock],
    current_tick: int,
    algorithm: str = "EDF"
) -> None:
    """
    Função Genérica de Escalonamento de Tempo Real.
    
    Aplica a mecânica de estado de forma unificada e usa a função do algoritmo
    selecionado apenas para ordenar a fila e avaliar preempções.
    """
    # 1. Identifica a função de prioridade com base no algoritmo
    priority_key_func = SCHEDULER_REGISTRY.get(algorithm.upper(), get_edf_priority_key)
    tcb_map = {t.id: t for t in tcbs}

    # 2. Processa novos releases (chegada de tarefas no tick atual)
    for tcb in tcbs:
        if tcb.estado in ["SUSPENSA", "CANCELADA"] or tcb.execucoes_concluidas >= tcb.limite_execucoes:
            continue

        if tcb.proximo_release <= current_tick:
            if tcb not in ready_queue and tcb.estado != "EXECUTANDO":
                tcb.estado = "PRONTA"
                ready_queue.append(tcb)

    # 3. Ordena a Fila de Prontos usando o critério do algoritmo escolhido
    ready_queue.sort(key=priority_key_func)

    # 4. Aloca tarefas da fila nas CPUs que estiverem OCIOSAS
    for cpu in cpus:
        if cpu.status == CPU.STATUS_DESLIGADA and ready_queue:
            highest_priority_task = ready_queue.pop(0)
            cpu.assign_task(highest_priority_task)

    # 5. Avalia PREEMPÇÃO nas CPUs que estão EXECUTANDO
    while ready_queue:
        top_ready_task = ready_queue[0]
        top_ready_key = priority_key_func(top_ready_task)

        worst_cpu = None
        worst_running_key = None

        # Procura a CPU com a tarefa de MENOR prioridade (chave mais "alta")
        for cpu in cpus:
            if cpu.status == CPU.STATUS_EXECUTANDO and cpu.current_task_id in tcb_map:
                running_task = tcb_map[cpu.current_task_id]
                running_key = priority_key_func(running_task)

                if worst_running_key is None or running_key > worst_running_key:
                    worst_running_key = running_key
                    worst_cpu = cpu

        # Se a tarefa da fila tiver maior prioridade que a pior em execução, realiza a preempção
        if worst_cpu and worst_running_key and top_ready_key < worst_running_key:
            preempted_task = tcb_map[worst_cpu.current_task_id]

            worst_cpu.release_task(preempted_task)
            preempted_task.estado = "PRONTA"
            ready_queue.append(preempted_task)

            # Reordena a fila após devolução da tarefa
            ready_queue.sort(key=priority_key_func)

            # Insere a nova tarefa de maior prioridade na CPU
            new_task = ready_queue.pop(0)
            worst_cpu.assign_task(new_task)
        else:
            break
