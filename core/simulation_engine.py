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
        """Inicializa o motor com as configurações carregadas na UI."""
        self.raw_config = config_data
        self.reset()

    def reset(self):
        """Reseta o motor para o Tick 0 e recria os objetos do zero."""
        self.current_tick = 0
        self.history.clear()

        # Instancia CPUs
        num_cpus = self.raw_config.get("cpus", 1)
        self.cpus = [CPU(i + 1) for i in range(num_cpus)]

        # Instancia TCBs a partir dos dicionários
        raw_tasks = self.raw_config.get("tasks", [])
        self.tcbs = [TaskControlBlock(t) for t in raw_tasks if isinstance(t, dict)]

        self.ready_queue = []
        self.save_snapshot()

    def save_snapshot(self):
        """Registra a 'foto' exata do estado atual para permitir retroceder no tempo."""
        snapshot = {
            "tick": self.current_tick,
            "cpus": [cpu.clone() for cpu in self.cpus],
            "tcbs": [tcb.clone() for tcb in self.tcbs],
            "ready_queue_ids": [tcb.id for tcb in self.ready_queue]
        }
        
        # Se for um novo tick após ter desfeito alguns passos, substitui o futuro
        if self.current_tick < len(self.history):
            self.history = self.history[:self.current_tick]
        self.history.append(snapshot)

    def restore_snapshot(self, snapshot: Dict[str, Any]):
        """Restaura o estado completo de um tick anterior."""
        self.current_tick = snapshot["tick"]
        self.cpus = [cpu.clone() for cpu in snapshot["cpus"]]
        self.tcbs = [tcb.clone() for tcb in snapshot["tcbs"]]

        # Re-mapeia as referências entre TCBs, Fila de Prontos e CPUs
        tcb_map = {tcb.id: tcb for tcb in self.tcbs}
        self.ready_queue = [tcb_map[tid] for tid in snapshot["ready_queue_ids"] if tid in tcb_map]

    def step_forward(self) -> Dict[str, Any]:
        """Avança exatamente 1 tick na simulação."""
        # 1. Checa novas releases de tarefas
        for tcb in self.tcbs:
            if tcb.proximo_release == self.current_tick and tcb.execucoes_concluidas < tcb.limite_execucoes:
                if tcb not in self.ready_queue and tcb.estado != "EXECUTANDO":
                    tcb.estado = "PRONTA"
                    self.ready_queue.append(tcb)

        # 2. Escalonamento preliminar (aloca tarefas em CPUs ociosas)
        for cpu in self.cpus:
            if cpu.status != CPU.STATUS_EXECUTANDO and self.ready_queue:
                next_task = self.ready_queue.pop(0)
                cpu.assign_task(next_task)

        # 3. Execução do tick nas CPUs
        tcb_map = {tcb.id: tcb for tcb in self.tcbs}
        for cpu in self.cpus:
            cpu.tick()
            if cpu.current_task_id and cpu.current_task_id in tcb_map:
                running_task = tcb_map[cpu.current_task_id]
                running_task.duracao_restante -= 1

                # Verifica conclusão da tarefa
                if running_task.duracao_restante <= 0:
                    running_task.estado = "CONCLUIDA"
                    running_task.execucoes_concluidas += 1
                    running_task.duracao_restante = running_task.duracao_total
                    running_task.proximo_release += running_task.periodo
                    running_task.prazo_absoluto = running_task.proximo_release + running_task.prazo_relativo
                    cpu.release_task(running_task)

        self.current_tick += 1
        self.save_snapshot()
        return self.get_current_state()

    def step_back(self) -> Dict[str, Any]:
        """Retrocede 1 tick na simulação utilizando o histórico."""
        if len(self.history) > 1:
            self.history.pop()  # Descarta o snapshot do tick atual
            previous_snapshot = self.history[-1]
            self.restore_snapshot(previous_snapshot)
        return self.get_current_state()

    def get_current_state(self) -> Dict[str, Any]:
        """Empacota o estado corrente para renderização nas páginas do PySide6."""
        return {
            "tick": self.current_tick,
            "cpus": self.cpus,
            "tcbs": self.tcbs,
            "ready_queue": self.ready_queue,
            "algorithm": self.raw_config.get("algorithm", "RM"),
            "quantum": self.raw_config.get("quantum", 1)
        }