class TaskControlBlock:
    """Bloco de Controle de Tarefas (TCB) para a simulação."""
    def __init__(self, task_data: dict):
        # Parâmetros Fixos da Tarefa
        self.id = str(task_data["id"])
        self.color = str(task_data.get("color", "FF5733"))
        self.ingresso = int(task_data["ingresso"])
        self.duracao_total = int(task_data["duracao"])
        self.periodo = int(task_data["periodo"])
        self.prazo_relativo = int(task_data["prazo"])
        self.eventos = str(task_data.get("eventos", "-"))
        
        # Variáveis de Estado Dinâmico
        # Define como PRONTA apenas se ingressar no tick 0; caso contrário, é NÃO INICIADA
        self.estado = "PRONTA" if self.ingresso == 0 else "NÃO INICIADA"
        self.cpu_alocada = None
        
        # Controle de Execução e Prazos
        self.duracao_restante = self.duracao_total
        self.proximo_release = self.ingresso
        self.prazo_absoluto = self.ingresso + self.prazo_relativo
        
        # Histórico e Limite
        self.execucoes_concluidas = 0
        self.limite_execucoes = 10

    def clone(self):
        """Cria uma cópia isolada da TCB para registrar o snapshot do tick atual."""
        new_tcb = TaskControlBlock.__new__(TaskControlBlock)
        new_tcb.__dict__ = self.__dict__.copy()
        return new_tcb