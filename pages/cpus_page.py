from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QScrollArea, QGridLayout, QFrame
)
from core import CPU


class CPUsPage(QWidget):
    """Página de Monitoramento das CPUs e Ociosidade."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        summary_box = QGroupBox("Métricas Globais dos Processadores")
        summary_layout = QHBoxLayout(summary_box)

        self.lbl_active_cpus = QLabel("CPUs Executando: 0 / 0")
        self.lbl_global_idle = QLabel("Tempo Total Ocioso/Desligado: 0 ticks")
        self.lbl_global_idle.setStyleSheet("color: #D35400; font-weight: bold;")

        summary_layout.addWidget(self.lbl_active_cpus)
        summary_layout.addWidget(self.lbl_global_idle)
        summary_layout.addStretch(1)

        layout.addWidget(summary_box)

        cpus_box = QGroupBox("Estado dos Processadores (Cores)")
        cpus_box_layout = QVBoxLayout(cpus_box)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.grid_cpus = QGridLayout(scroll_widget)
        self.grid_cpus.setSpacing(15)

        scroll.setWidget(scroll_widget)
        cpus_box_layout.addWidget(scroll)
        layout.addWidget(cpus_box, 1)

        queue_box = QGroupBox("Fila Global de Prontos (Aguardando Escalonamento)")
        queue_layout = QHBoxLayout(queue_box)
        self.lbl_ready_queue = QLabel("Fila de Prontos: [ Vazia ]")
        self.lbl_ready_queue.setStyleSheet("font-family: monospace; font-size: 13px; color: #27AE60;")
        queue_layout.addWidget(self.lbl_ready_queue)

        layout.addWidget(queue_box)

    def render_state(self, state: Dict[str, Any]):
        """Renderiza as CPUs e a Fila de Prontos com base no snapshot do motor."""
        cpus_list: List[CPU] = state.get("cpus", [])
        ready_queue = state.get("ready_queue", [])

        while self.grid_cpus.count():
            item = self.grid_cpus.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        total_cpus = len(cpus_list)
        active_cpus = sum(1 for c in cpus_list if c.status == CPU.STATUS_EXECUTANDO)
        total_idle = sum(c.idle_ticks for c in cpus_list)

        self.lbl_active_cpus.setText(f"CPUs Executando: {active_cpus} / {total_cpus}")
        self.lbl_global_idle.setText(f"Tempo Total Ocioso/Desligado: {total_idle} ticks")

        cols = 3 if total_cpus >= 3 else total_cpus
        for i, cpu in enumerate(cpus_list):
            card = self.create_cpu_card(cpu)
            self.grid_cpus.addWidget(card, i // cols, i % cols)

        if ready_queue:
            task_ids = [tcb.id for tcb in ready_queue]
            self.lbl_ready_queue.setText(f"Fila de Prontos ({len(task_ids)}): [ {', '.join(task_ids)} ]")
        else:
            self.lbl_ready_queue.setText("Fila de Prontos (0): [ Vazia ]")

    def create_cpu_card(self, cpu: CPU) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)

        status_colors = {
            CPU.STATUS_EXECUTANDO: "#2ECC71",
            CPU.STATUS_OCIOSA:     "#F1C40F",
            CPU.STATUS_DESLIGADA:  "#E74C3C"
        }
        status_color = status_colors.get(cpu.status, "#FFFFFF")

        card.setStyleSheet("""
            QFrame {
                background-color: #2D2D30; border: 1px solid #3F3F46; border-radius: 6px; padding: 10px;
            }
        """)
        card_layout = QVBoxLayout(card)

        lbl_header = QLabel(f"<b>PROCESSADOR CPU #{cpu.cpu_id:02d}</b>")
        lbl_header.setStyleSheet("color: #007ACC; font-size: 14px;")

        lbl_status = QLabel(f"Status: <b style='color: {status_color};'>{cpu.status}</b>")
        task_id = cpu.current_task_id if cpu.current_task_id else "Nenhuma"

        lbl_task = QLabel(f"Tarefa Atual: <b>{task_id}</b>")
        lbl_idle = QLabel(f"Tempo Ocioso/Desligado: <b>{cpu.idle_ticks}</b> ticks")

        card_layout.addWidget(lbl_header)
        card_layout.addWidget(lbl_status)
        card_layout.addWidget(lbl_task)
        card_layout.addWidget(lbl_idle)

        return card