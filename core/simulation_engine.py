from typing import List, Dict, Any
from core.tcb import TaskControlBlock
from core.cpu import CPU


class SimulationEngine:
    """Motor central do Simulador de SO."""

    def __init__(self):
        self.raw_config: Dict[str, Any] = {}
        self.current_tick: int = 0
        self.cpus: List[CPU] = []
        self.tcbs: List[TaskControlBlock] = []
        self.ready_queue: List[TaskControlBlock] = []
        self.history: List[Dict[str, Any]] = []

    def init_from_config(self, config_data: Dict[str, Any]):
        """Inicializa ou reconfigura o motor."""
        self.raw_config = config_data
        self.reset()

    def set_cpu_count(self, new_count: int):
        """
        Ajusta o número de CPUs em tempo de execução sem resetar o relógio.
        """
        current_count = len(self.cpus)
        if new_count == current_count or new_count < 1:
            return

        if new_count > current_count:
            # Adiciona novas CPUs preservando as existentes
            for i in range(current_count + 1, new_count + 1):
                self.cpus.append(CPU(i))
        else:
            # Desaloca tarefas das CPUs que serão removidas
            for cpu in self.cpus[new_count:]:
                if cpu.current_task_id:
                    tcb = next((t for t in self.tcbs if t.id == cpu.current_task_id), None)
                    if tcb and tcb not in self.ready_queue:
                        tcb.estado = "PRONTA"
                        tcb.cpu_alocada = None
                        self.ready_queue.append(tcb)
            self.cpus = self.cpus[:new_count]

        self.raw_config["cpus"] = new_count
        # Atualiza o snapshot do tick atual
        if self.history:
            self.history[-1] = self.create_snapshot()

    def reset(self):
        """Reseta o motor para o Tick 0 e realiza a pré-alocação dos ingressos no t=0."""
        self.current_tick = 0
        self.history.clear()

        num_cpus = self.raw_config.get("cpus", 1)
        self.cpus = [CPU(i + 1) for i in range(num_cpus)]

        raw_tasks = self.raw_config.get("tasks", [])
        self.tcbs = [TaskControlBlock(t) for t in raw_tasks if isinstance(t, dict)]

        self.ready_queue = []

        # Realiza a alocação inicial para o t=0 sem consumir ticks
        self._check_releases_and_allocate()
        self.save_snapshot()

    def _check_releases_and_allocate(self):
        """Verifica quais tarefas chegaram e aloca em CPUs ociosas (sem executar tempo ainda)."""
        # 1. Novas tarefas que chegaram neste tick
        for tcb in self.tcbs:
            if tcb.proximo_release == self.current_tick and tcb.execucoes_concluidas < tcb.limite_execucoes:
                if tcb not in self.ready_queue and tcb.estado != "EXECUTANDO":
                    tcb.estado = "PRONTA"
                    self.ready_queue.append(tcb)

        # 2. Aloca tarefas da Fila de Prontos nas CPUs ociosas
        for cpu in self.cpus:
            if cpu.status != CPU.STATUS_EXECUTANDO and self.ready_queue:
                next_task = self.ready_queue.pop(0)
                cpu.assign_task(next_task)

    def save_snapshot(self):
        """Registra a foto exata do estado atual."""
        snapshot = self.create_snapshot()
        if self.current_tick < len(self.history):
            self.history = self.history[:self.current_tick]
        self.history.append(snapshot)

    def create_snapshot(self) -> Dict[str, Any]:
        return {
            "tick": self.current_tick,
            "cpus": [cpu.clone() for cpu in self.cpus],
            "tcbs": [tcb.clone() for tcb in self.tcbs],
            "ready_queue_ids": [tcb.id for tcb in self.ready_queue]
        }

    def restore_snapshot(self, snapshot: Dict[str, Any]):
        self.current_tick = snapshot["tick"]
        self.cpus = [cpu.clone() for cpu in snapshot["cpus"]]
        self.tcbs = [tcb.clone() for tcb in snapshot["tcbs"]]

        tcb_map = {tcb.id: tcb for tcb in self.tcbs}
        self.ready_queue = [tcb_map[tid] for tid in snapshot["ready_queue_ids"] if tid in tcb_map]

    def step_forward(self) -> Dict[str, Any]:
        """Avança exatamente 1 tick na simulação."""
        # 1. Executa 1 tick de processamento nas CPUs
        tcb_map = {tcb.id: tcb for tcb in self.tcbs}
        for cpu in self.cpus:
            cpu.tick()
            if cpu.current_task_id and cpu.current_task_id in tcb_map:
                running_task = tcb_map[cpu.current_task_id]
                running_task.duracao_restante -= 1

                # Verifica se a tarefa concluiu a execução
                if running_task.duracao_restante <= 0:
                    running_task.estado = "CONCLUIDA"
                    running_task.execucoes_concluidas += 1
                    running_task.duracao_restante = running_task.duracao_total
                    running_task.proximo_release += running_task.periodo
                    running_task.prazo_absoluto = running_task.proximo_release + running_task.prazo_relativo
                    cpu.release_task(running_task)

        # 2. Avança o tempo global
        self.current_tick += 1

        # 3. Processa releases do novo tick e aloca em CPUs livres
        self._check_releases_and_allocate()

        # 4. Salva o snapshot e retorna o novo estado
        self.save_snapshot()
        return self.get_current_state()

    def step_back(self) -> Dict[str, Any]:
        """Retrocede 1 tick na simulação utilizando o histórico."""
        if len(self.history) > 1:
            self.history.pop()
            previous_snapshot = self.history[-1]
            self.restore_snapshot(previous_snapshot)
        return self.get_current_state()

    def get_current_state(self) -> Dict[str, Any]:
        return {
            "tick": self.current_tick,
            "cpus": self.cpus,
            "tcbs": self.tcbs,
            "ready_queue": self.ready_queue,
            "algorithm": self.raw_config.get("algorithm", "RM"),
            "quantum": self.raw_config.get("quantum", 1)
        }