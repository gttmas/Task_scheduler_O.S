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

        # --- AQUI ENTRA O GRÁFICO REAL ---
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.figure.patch.set_facecolor('#1E1E1E') # Fundo combinando com a interface
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.figure)
        
        gantt_layout.addWidget(self.canvas)
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
            
        # Linhas pontilhadas verticais como na imagem de referência
        self.ax.grid(True, axis='x', linestyle=':', color='#555555')
        
        historico = state.get("history", [])
        tick_atual = state.get("tick", 0)
        
        # Mapeia as Tarefas para o Eixo Y
        # Pega as tarefas atuais do estado para saber quantas existem e os IDs
        tcbs_atuais = state.get("tcbs", [])
        task_ids = [tcb.id for tcb in tcbs_atuais]
        num_tasks = len(task_ids)
        
        # Associa cada ID de tarefa a uma posição no eixo Y (T1 = 1, T2 = 2...)
        # Para ficar igual à imagem (T1 embaixo, T2 em cima), podemos inverter ou manter a ordem.
        # Mantendo T1 embaixo:
        task_y_map = {tid: i + 1 for i, tid in enumerate(task_ids)}

        self.ax.set_yticks(range(1, num_tasks + 1))
        self.ax.set_yticklabels(task_ids)
        self.ax.set_ylim(0.5, num_tasks + 0.5)

        # Varre as 'fotografias' do passado para desenhar os blocos
        for snap in historico:
            t = snap["tick"]
            tcbs_snap = snap["tcbs"]
            
            # Analisa o estado de CADA tarefa naquele instante de tempo
            for tcb in tcbs_snap:
                if tcb.id not in task_y_map:
                    continue
                    
                y_pos = task_y_map[tcb.id]
                cor_tarefa = f"#{tcb.color.lstrip('#')}"
                
                if tcb.estado == "EXECUTANDO":
                    # Bloco colorido (Na CPU)
                    self.ax.barh(y_pos, 1, left=t, color=cor_tarefa, edgecolor="black")
                    
                elif tcb.estado == "PRONTA":
                    # Bloco branco (Fila de Prontas)
                    self.ax.barh(y_pos, 1, left=t, color="#FFFFFF", edgecolor="black")
                    
                # Se for "CONCLUIDA" ou outro estado, não desenha nada (fica vazio)

        # Configura o eixo X (Linha do Tempo)
        limite_x = max(15, tick_atual + 2)
        self.ax.set_xlim(0, limite_x)
        
        # Garante que os números do eixo X pulem de 1 em 1
        self.ax.set_xticks(range(0, limite_x + 1))
        self.ax.set_xlabel("Tempo (Ticks)", color='white')

        # Redesenha efetivamente na tela
        self.canvas.draw()