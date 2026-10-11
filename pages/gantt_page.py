from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QFrame, QPushButton
)
from PySide6.QtCore import Qt


class GanttPage(QWidget):
    """Página de Visualização do Diagrama de Gantt da Simulação."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        gantt_box = QGroupBox("Visualização Gráfica da Execução ao Longo do Tempo")
        gantt_layout = QVBoxLayout(gantt_box)

        self.gantt_canvas_placeholder = QFrame()
        self.gantt_canvas_placeholder.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E; border: 1px dashed #555555; border-radius: 4px;
            }
        """)
        placeholder_layout = QVBoxLayout(self.gantt_canvas_placeholder)
        self.lbl_info = QLabel("📊 [ Área de Renderização do Gráfico de Gantt (Matplotlib) ]")
        self.lbl_info.setAlignment(Qt.AlignCenter)
        self.lbl_info.setStyleSheet("color: #888888; font-size: 14px;")
        placeholder_layout.addWidget(self.lbl_info)

        gantt_layout.addWidget(self.gantt_canvas_placeholder, 1)
        layout.addWidget(gantt_box, 1)

        bottom_box = QWidget()
        bottom_layout = QHBoxLayout(bottom_box)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        legend_box = QGroupBox("Legenda de Elementos Gráficos")
        legend_layout = QHBoxLayout(legend_box)

        lbl_leg1 = QLabel("█ Executando: Cor da Tarefa")
        lbl_leg2 = QLabel("░ Fila: Ausência de Cor")
        lbl_leg3 = QLabel("▓ Suspensa: Preto Hachurado")
        lbl_leg4 = QLabel("↓ Ingresso | ↑ Término | ⚠ Perda Deadline | 🎲 Sorteio")

        for lbl in [lbl_leg1, lbl_leg2, lbl_leg3, lbl_leg4]:
            lbl.setStyleSheet("font-size: 11px;")
            legend_layout.addWidget(lbl)

        bottom_layout.addWidget(legend_box, 1)

        btn_export = QPushButton("💾 Exportar Imagem do Gantt (PNG/SVG)")
        btn_export.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; padding: 10px;")
        bottom_layout.addWidget(btn_export)

        layout.addWidget(bottom_box)

    def update_config(self, config: dict):
        """Atualiza a prévia do gráfico de Gantt com as dimensões de CPU e Tarefas."""
        cpus_count = config.get("cpus", 1)
        tasks = config.get("tasks", [])
        algo = config.get("algorithm", "RM")

        info_text = (
            f"📊 [ Área de Renderização do Gráfico de Gantt (Matplotlib) ]\n\n"
            f"Eixo Y: {cpus_count} Processador(es) | Eixo X: Linha do Tempo (Ticks)\n"
            f"Algoritmo: {algo} | Total de Tarefas a Renderizar: {len(tasks)}\n\n"
            f"(Ao avançar os ticks, a execução das CPUs será desenhada aqui)"
        )
        self.lbl_info.setText(info_text)