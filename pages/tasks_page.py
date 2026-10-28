from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
    QPushButton, QLineEdit, QSpinBox
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from core.tcb import TaskControlBlock


class TasksPage(QWidget):
    """Página de Gerenciamento, Exibição, Injeção e Edição de Tarefas (Requisito 3.1)."""

    manual_state_change = Signal(str, str)        # (task_id, new_state)
    add_task_requested = Signal(dict)             # (task_data_dict)
    task_properties_changed = Signal(str, dict)   # (task_id, new_params_dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dynamic_task_count = 1
        self.current_tcbs: List[TaskControlBlock] = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # --- 1. TABELA DE TCBs ---
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

        # --- 2. INJETAR NOVA TAREFA EM TEMPO DE EXECUÇÃO ---
        add_box = QGroupBox("➕ Injetar Nova Tarefa em Tempo de Execução")
        add_layout = QHBoxLayout(add_box)

        add_layout.addWidget(QLabel("ID:"))
        self.txt_id = QLineEdit("TD1")
        self.txt_id.setFixedWidth(50)
        add_layout.addWidget(self.txt_id)

        add_layout.addWidget(QLabel("Duração:"))
        self.spin_duracao = QSpinBox()
        self.spin_duracao.setRange(1, 100)
        self.spin_duracao.setValue(2)
        add_layout.addWidget(self.spin_duracao)

        add_layout.addWidget(QLabel("Período:"))
        self.spin_periodo = QSpinBox()
        self.spin_periodo.setRange(1, 200)
        self.spin_periodo.setValue(10)
        add_layout.addWidget(self.spin_periodo)

        add_layout.addWidget(QLabel("Prazo:"))
        self.spin_prazo = QSpinBox()
        self.spin_prazo.setRange(1, 200)
        self.spin_prazo.setValue(4)
        add_layout.addWidget(self.spin_prazo)

        add_layout.addWidget(QLabel("Cor (Hex):"))
        self.txt_color = QLineEdit("E74C3C")
        self.txt_color.setFixedWidth(65)
        add_layout.addWidget(self.txt_color)

        btn_add = QPushButton("🚀 Injetar Tarefa")
        btn_add.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; padding: 5px 10px;")
        btn_add.clicked.connect(self.on_add_task_clicked)
        add_layout.addWidget(btn_add)
        layout.addWidget(add_box)

        # --- 3. ALTERAR CARACTERÍSTICAS DA TAREFA (REQUISITO 3.1 - ID FIXO) ---
        edit_box = QGroupBox("✏️ Alterar Características da Tarefa (Requisito 3.1)")
        edit_layout = QHBoxLayout(edit_box)

        edit_layout.addWidget(QLabel("Selecionar Tarefa:"))
        self.combo_edit_task = QComboBox()
        self.combo_edit_task.currentIndexChanged.connect(self.on_edit_task_selected)
        edit_layout.addWidget(self.combo_edit_task)

        edit_layout.addWidget(QLabel("Duração:"))
        self.spin_edit_duracao = QSpinBox()
        self.spin_edit_duracao.setRange(1, 200)
        edit_layout.addWidget(self.spin_edit_duracao)

        edit_layout.addWidget(QLabel("Período:"))
        self.spin_edit_periodo = QSpinBox()
        self.spin_edit_periodo.setRange(-10, 200)
        edit_layout.addWidget(self.spin_edit_periodo)

        edit_layout.addWidget(QLabel("Prazo:"))
        self.spin_edit_prazo = QSpinBox()
        self.spin_edit_prazo.setRange(1, 200)
        edit_layout.addWidget(self.spin_edit_prazo)

        edit_layout.addWidget(QLabel("Cor (Hex):"))
        self.txt_edit_color = QLineEdit()
        self.txt_edit_color.setFixedWidth(65)
        edit_layout.addWidget(self.txt_edit_color)

        btn_save_edit = QPushButton("💾 Salvar Alterações")
        btn_save_edit.setStyleSheet("background-color: #D35400; color: white; font-weight: bold; padding: 5px 10px;")
        btn_save_edit.clicked.connect(self.on_save_edit_clicked)
        edit_layout.addWidget(btn_save_edit)
        layout.addWidget(edit_box)

        # --- 4. DEBUGGER MANUAL DE ESTADO ---
        debug_box = QGroupBox("Painel de Modificação Manual de Estado (Debugger)")
        debug_layout = QHBoxLayout(debug_box)

        debug_layout.addWidget(QLabel("Selecionar Tarefa:"))
        self.combo_select_task = QComboBox()
        debug_layout.addWidget(self.combo_select_task)

        debug_layout.addWidget(QLabel("Novo Estado:"))
        self.combo_new_state = QComboBox()
        self.combo_new_state.addItems(["PRONTA", "SUSPENSA", "CANCELADA"])
        debug_layout.addWidget(self.combo_new_state)

        self.btn_apply = QPushButton("✏️ Modificar Estado")
        self.btn_apply.setStyleSheet("background-color: #007ACC; color: white; font-weight: bold;")
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        debug_layout.addWidget(self.btn_apply)
        debug_layout.addStretch(1)
        layout.addWidget(debug_box)

    def on_add_task_clicked(self):
        """Coleta dados do formulário e injeta nova tarefa."""
        task_data = {
            "id": self.txt_id.text().strip() or f"TD{self.dynamic_task_count}",
            "color": self.txt_color.text().strip() or "E74C3C",
            "duracao": self.spin_duracao.value(),
            "periodo": self.spin_periodo.value(),
            "prazo": self.spin_prazo.value(),
            "eventos": "-"
        }
        self.dynamic_task_count += 1
        self.txt_id.setText(f"TD{self.dynamic_task_count}")
        self.add_task_requested.emit(task_data)

    def on_edit_task_selected(self):
        """Preenche os campos de edição com os valores atuais da tarefa selecionada."""
        selected_id = self.combo_edit_task.currentText()
        tcb = next((t for t in self.current_tcbs if t.id == selected_id), None)
        if tcb:
            self.txt_edit_color.setText(tcb.color)
            self.spin_edit_duracao.setValue(tcb.duracao_total)
            self.spin_edit_periodo.setValue(tcb.periodo)
            self.spin_edit_prazo.setValue(tcb.prazo_relativo)

    def on_save_edit_clicked(self):
        """Emite sinal para atualizar Duração, Período, Prazo e Cor mantendo o ID fixo."""
        task_id = self.combo_edit_task.currentText()
        if not task_id:
            return

        new_params = {
            "color": self.txt_edit_color.text().strip(),
            "duracao": self.spin_edit_duracao.value(),
            "periodo": self.spin_edit_periodo.value(),
            "prazo": self.spin_edit_prazo.value()
        }
        self.task_properties_changed.emit(task_id, new_params)

    def on_apply_clicked(self):
        """Emite sinal para alteração de estado manual."""
        task_id = self.combo_select_task.currentText()
        new_state = self.combo_new_state.currentText()
        if task_id and new_state:
            self.manual_state_change.emit(task_id, new_state)

    def render_state(self, state: Dict[str, Any]):
        """Renderiza TCBs e atualiza as caixas de seleção."""
        tcbs: List[TaskControlBlock] = state.get("tcbs", [])
        self.current_tcbs = tcbs
        self.table_tcb.setRowCount(len(tcbs))

        current_state_selection = self.combo_select_task.currentText()
        current_edit_selection = self.combo_edit_task.currentText()

        self.combo_select_task.blockSignals(True)
        self.combo_edit_task.blockSignals(True)

        self.combo_select_task.clear()
        self.combo_edit_task.clear()

        for row, tcb in enumerate(tcbs):
            self.combo_select_task.addItem(tcb.id)
            self.combo_edit_task.addItem(tcb.id)

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

        idx_state = self.combo_select_task.findText(current_state_selection)
        if idx_state >= 0:
            self.combo_select_task.setCurrentIndex(idx_state)
        self.combo_select_task.blockSignals(False)

        idx_edit = self.combo_edit_task.findText(current_edit_selection)
        if idx_edit >= 0:
            self.combo_edit_task.setCurrentIndex(idx_edit)
        elif self.combo_edit_task.count() > 0:
            self.combo_edit_task.setCurrentIndex(0)

        self.combo_edit_task.blockSignals(False)
        self.on_edit_task_selected()