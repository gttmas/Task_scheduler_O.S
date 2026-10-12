from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QPushButton
)
from PySide6.QtGui import QColor
from core import TaskControlBlock


class TasksPage(QWidget):
    """Página de Gerenciamento e Exibição de TCBs[cite: 1]."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        tcb_box = QGroupBox("Blocos de Controle de Tarefa (TCB)")
        tcb_layout = QVBoxLayout(tcb_box)

        self.table_tcb = QTableWidget()
        self.table_tcb.setColumnCount(9)
        self.table_tcb.setHorizontalHeaderLabels([
            "ID", "Estado Atual", "CPU", "Ingresso", "Duração Restante",
            "Período", "Próximo Release", "Prazo Absoluto", "Execuções"
        ])
        self.table_tcb.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tcb_layout.addWidget(self.table_tcb)

        layout.addWidget(tcb_box, 1)

        debug_box = QGroupBox("Painel de Modificação Manual (Debugger)")
        debug_layout = QHBoxLayout(debug_box)

        debug_layout.addWidget(QLabel("Selecionar Tarefa:"))
        self.combo_select_task = QComboBox()
        debug_layout.addWidget(self.combo_select_task)

        debug_layout.addWidget(QLabel("Novo Estado:"))
        self.combo_new_state = QComboBox()
        self.combo_new_state.addItems(["PRONTA", "SUSPENSA", "CANCELADA"])
        debug_layout.addWidget(self.combo_new_state)

        btn_apply = QPushButton("✏️ Modificar Estado")
        btn_apply.setStyleSheet("background-color: #007ACC; color: white; font-weight: bold;")
        debug_layout.addWidget(btn_apply)

        debug_layout.addStretch(1)
        layout.addWidget(debug_box)

    def render_state(self, state: Dict[str, Any]):
        """Atualiza a TCB lendo as instâncias de TaskControlBlock[cite: 1]."""
        tcbs: List[TaskControlBlock] = state.get("tcbs", [])

        self.table_tcb.setRowCount(len(tcbs))
        self.combo_select_task.clear()

        for row, tcb in enumerate(tcbs):
            self.combo_select_task.addItem(tcb.id)

            self.table_tcb.setItem(row, 0, QTableWidgetItem(tcb.id))

            item_status = QTableWidgetItem(tcb.estado)
            status_colors = {
                "PRONTA": "#F1C40F", "EXECUTANDO": "#2ECC71",
                "SUSPENSA": "#E67E22", "CONCLUIDA": "#95A5A6"
            }
            item_status.setForeground(QColor(status_colors.get(tcb.estado, "#FFFFFF")))
            self.table_tcb.setItem(row, 1, item_status)

            cpu_text = f"CPU #{tcb.cpu_alocada:02d}" if tcb.cpu_alocada else "-"
            self.table_tcb.setItem(row, 2, QTableWidgetItem(cpu_text))
            self.table_tcb.setItem(row, 3, QTableWidgetItem(str(tcb.ingresso)))
            self.table_tcb.setItem(row, 4, QTableWidgetItem(f"{tcb.duracao_restante} / {tcb.duracao_total}"))
            self.table_tcb.setItem(row, 5, QTableWidgetItem(str(tcb.periodo)))
            self.table_tcb.setItem(row, 6, QTableWidgetItem(str(tcb.proximo_release)))
            self.table_tcb.setItem(row, 7, QTableWidgetItem(str(tcb.prazo_absoluto)))
            self.table_tcb.setItem(row, 8, QTableWidgetItem(f"{tcb.execucoes_concluidas} / {tcb.limite_execucoes}"))