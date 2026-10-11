from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QPushButton
)
from PySide6.QtGui import QColor


class TasksPage(QWidget):
    """Página do Gerenciador de Tarefas, TCB (Task Control Block) e Debugger."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        tcb_box = QGroupBox("Blocos de Controle de Tarefa (TCB - Task Control Block)")
        tcb_layout = QVBoxLayout(tcb_box)

        self.table_tcb = QTableWidget()
        self.table_tcb.setColumnCount(9)
        self.table_tcb.setHorizontalHeaderLabels([
            "ID", "Estado Atual", "CPU", "Ingresso", "Duração Restante",
            "Período", "Próximo Release", "Prazo (Deadline)", "Execuções"
        ])
        self.table_tcb.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tcb_layout.addWidget(self.table_tcb)

        layout.addWidget(tcb_box, 1)

        debug_box = QGroupBox("Painel de Controle e Modificação Manual (Debugger Passo a Passo)")
        debug_layout = QHBoxLayout(debug_box)

        debug_layout.addWidget(QLabel("Selecionar Tarefa:"))
        self.combo_select_task = QComboBox()
        debug_layout.addWidget(self.combo_select_task)

        debug_layout.addWidget(QLabel("Novo Estado:"))
        self.combo_new_state = QComboBox()
        self.combo_new_state.addItems(["PRONTA", "SUSPENSA", "CANCELADA"])
        debug_layout.addWidget(self.combo_new_state)

        btn_apply_state = QPushButton("✏️ Modificar Estado no Tick Atual")
        btn_apply_state.setStyleSheet("background-color: #007ACC; color: white; font-weight: bold;")
        debug_layout.addWidget(btn_apply_state)

        debug_layout.addStretch(1)
        layout.addWidget(debug_box)

    def update_config(self, config: dict):
        """Sincroniza a tabela de TCB com todas as tarefas carregadas."""
        tasks = config.get("tasks", [])

        self.table_tcb.setRowCount(len(tasks))
        self.combo_select_task.clear()

        for row, task in enumerate(tasks):
            t_id = str(task["id"])
            self.combo_select_task.addItem(t_id)

            # Coluna 0: ID
            self.table_tcb.setItem(row, 0, QTableWidgetItem(t_id))

            # Coluna 1: Estado Inicial (PRONTA)
            item_status = QTableWidgetItem("PRONTA")
            item_status.setForeground(QColor("#F1C40F"))
            self.table_tcb.setItem(row, 1, item_status)

            # Coluna 2: CPU Alocada
            self.table_tcb.setItem(row, 2, QTableWidgetItem("-"))

            # Coluna 3: Ingresso
            self.table_tcb.setItem(row, 3, QTableWidgetItem(str(task["ingresso"])))

            # Coluna 4: Duração Restante
            self.table_tcb.setItem(row, 4, QTableWidgetItem(f"{task['duracao']} / {task['duracao']}"))

            # Coluna 5: Período
            self.table_tcb.setItem(row, 5, QTableWidgetItem(str(task["periodo"])))

            # Coluna 6: Próximo Release
            self.table_tcb.setItem(row, 6, QTableWidgetItem(str(task["ingresso"])))

            # Coluna 7: Prazo (Deadline)
            self.table_tcb.setItem(row, 7, QTableWidgetItem(str(task["prazo"])))

            # Coluna 8: Execuções Concluídas (até 10 max)
            self.table_tcb.setItem(row, 8, QTableWidgetItem("0 / 10"))