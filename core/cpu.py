from typing import Optional


class CPU:
    """representa uma cpu"""
    #estados da cpu
    STATUS_EXECUTANDO = "EXECUTANDO"
    STATUS_DESLIGADA = "DESLIGADA"
    #inicialização base das cpus
    def __init__(self, cpu_id: int):
        self.cpu_id: int = cpu_id
        self.current_task_id: Optional[str] = None
        self.status: str = CPU.STATUS_DESLIGADA
        self.idle_ticks: int = 0
        self.active_ticks: int = 0
        self.quantum_counter = 0
    
    def assign_task(self, task) -> None:
        """aloca uma tarefa para executar nesta CPU"""
        self.current_task_id = task.id
        self.status = CPU.STATUS_EXECUTANDO
        self.quantum_counter = 0
        task.estado = "EXECUTANDO"
        task.cpu_alocada = self.cpu_id

    def release_task(self, task=None) -> None:
        """desaloca a tarefa atual e define a CPU como DESLIGADA."""
        #ve se tem task e se o atributo dela está correto, e então libera
        if task and hasattr(task, 'cpu_alocada'):
            task.cpu_alocada = None
        self.current_task_id = None
        self.quantum_counter = 0
        self.status = CPU.STATUS_DESLIGADA


    def tick(self) -> None:
        """contabiliza a atividade ou ociosidade no tick atual"""
        if self.status == CPU.STATUS_EXECUTANDO and self.current_task_id:
            self.active_ticks += 1
        else:
            self.idle_ticks += 1

    def clone(self):
        """cria uma cópia isolada do estado da CPU para o histórico."""
        new_cpu = CPU.__new__(CPU)
        new_cpu.__dict__ = self.__dict__.copy()
        return new_cpu