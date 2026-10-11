from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QScrollArea, QGridLayout, QFrame
)


class CPUsPage(QWidget):
    """Página de Monitoramento dos Processadores (CPUs) e Ociosidade."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        summary_box = QGroupBox("Métricas Globais dos Processadores")
        summary_layout = QHBoxLayout(summary_box)

        self.lbl_active_cpus = QLabel("CPUs Ativas: 0 / 0")
        self.lbl_global_idle = QLabel("Tempo Total de Ociosidade: 0 ticks")
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

    def update_config(self, config: dict):
        """Sincroniza o número de cartões de CPU e a fila inicial com base na configuração."""
        cpus_count = config.get("cpus", 1)
        tasks = config.get("tasks", [])

        # 1. Limpar grid anterior de CPUs
        while self.grid_cpus.count():
            item = self.grid_cpus.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 2. Atualizar cabeçalho de status
        self.lbl_active_cpus.setText(f"CPUs Ativas: {cpus_count} / {cpus_count}")

        # 3. Recriar cartões para o número exato de CPUs
        cols = 3 if cpus_count >= 3 else cpus_count
        for i in range(cpus_count):
            card = self.create_cpu_card(cpu_id=i + 1, task_name="Ociosa", status="OCIOSA / AGUARDANDO", idle_time=0)
            self.grid_cpus.addWidget(card, i // cols, i % cols)

        # 4. Atualizar a Fila de Prontos inicial
        task_ids = [t["id"] for t in tasks]
        if task_ids:
            self.lbl_ready_queue.setText(f"Fila de Prontos: [ {', '.join(task_ids)} ]")
        else:
            self.lbl_ready_queue.setText("Fila de Prontos: [ Vazia ]")

    def create_cpu_card(self, cpu_id: int, task_name: str, status: str, idle_time: int) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: #2D2D30; border: 1px solid #3F3F46; border-radius: 6px; padding: 10px;
            }
        """)
        card_layout = QVBoxLayout(card)

        lbl_header = QLabel(f"<b>PROCESSADOR CPU #{cpu_id:02d}</b>")
        lbl_header.setStyleSheet("color: #007ACC; font-size: 14px;")

        lbl_status = QLabel(f"Status: <b style='color: #F1C40F;'>{status}</b>")
        lbl_task = QLabel(f"Tarefa Atual: <b>{task_name}</b>")
        lbl_idle = QLabel(f"Tempo Ocioso/Desligado: {idle_time} ticks")

        card_layout.addWidget(lbl_header)
        card_layout.addWidget(lbl_status)
        card_layout.addWidget(lbl_task)
        card_layout.addWidget(lbl_idle)

        return card