from typing import List, Callable, Dict, Tuple
from core.tcb import TaskControlBlock
from core.cpu import CPU

# funções dos algoritmos
# para tuplas em python valores menores indicam maior prioridade

def get_rm_priority_key(tcb: TaskControlBlock, is_running: bool = False) -> Tuple:
    """
    rate monotonic (RM) + critérios estritos de desempate 
    critério do algoritmo: menor período
    """
    # Atribui 0 para tarefas em execução e 1 para tarefas na fila.
    # Como números menores têm maior prioridade, isso garante o desempate
    running_affinity = 0 if (is_running or tcb.estado == "EXECUTANDO") else 1

    return (
        tcb.periodo,            #  Menor período = maior prioridade
        running_affinity,       #  Desempate 1  Prioriza tarefa já em execução
        tcb.prazo_absoluto,     #  Desempate 2  Menor prazo absoluto
        tcb.ingresso,           #  Desempate 3  Instante de ingresso 
        tcb.duracao_total,      #  Desempate 4  Menor duração total
        tcb.id                  #  Desempate 5: ID único
    )


def get_edf_priority_key(tcb: TaskControlBlock, is_running: bool = False) -> Tuple:
    """
    earliest deadline first (EDF) + critérios estritos de desempate 
    critério do algoritmo: menor prazo absoluto
    """
    running_affinity = 0 if (is_running or tcb.estado == "EXECUTANDO") else 1

    return (
        tcb.prazo_absoluto,     #  Algoritmo EDF: Menor prazo absoluto
        running_affinity,       #  Desempate 1: Prioriza tarefa já em execução
        tcb.ingresso,           #  Desempate 3: Instante de ingresso 
        tcb.duracao_total,      #  Desempate 4: Menor duração total
        tcb.id                  #  Desempate 5: ID único
    )


# dicionário de algoritmos, funciona como um hash map, mas pode mapear funções
SCHEDULER_REGISTRY: Dict[str, Callable[[TaskControlBlock, bool], Tuple]] = {
    "RM": get_rm_priority_key,
    "EDF": get_edf_priority_key,
}

class RealTimeScheduler:
    """
    classe responsável por receber os dados de entrada (TCBs, CPUs, Fila, Tick)
    e fazer a alocação e preempção usando o algoritmo selecionado.
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
        #tudo pra maiúsculo pra ficar de acordo com o dicionário        
        algo_str = algorithm.upper()
        #extrai a substring RM ou EDF e seta como chave do dic 
        if "RM" in algo_str:
            algo_key = "RM"
        elif "EDF" in algo_str:
            algo_key = "EDF"
        else:
            algo_key = "EDF" #se não tiver a substring usa o edf como padrão
        
        # busca o algoritmo cadastrado
        priority_func = SCHEDULER_REGISTRY.get(algo_key, get_edf_priority_key)
        tcb_map = {t.id: t for t in tcbs}

        # atualiza liberações no tick atual e transiciona para PRONTA
        for tcb in tcbs:
            #ignora tarefas concluidas/suspensas/canceladas
            if tcb.estado in ["SUSPENSA", "CANCELADA"] or tcb.execucoes_concluidas >= tcb.limite_execucoes:
                continue
            #ve se o relógio atingiu o tempo de liberação da tarefa, e então coloca na fila de prontas
            if tcb.proximo_release <= current_tick:
                if tcb not in ready_queue and tcb.estado != "EXECUTANDO":
                    tcb.estado = "PRONTA"
                    ready_queue.append(tcb)

        #ordena a fila de prontos com base na função do algoritmo escolhido
        ready_queue.sort(key=lambda t: priority_func(t, False))

        #aloca tarefas da fila nas CPUs que estiverem desligadas
        for cpu in cpus:
            if cpu.status == CPU.STATUS_DESLIGADA and ready_queue:
                next_task = ready_queue.pop(0)
                cpu.assign_task(next_task)

        # avalia preempção nas CPUs que estão rodando tarefas
        while ready_queue:
            top_ready_task = ready_queue[0]#pega o elemento de maior prioridade
            top_ready_key = priority_func(top_ready_task, False)#calcula a prioridade da tarefa

            #variáveis pra armazenar a cpu com a tarefa de menor prioridade do sistema
            worst_cpu = None
            worst_running_key = None

            # localiza a CPU rodando a tarefa com a menor prioridade, ou seja, a maior chave
            for cpu in cpus:
                if cpu.status == CPU.STATUS_EXECUTANDO and cpu.current_task_id in tcb_map:
                    running_task = tcb_map[cpu.current_task_id]
                    running_key = priority_func(running_task, True)

                    if worst_running_key is None or running_key > worst_running_key:
                        worst_running_key = running_key
                        worst_cpu = cpu

            # se a tarefa do topo da fila for mais prioritária que a pior na CPU realiza preempção trocando a que está executando
            if worst_cpu and worst_running_key and top_ready_key < worst_running_key:
                #salva o id da task em uma variável
                preempted_task = tcb_map[worst_cpu.current_task_id]

                #libera da cpu, muda o estado e inclue na fila de prontas
                worst_cpu.release_task(preempted_task)
                preempted_task.estado = "PRONTA"
                ready_queue.append(preempted_task)

                ready_queue.sort(key=lambda t: priority_func(t, False))#reordena a fila após adicionar a tarefa preemptada

                #coloca a tarefa do topo da fila em execução na cpu
                new_task = ready_queue.pop(0)
                worst_cpu.assign_task(new_task)
            else:
                break

#funciona como um ponto de entrada pro resto do código, repassando os argumentos recebidos pro método RealTimeScheduler.run()
def run_scheduler(
    tcbs: List[TaskControlBlock],#lita de tcbs
    cpus: List[CPU],#lista de cpus
    ready_queue: List[TaskControlBlock],#lista de prontas
    current_tick: int,#tick atual
    algorithm: str = "EDF"#algritmo
) -> None:
    RealTimeScheduler.run(tcbs, cpus, ready_queue, current_tick, algorithm)#chama a função atual repassando