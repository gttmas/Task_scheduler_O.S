from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QPushButton
)
from PySide6.QtCore import Signal  # <-- IMPORTAR Signal
from PySide6.QtGui import QColor
from core import TaskControlBlock


class TasksPage(QWidget):
    """Página de Gerenciamento e Exibição de TCBs."""

    # NOVO SINAL: Emite (ID da Tarefa, Novo Estado)
    manual_state_change = Signal(str, str)

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

        # Botão Modificar Estado
        self.btn_apply = QPushButton("✏️ Modificar Estado")
        self.btn_apply.setStyleSheet("background-color: #007ACC; color: white; font-weight: bold;")
        
        # CONEXÃO DO BOTÃO
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        
        debug_layout.addWidget(self.btn_apply)
        debug_layout.addStretch(1)
        layout.addWidget(debug_box)

    def on_apply_clicked(self):
        """Captura os valores do painel e emite o sinal para o Motor."""
        task_id = self.combo_select_task.currentText()
        new_state = self.combo_new_state.currentText()
        if task_id and new_state:
            self.manual_state_change.emit(task_id, new_state)

    def render_state(self, state: Dict[str, Any]):
        """Atualiza a TCB lendo as instâncias de TaskControlBlock."""
        tcbs: List[TaskControlBlock] = state.get("tcbs", [])

        self.table_tcb.setRowCount(len(tcbs))
        
        # Salva o texto atual para não perder a seleção do usuário a cada tick
        current_selection = self.combo_select_task.currentText()
        self.combo_select_task.blockSignals(True)
        self.combo_select_task.clear()

        for row, tcb in enumerate(tcbs):
            self.combo_select_task.addItem(tcb.id)

            self.table_tcb.setItem(row, 0, QTableWidgetItem(tcb.id))

            item_status = QTableWidgetItem(tcb.estado)
            status_colors = {
                "PRONTA": "#F1C40F", "EXECUTANDO": "#2ECC71",
                "SUSPENSA": "#E67E22", "CONCLUIDA": "#95A5A6", "CANCELADA": "#E74C3C"
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

        # Restaura a seleção anterior se ela ainda existir na lista
        index = self.combo_select_task.findText(current_selection)
        if index >= 0:
            self.combo_select_task.setCurrentIndex(index)
        self.combo_select_task.blockSignals(False)