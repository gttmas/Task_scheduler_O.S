from typing import List, Dict, Any
from core.tcb import TaskControlBlock
from core.cpu import CPU
from schedulers import run_scheduler
import re


def is_valid_hex_color(color_str: str) -> bool:
    """Verifica se a string é um código hexadecimal de cor válido (ex: FF5733 ou #FF5733)."""
    if not color_str or not isinstance(color_str, str):
        return False
    clean = color_str.lstrip('#').strip()
    return bool(re.fullmatch(r'^[0-9a-fA-F]{6}$', clean) or re.fullmatch(r'^[0-9a-fA-F]{3}$', clean))


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
        self.raw_config = config_data
        self.reset()

    def set_cpu_count(self, new_count: int):
        current_count = len(self.cpus)
        if new_count == current_count or new_count < 1:
            return

        if new_count > current_count:
            for i in range(current_count + 1, new_count + 1):
                self.cpus.append(CPU(i))
        else:
            for cpu in self.cpus[new_count:]:
                if cpu.current_task_id:
                    tcb = next((t for t in self.tcbs if t.id == cpu.current_task_id), None)
                    if tcb and tcb not in self.ready_queue:
                        tcb.estado = "PRONTA"
                        tcb.cpu_alocada = None
                        self.ready_queue.append(tcb)
            self.cpus = self.cpus[:new_count]

        self.raw_config["cpus"] = new_count
        if self.history:
            self.history[-1] = self.create_snapshot()

    def reset(self):
        self.current_tick = 0
        self.history.clear()

        num_cpus = self.raw_config.get("cpus", 1)
        self.cpus = [CPU(i + 1) for i in range(num_cpus)]

        raw_tasks = self.raw_config.get("tasks", [])
        self.tcbs = [TaskControlBlock(t) for t in raw_tasks if isinstance(t, dict)]

        self.ready_queue = []
        self._check_releases_and_allocate()
        self.save_snapshot()

    def add_task_dynamically(self, task_data: dict) -> tuple[bool, str, TaskControlBlock | None]:
        """Injeta uma nova tarefa no sistema com validações completas."""
        try:
            duracao = int(task_data.get("duracao", 0))
            periodo = int(task_data.get("periodo", 0))
            prazo = int(task_data.get("prazo", 0))
        except (ValueError, TypeError):
            return False, "Erro: Duração, Período e Prazo devem ser números inteiros.", None

        color = str(task_data.get("color", "")).strip()
        if not is_valid_hex_color(color):
            return False, f"Erro: A cor '{color}' é inválida.", None

        if periodo <= 0:
            return False, f"Erro: O período ({periodo}) deve ser > 0. Tarefas aperiódicas não são permitidas no Projeto A.", None

        if duracao <= 0:
            return False, f"Erro: A duração ({duracao}) deve ser > 0.", None

        if prazo <= 0:
            return False, f"Erro: O prazo ({prazo}) deve ser > 0.", None

        if "ingresso" not in task_data or int(task_data.get("ingresso", 0)) < self.current_tick:
            task_data["ingresso"] = self.current_tick

        new_tcb = TaskControlBlock(task_data)
        new_tcb.proximo_release = new_tcb.ingresso
        new_tcb.prazo_absoluto = new_tcb.proximo_release + new_tcb.prazo_relativo

        existing_ids = {t.id for t in self.tcbs}
        if new_tcb.id in existing_ids:
            count = 1
            while f"{new_tcb.id}_{count}" in existing_ids:
                count += 1
            new_tcb.id = f"{new_tcb.id}_{count}"

        self.tcbs.append(new_tcb)
        self._check_releases_and_allocate()
        self.save_snapshot()
        return True, f"Sucesso: Tarefa '{new_tcb.id}' injetada no Tick {self.current_tick}.", new_tcb

    def update_task_properties_manually(self, task_id: str, new_params: dict) -> tuple[bool, str]:
        """Concentra TODAS as validações de alteração em tempo de execução (Requisito 3.1)."""
        tcb = next((t for t in self.tcbs if t.id == task_id), None)
        if not tcb:
            return False, f"Tarefa '{task_id}' não foi encontrada no sistema."

        if tcb.estado == "CANCELADA":
            return False, f"Alteração Rejeitada: A tarefa '{task_id}' está CANCELADA e não pode ser modificada."

        new_color = str(new_params.get("color", "")).strip()
        if not is_valid_hex_color(new_color):
            return False, f"Alteração Rejeitada: A cor '{new_color}' é inválida. Informe um código Hexadecimal de 6 dígitos (ex: FF5733)."

        try:
            new_duracao = int(new_params.get("duracao", tcb.duracao_total))
            new_periodo = int(new_params.get("periodo", tcb.periodo))
            new_prazo = int(new_params.get("prazo", tcb.prazo_relativo))
        except (ValueError, TypeError):
            return False, "Erro de Validação: Duração, Período e Prazo devem ser números inteiros válidos."

        if new_periodo <= 0:
            return False, f"Alteração Rejeitada: O período ({new_periodo}) deve ser > 0. Tarefas aperiódicas ou esporádicas só são permitidas no Projeto B."

        if new_duracao <= 0:
            return False, f"Alteração Rejeitada: A duração ({new_duracao}) deve ser um valor positivo maior que zero."

        if new_prazo <= 0:
            return False, f"Alteração Rejeitada: O prazo relativo ({new_prazo}) deve ser um valor positivo maior que zero."

        tcb.color = new_color.lstrip('#').upper()
        tcb.periodo = new_periodo
        tcb.prazo_relativo = new_prazo

        executado = max(0, tcb.duracao_total - tcb.duracao_restante)
        tcb.duracao_total = new_duracao
        tcb.duracao_restante = max(1, new_duracao - executado)
        tcb.prazo_absoluto = tcb.proximo_release + tcb.prazo_relativo

        self._check_releases_and_allocate()
        self.save_snapshot()

        return True, f"Sucesso: Características da tarefa '{task_id}' atualizadas no Tick {self.current_tick}."

    def modify_task_state_manually(self, task_id: str, new_state: str):
        tcb = next((t for t in self.tcbs if t.id == task_id), None)
        if not tcb or tcb.estado == new_state:
            return

        old_state = tcb.estado
        if old_state == "CANCELADA":
            return

        tcb.estado = new_state

        if old_state == "EXECUTANDO" and new_state in ["SUSPENSA", "CANCELADA"]:
            for cpu in self.cpus:
                if cpu.current_task_id == tcb.id:
                    cpu.release_task(tcb)
                    break

        if new_state == "PRONTA":
            if tcb.proximo_release < self.current_tick:
                while tcb.proximo_release < self.current_tick:
                    tcb.proximo_release += tcb.periodo
                tcb.prazo_absoluto = tcb.proximo_release + tcb.prazo_relativo

            if tcb not in self.ready_queue:
                self.ready_queue.append(tcb)
        else:
            if tcb in self.ready_queue:
                self.ready_queue.remove(tcb)

        self.save_snapshot()

    def _check_releases_and_allocate(self):
        selected_algorithm = self.raw_config.get("algorithm", "EDF")
        run_scheduler(
            tcbs=self.tcbs,
            cpus=self.cpus,
            ready_queue=self.ready_queue,
            current_tick=self.current_tick,
            algorithm=selected_algorithm
        )

    def save_snapshot(self):
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
        system_quantum = self.raw_config.get("quantum", 1)
        tcb_map = {tcb.id: tcb for tcb in self.tcbs}
        
        for cpu in self.cpus:
            cpu.tick()
            if cpu.current_task_id and cpu.current_task_id in tcb_map:
                running_task = tcb_map[cpu.current_task_id]
                running_task.duracao_restante -= 1
                cpu.quantum_counter += 1

                if running_task.duracao_restante <= 0:
                    running_task.estado = "CONCLUIDA"
                    running_task.execucoes_concluidas += 1
                    running_task.duracao_restante = running_task.duracao_total
                    running_task.proximo_release += running_task.periodo
                    running_task.prazo_absoluto = running_task.proximo_release + running_task.prazo_relativo
                    cpu.release_task(running_task)

        self.current_tick += 1
        self._check_releases_and_allocate()
        self.save_snapshot()
        return self.get_current_state()

    def step_back(self) -> Dict[str, Any]:
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
            "quantum": self.raw_config.get("quantum", 1),
            "history": self.history
        }

    @property
    def is_finished(self) -> bool:
        if not self.tcbs:
            return False
        return all(tcb.execucoes_concluidas >= tcb.limite_execucoes for tcb in self.tcbs)

    def run_full_simulation(self) -> dict:
        LIMITE_SEGURANCA = 10000
        while not self.is_finished and self.current_tick < LIMITE_SEGURANCA:
            self.step_forward()
        return self.get_current_state()