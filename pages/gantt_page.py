from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QPushButton, QScrollArea
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

        # --- CONFIGURAÇÃO DO GRÁFICO ---
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.figure.patch.set_facecolor('#1E1E1E') 
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.figure)
        
        # --- NOVO: ENVOLVENDO O GRÁFICO EM UMA ÁREA DE ROLAGEM ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # Permite que o gráfico cresça e encolha
        self.scroll_area.setWidget(self.canvas)    # Coloca o canvas dentro do scroll
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }") # Remove bordas duplas
        
        gantt_layout.addWidget(self.scroll_area) # Adiciona o scroll na tela, não o canvas direto
        layout.addWidget(gantt_box, 1)

        # --- LEGENDA ---
        bottom_box = QWidget()
        bottom_layout = QHBoxLayout(bottom_box)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        legend_box = QGroupBox("Legenda de Elementos Gráficos")
        legend_layout = QHBoxLayout(legend_box)

        lbl_leg1 = QLabel("█ Executando (Na CPU)")
        lbl_leg2 = QLabel("⬜ Fila de Prontas (Aguardando)")
        lbl_leg3 = QLabel("(Vazio) Concluída ou Não Iniciada")

        for lbl in [lbl_leg1, lbl_leg2, lbl_leg3]:
            lbl.setStyleSheet("font-size: 11px;")
            legend_layout.addWidget(lbl)

        bottom_layout.addWidget(legend_box, 1)

        btn_export = QPushButton("💾 Exportar Imagem do Gantt (PNG)")
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
            
        self.ax.grid(True, axis='x', linestyle=':', color='#555555')
        
        historico = state.get("history", [])
        tick_atual = state.get("tick", 0)
        
        # Mapeia as Tarefas para o Eixo Y
        tcbs_atuais = state.get("tcbs", [])
        task_ids = [tcb.id for tcb in tcbs_atuais]
        num_tasks = len(task_ids)
        
        # CORREÇÃO 1: Mantém T1 na parte inferior (base = 1)
        task_y_map = {tid: i + 1 for i, tid in enumerate(task_ids)}

        self.ax.set_yticks(range(1, num_tasks + 1))
        self.ax.set_yticklabels(task_ids)
        self.ax.set_ylim(0.5, num_tasks + 0.5)

        # Varre as 'fotografias' do passado para desenhar os blocos
        for snap in historico:
            t = snap["tick"]
            tcbs_snap = snap["tcbs"]
            
            for tcb in tcbs_snap:
                if tcb.id not in task_y_map:
                    continue
                
                # CORREÇÃO 2: Se o relógio não chegou no tempo de ingresso, 
                # a tarefa "não existe" no sistema, então não desenha nada.
                if t < tcb.ingresso:
                    continue
                    
                y_pos = task_y_map[tcb.id]
                cor_tarefa = f"#{tcb.color.lstrip('#')}"
                
                if tcb.estado == "EXECUTANDO":
                    self.ax.barh(y_pos, 1, left=t, color=cor_tarefa, edgecolor="black")
                elif tcb.estado == "PRONTA":
                    self.ax.barh(y_pos, 1, left=t, color="#FFFFFF", edgecolor="black")

        # Configura o eixo X (Linha do Tempo)
        limite_x = max(15, tick_atual + 2)
        self.ax.set_xlim(0, limite_x)
        self.ax.set_xticks(range(0, limite_x + 1))
        self.ax.set_xlabel("Tempo (Ticks)", color='white')

        # Dimensionamento Dinâmico para Habilitar o Scroll
        largura_minima = max(800, limite_x * 25)
        self.canvas.setMinimumWidth(largura_minima)
        
        altura_minima = max(300, num_tasks * 35)
        self.canvas.setMinimumHeight(altura_minima)
        
        self.figure.tight_layout()
        self.canvas.draw()