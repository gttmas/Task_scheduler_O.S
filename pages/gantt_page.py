from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QPushButton
)
from PySide6.QtCore import Qt

# Importações do Matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


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

        # --- AQUI ENTRA O GRÁFICO REAL SUBSTITUINDO O PLACEHOLDER ---
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.figure.patch.set_facecolor('#1E1E1E') # Fundo combinando com a interface
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.figure)
        
        gantt_layout.addWidget(self.canvas)
        layout.addWidget(gantt_box, 1)

        # --- MANTÉM A SUA LEGENDA E BOTÃO DE EXPORTAR INTACTOS ---
        bottom_box = QWidget()
        bottom_layout = QHBoxLayout(bottom_box)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        legend_box = QGroupBox("Legenda de Elementos Gráficos")
        legend_layout = QHBoxLayout(legend_box)

        lbl_leg1 = QLabel("█ Executando: Cor da Tarefa")
        lbl_leg2 = QLabel("░ Fila: Ausência de Cor")
        lbl_leg3 = QLabel("▓ Suspensa: Preto Hachurado")
        lbl_leg4 = QLabel("↓ Ingresso | ↑ Término | ⚠ Perda Deadline")

        for lbl in [lbl_leg1, lbl_leg2, lbl_leg3, lbl_leg4]:
            lbl.setStyleSheet("font-size: 11px;")
            legend_layout.addWidget(lbl)

        bottom_layout.addWidget(legend_box, 1)

        btn_export = QPushButton("💾 Exportar Imagem do Gantt (PNG/SVG)")
        btn_export.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; padding: 10px;")
        bottom_layout.addWidget(btn_export)

        layout.addWidget(bottom_box)

    def render_state(self, state: dict):
        """Desenha o gráfico consumindo o histórico salvo pelo Motor."""
        if not state:
            return

        self.ax.clear()
        
        # Estilo do gráfico para o tema escuro
        self.ax.set_facecolor('#1E1E1E')
        self.ax.tick_params(colors='white')
        for spine in self.ax.spines.values():
            spine.set_color('#555555')
        
        historico = state.get("history", [])
        num_cpus = len(state.get("cpus", []))
        tick_atual = state.get("tick", 0)
        
        # Configura o eixo Y (CPUs)
        self.ax.set_yticks(range(1, num_cpus + 1))
        self.ax.set_yticklabels([f"CPU {i}" for i in range(1, num_cpus + 1)])
        self.ax.set_ylim(0.5, num_cpus + 0.5)

        # Varre as 'fotografias' do passado para desenhar os blocos de execução
        for snap in historico:
            t = snap["tick"]
            cpus_snap = snap["cpus"]
            tcbs_snap = {tcb.id: tcb for tcb in snap["tcbs"]}
            
            for cpu in cpus_snap:
                if cpu.status == "EXECUTANDO" and cpu.current_task_id:
                    tarefa = tcbs_snap.get(cpu.current_task_id)
                    if tarefa:
                        cor = f"#{tarefa.color.lstrip('#')}"
                        # Desenha o bloco (CPU no eixo y, largura de 1 tick)
                        self.ax.barh(cpu.cpu_id, 1, left=t, color=cor, edgecolor="black")

        # Configura o eixo X (Linha do Tempo)
        limite_x = max(10, tick_atual + 2)
        self.ax.set_xlim(0, limite_x)
        self.ax.set_xlabel("Tempo (Ticks)", color='white')

        # Redesenha efetivamente na tela
        self.canvas.draw()