from typing import List, Callable, Dict, Tuple
from core.tcb import TaskControlBlock
from core.cpu import CPU

# ==============================================================================
# 1. FUNÇÕES DE PRIORIDADE DOS ALGORITMOS (RETORNAM A CHAVE DE ORDENAÇÃO)
# ==============================================================================
# Regra: Tupla com valores MENORES indica MAIOR prioridade.

def get_rm_priority_key(tcb: TaskControlBlock, is_running: bool = False) -> Tuple:
    """
    Rate Monotonic (RM) + Critérios Estritos de Desempate (Seção 4.3).
    Critério Primário: Menor Período.
    """
    running_affinity = 0 if (is_running or tcb.estado == "EXECUTANDO") else 1

    return (
        tcb.periodo,            # 1. Algoritmo RM: Menor período = maior prioridade
        running_affinity,       # 2. Desempate 1 (Seção 4.3): Prioriza tarefa já em execução
        tcb.prazo_absoluto,     # 3. Desempate 2 (Seção 4.3): Menor prazo absoluto
        tcb.ingresso,           # 4. Desempate 3 (Seção 4.3): Instante de ingresso (FIFO)
        tcb.duracao_total,      # 5. Desempate 4 (Seção 4.3): Menor duração total
        tcb.id                  # 6. Desempate 5: ID único
    )


def get_edf_priority_key(tcb: TaskControlBlock, is_running: bool = False) -> Tuple:
    """
    Earliest Deadline First (EDF) + Critérios Estritos de Desempate (Seção 4.3).
    Critério Primário: Menor Prazo Absoluto (deadline mais próximo).
    """
    running_affinity = 0 if (is_running or tcb.estado == "EXECUTANDO") else 1

    return (
        tcb.prazo_absoluto,     # 1. Algoritmo EDF: Menor prazo absoluto
        running_affinity,       # 2. Desempate 1 (Seção 4.3): Prioriza tarefa já em execução
        tcb.ingresso,           # 3. Desempate 3 (Seção 4.3): Instante de ingresso (FIFO)
        tcb.duracao_total,      # 4. Desempate 4 (Seção 4.3): Menor duração total
        tcb.id                  # 5. Desempate 5: ID único
    )


# ==============================================================================
# 2. DICIONÁRIO REGISTRADOR DE ALGORITMOS (SCHEDULER REGISTRY)
# ==============================================================================

SCHEDULER_REGISTRY: Dict[str, Callable[[TaskControlBlock, bool], Tuple]] = {
    "RM": get_rm_priority_key,
    "EDF": get_edf_priority_key,
}


# ==============================================================================
# 3. MOTOR DE EXECUÇÃO DO ESCALONADOR
# ==============================================================================

class RealTimeScheduler:
    """
    Classe responsável por receber os dados de entrada (TCBs, CPUs, Fila, Tick)
    e executar a alocação e preempção segundo o algoritmo selecionado.
    """

    @staticmethod
    def register_algorithm(name: str, priority_func: Callable[[TaskControlBlock, bool], Tuple]):
        """Permite cadastrar dinamicamente novos algoritmos sem alterar a classe."""
        SCHEDULER_REGISTRY[name.upper().strip()] = priority_func

    @staticmethod
    def run(
        tcbs: List[TaskControlBlock],
        cpus: List[CPU],
        ready_queue: List[TaskControlBlock],
        current_tick: int,
        algorithm: str = "EDF"
    ) -> None:
        """Executa 1 ciclo de escalonamento para as CPUs e Fila de Prontos."""
        algo_str = algorithm.upper()
        if "RM" in algo_str:
            algo_key = "RM"
        elif "EDF" in algo_str:
            algo_key = "EDF"
        else:
            algo_key = "EDF"
        
        # Busca o algoritmo cadastrado
        priority_func = SCHEDULER_REGISTRY.get(algo_key, get_edf_priority_key)
        tcb_map = {t.id: t for t in tcbs}

        # 1. Atualiza liberações (releases) no tick atual e transiciona para PRONTA
        for tcb in tcbs:
            if tcb.estado in ["SUSPENSA", "CANCELADA"] or tcb.execucoes_concluidas >= tcb.limite_execucoes:
                continue

            if tcb.proximo_release <= current_tick:
                if tcb not in ready_queue and tcb.estado != "EXECUTANDO":
                    tcb.estado = "PRONTA"
                    ready_queue.append(tcb)

        # 2. Ordena a fila de prontos com base na função do algoritmo escolhido
        ready_queue.sort(key=lambda t: priority_func(t, False))

        # 3. Aloca tarefas da fila nas CPUs que estiverem ociosas/desligadas
        for cpu in cpus:
            if cpu.status == CPU.STATUS_DESLIGADA and ready_queue:
                next_task = ready_queue.pop(0)
                cpu.assign_task(next_task)

        # 4. Avalia Preempção nas CPUs que estão rodando tarefas
        while ready_queue:
            top_ready_task = ready_queue[0]
            top_ready_key = priority_func(top_ready_task, False)

            worst_cpu = None
            worst_running_key = None

            # Localiza a CPU rodando a tarefa com a MENOR prioridade (chave maior)
            for cpu in cpus:
                if cpu.status == CPU.STATUS_EXECUTANDO and cpu.current_task_id in tcb_map:
                    running_task = tcb_map[cpu.current_task_id]
                    running_key = priority_func(running_task, True)

                    if worst_running_key is None or running_key > worst_running_key:
                        worst_running_key = running_key
                        worst_cpu = cpu

            # Se a tarefa da fila for mais prioritária que a pior na CPU -> realiza Preempção
            if worst_cpu and worst_running_key and top_ready_key < worst_running_key:
                preempted_task = tcb_map[worst_cpu.current_task_id]

                worst_cpu.release_task(preempted_task)
                preempted_task.estado = "PRONTA"
                ready_queue.append(preempted_task)

                ready_queue.sort(key=lambda t: priority_func(t, False))

                new_task = ready_queue.pop(0)
                worst_cpu.assign_task(new_task)
            else:
                break


def run_scheduler(
    tcbs: List[TaskControlBlock],
    cpus: List[CPU],
    ready_queue: List[TaskControlBlock],
    current_tick: int,
    algorithm: str = "EDF"
) -> None:
    RealTimeScheduler.run(tcbs, cpus, ready_queue, current_tick, algorithm)