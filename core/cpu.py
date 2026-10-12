from typing import Optional


class CPU:
    """Representa uma unidade de processamento (Core)."""
    STATUS_EXECUTANDO = "EXECUTANDO"
    STATUS_OCIOSA = "OCIOSA"
    STATUS_DESLIGADA = "DESLIGADA"

    def __init__(self, cpu_id: int):
        self.cpu_id: int = cpu_id
        self.current_task_id: Optional[str] = None
        self.status: str = CPU.STATUS_OCIOSA
        self.idle_ticks: int = 0
        self.active_ticks: int = 0

    def assign_task(self, task) -> None:
        """Aloca uma TCB para executar nesta CPU."""
        self.current_task_id = task.id
        self.status = CPU.STATUS_EXECUTANDO
        task.estado = "EXECUTANDO"
        task.cpu_alocada = self.cpu_id

    def release_task(self, task=None) -> None:
        """Desaloca a tarefa atual e define a CPU como OCIOSA."""
        if task and hasattr(task, 'cpu_alocada'):
            task.cpu_alocada = None
        self.current_task_id = None
        self.status = CPU.STATUS_OCIOSA

    def turn_off(self) -> None:
        self.release_task()
        self.status = CPU.STATUS_DESLIGADA

    def tick(self) -> None:
        """Contabiliza a atividade ou ociosidade no tick corrente."""
        if self.status == CPU.STATUS_EXECUTANDO and self.current_task_id:
            self.active_ticks += 1
        else:
            self.idle_ticks += 1

    def clone(self):
        """Cria uma cópia isolada do estado da CPU para o histórico."""
        new_cpu = CPU.__new__(CPU)
        new_cpu.__dict__ = self.__dict__.copy()
        return new_cpu