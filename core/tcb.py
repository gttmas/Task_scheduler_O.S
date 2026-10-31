class TaskControlBlock:
    """bloco de controle de tarefas para a simulação"""
    def __init__(self, task_data: dict):
        # parâmetros fixos da tarefa
        self.id = str(task_data["id"])
        self.color = str(task_data.get("color", "FF5733"))
        self.ingresso = int(task_data["ingresso"])
        self.duracao_total = int(task_data["duracao"])
        self.periodo = int(task_data["periodo"])
        self.prazo_relativo = int(task_data["prazo"])
        self.eventos = str(task_data.get("eventos", "-"))
        
        # variáveis de estado dinâmico
        # define como PRONTA apenas se ingressar no tick 0, se não é NÃO INICIADA
        self.estado = "PRONTA" if self.ingresso == 0 else "NÃO INICIADA"
        self.cpu_alocada = None
        
        # controle de execução e prazos
        self.duracao_restante = self.duracao_total
        self.proximo_release = self.ingresso
        self.prazo_absoluto = self.ingresso + self.prazo_relativo
        
        # histórico e limite
        self.execucoes_concluidas = 0
        self.limite_execucoes = 10

    def clone(self):
        """cria uma cópia isolada da TCB para registrar o tick atual"""
        new_tcb = TaskControlBlock.__new__(TaskControlBlock)
        new_tcb.__dict__ = self.__dict__.copy()
        return new_tcb