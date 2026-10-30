from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QPushButton, QScrollArea, QFileDialog, QMessageBox
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
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.canvas)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        gantt_layout.addWidget(self.scroll_area)
        layout.addWidget(gantt_box, 1)

        # --- NOVA LEGENDA DIVIDIDA EM DUAS LINHAS ---
        bottom_box = QWidget()
        bottom_layout = QHBoxLayout(bottom_box)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        legend_box = QGroupBox("Legenda de Elementos Gráficos e Eventos")
        legend_layout = QVBoxLayout(legend_box)

        # Linha 1: Estados dos Blocos
        row1_layout = QHBoxLayout()
        lbl_leg1 = QLabel("█ Executando (Na CPU)")
        lbl_leg2 = QLabel("⬜ Fila de Prontas (Aguardando)")
        lbl_leg3 = QLabel("▧ Suspensa")
        lbl_leg4 = QLabel("(Vazio) Concluída ou Não Iniciada")

        for lbl in [lbl_leg1, lbl_leg2, lbl_leg3, lbl_leg4]:
            lbl.setStyleSheet("font-size: 11px;")
            row1_layout.addWidget(lbl)

        # Linha 2: Marcadores de Eventos
        row2_layout = QHBoxLayout()
        lbl_ev1 = QLabel("<span style='color:#00FF00;'>▲</span> Chegada (Release)")
        lbl_ev2 = QLabel("<span style='color:#00BFFF;'>■</span> Término")
        lbl_ev3 = QLabel("<span style='color:#F39C12;'>■</span> Início Suspensão")
        lbl_ev4 = QLabel("<span style='color:#F39C12;'>▶</span> Fim Suspensão")
        lbl_ev5 = QLabel("<span style='color:#E74C3C;'>▼</span> Perda de Prazo")
        
        for lbl in [lbl_ev1, lbl_ev2, lbl_ev3, lbl_ev4, lbl_ev5]:
            lbl.setStyleSheet("font-size: 11px; font-weight: bold; background: transparent;")
            row2_layout.addWidget(lbl)

        legend_layout.addLayout(row1_layout)
        legend_layout.addLayout(row2_layout)

        bottom_layout.addWidget(legend_box, 1)

        btn_export = QPushButton("💾 Exportar Imagem do Gantt (PNG)")
        btn_export.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; padding: 10px; min-width: 200px;")

        btn_export.clicked.connect(self.exportar_imagem)

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
        
        tcbs_atuais = state.get("tcbs", [])
        task_ids = [tcb.id for tcb in tcbs_atuais]
        num_tasks = len(task_ids)

        # --- EXTRAÇÃO SEGURA PARA EXPORTAÇÃO ---
        # Salva apenas strings e inteiros para não prender os objetos do simulador
        self._export_data = {
            "tick": tick_atual,
            "task_ids": task_ids,
            "history_primitives": []
        }
        for snap in historico:
            self._export_data["history_primitives"].append({
                "tick": snap["tick"],
                "cpus": [{"status": c.status, "current_task_id": c.current_task_id, "cpu_id": c.cpu_id} for c in snap["cpus"]],
                "tcbs": [{"id": t.id, "ingresso": t.ingresso, "estado": t.estado, "color": t.color} for t in snap["tcbs"]]
            })
        # ---------------------------------------
        
        task_y_map = {tid: i + 1 for i, tid in enumerate(task_ids)}

        self.ax.set_yticks(range(1, num_tasks + 1))
        self.ax.set_yticklabels(task_ids)
        self.ax.set_ylim(0.5, num_tasks + 0.5)

        # Dicionário para guardar a fotografia da tarefa no tick anterior (para detectar mudanças/eventos)
        prev_tcbs = {}

        # Varre as 'fotografias' do passado para desenhar blocos e ícones
        for snap in historico:
            t = snap["tick"]
            tcbs_snap = snap["tcbs"]
            cpus_snap = snap["cpus"]
            
            task_to_cpu = {}
            for cpu in cpus_snap:
                if cpu.status == "EXECUTANDO" and cpu.current_task_id:
                    task_to_cpu[cpu.current_task_id] = cpu.cpu_id
            
            for tcb in tcbs_snap:
                tid = tcb.id
                if tid not in task_y_map:
                    continue
                
                y_pos = task_y_map[tid]
                cor_tarefa = f"#{tcb.color.lstrip('#')}"
                
                # 1. DESENHO DOS BLOCOS (Retângulos)
                if t >= tcb.ingresso:
                    if tcb.estado == "EXECUTANDO":
                        self.ax.barh(y_pos, 1, left=t, color=cor_tarefa, edgecolor="black")
                        
                        # Texto da CPU dentro do bloco executando
                        cpu_id = task_to_cpu.get(tid)
                        if cpu_id is not None:
                            self.ax.text(t + 0.5, y_pos, f"P{cpu_id}", 
                                         ha='center', va='center', 
                                         color='white', fontsize=7, fontweight='bold')
                            
                    elif tcb.estado == "PRONTA":
                        self.ax.barh(y_pos, 1, left=t, color="#FFFFFF", edgecolor="black")
                        
                    elif tcb.estado == "SUSPENSA":
                        self.ax.barh(y_pos, 1, left=t, color="#555555", edgecolor="black", hatch="///")

               # 2. LÓGICA DOS MARCADORES DE EVENTOS (Ícones e Linhas)
                prev_tcb = prev_tcbs.get(tid)
                
                # EVENTO A: Chegada da Tarefa (Ingresso Inicial ou Novo Período)
                if t == tcb.ingresso or (prev_tcb and prev_tcb.estado == "CONCLUIDA" and tcb.estado in ["PRONTA", "EXECUTANDO"]):
                    # Triângulo no topo e linha verde ajustada estritamente aos limites do bloco
                    self.ax.text(t, y_pos + 0.38, "▲", color="#00FF00", ha="center", va="center", fontsize=9, zorder=4)
                    self.ax.vlines(t, ymin=y_pos - 0.38, ymax=y_pos + 0.38, color="#00FF00", linewidth=1.5, zorder=3)
                
                if prev_tcb:
                    # EVENTO B: Término da Execução
                    if prev_tcb.execucoes_concluidas < tcb.execucoes_concluidas:
                        # Quadrado na base e linha azul ajustada estritamente aos limites do bloco
                        self.ax.text(t, y_pos - 0.38, "■", color="#00BFFF", ha="center", va="center", fontsize=8, zorder=4)
                        self.ax.vlines(t, ymin=y_pos - 0.38, ymax=y_pos + 0.38, color="#00BFFF", linewidth=1.5, zorder=3)
                    
                    # EVENTO C: Início de Suspensão (Mudança explícita para SUSPENSA)
                    if prev_tcb.estado != "SUSPENSA" and tcb.estado == "SUSPENSA":
                        # Quadrado laranja no centro
                        self.ax.text(t, y_pos, "■", color="#F39C12", ha="center", va="center", fontsize=9, zorder=4)
                        
                    # EVENTO D: Fim de Suspensão / Retorno (Saiu de SUSPENSA)
                    if prev_tcb.estado == "SUSPENSA" and tcb.estado not in ["SUSPENSA", "CANCELADA"]:
                        self.ax.text(t, y_pos, "▶", color="#F39C12", ha="center", va="center", fontsize=9, zorder=4)
                
                # EVENTO E: Perda de Prazo (Deadline Miss)
                if t == tcb.prazo_absoluto and tcb.estado not in ["CONCLUIDA", "CANCELADA"]:
                    # Triângulo invertido vermelho na parte superior
                    self.ax.text(t, y_pos + 0.38, "▼", color="#E74C3C", ha="center", va="center", fontsize=9, zorder=5)
                    # Linha vermelha cortando os limites do bloco para destacar o momento do estouro
                    self.ax.vlines(t, ymin=y_pos - 0.38, ymax=y_pos + 0.38, color="#E74C3C", linewidth=1.5, zorder=3)

                # Salva o estado desta iteração para comparar no próximo tick da linha do tempo
                prev_tcbs[tid] = tcb

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
    def exportar_imagem(self):
        """Exporta um diagrama de Gantt limpo com fontes dinâmicas e numeração de CPU."""
        if not hasattr(self, '_export_data') or not self._export_data:
            QMessageBox.warning(self, "Aviso", "Não há dados de simulação para exportar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Diagrama de Gantt", "diagrama_gantt.png", "Imagens PNG (*.png)"
        )
        
        if not file_path:
            return

        try:
            data = self._export_data
            historico = data["history_primitives"]
            tick_atual = data["tick"]
            task_ids = data["task_ids"]
            
            num_tasks = len(task_ids)
            if num_tasks == 0:
                return

            task_y_map = {tid: i + 1 for i, tid in enumerate(task_ids)}
            limite_x = max(15, tick_atual + 2)

            # Cálculos Dinâmicos de Dimensão e Fonte
            largura_fig = max(10, limite_x * 0.25)
            altura_fig = max(5, num_tasks * 0.4)
            
            tamanho_fonte_y = max(6, 12 - (num_tasks // 5))
            tamanho_fonte_x = max(6, 12 - (limite_x // 15))
            tamanho_fonte_cpu = max(5, 10 - (limite_x // 20))

            export_fig = Figure(figsize=(largura_fig, altura_fig), dpi=300)
            export_fig.patch.set_facecolor('white')
            ax = export_fig.add_subplot(111)
            ax.set_facecolor('white')

            for snap in historico:
                t = snap["tick"]
                
                # Mapeia CPU (primitiva)
                task_to_cpu = {}
                for cpu in snap["cpus"]:
                    if cpu["status"] == "EXECUTANDO" and cpu["current_task_id"]:
                        task_to_cpu[cpu["current_task_id"]] = cpu["cpu_id"]

                for tcb in snap["tcbs"]:
                    tid = tcb["id"]
                    if tid not in task_y_map:
                        continue
                    
                    y_pos = task_y_map[tid]
                    
                    if t >= tcb["ingresso"]:
                        if tcb["estado"] == "EXECUTANDO":
                            cor_tarefa = f"#{tcb['color'].lstrip('#')}"
                            ax.barh(y_pos, 1, left=t, color=cor_tarefa, edgecolor="black", linewidth=1.2, zorder=3)
                            
                            cpu_id = task_to_cpu.get(tid)
                            if cpu_id is not None:
                                ax.text(t + 0.5, y_pos, f"{cpu_id}", ha='center', va='center', 
                                        color='white', fontweight='bold', fontsize=tamanho_fonte_cpu, zorder=4)
                                
                        elif tcb["estado"] == "PRONTA":
                            ax.barh(y_pos, 1, left=t, color="white", edgecolor="black", linewidth=1.2, zorder=3)

            # Estilização
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('black')
            ax.spines['left'].set_color('black')
            ax.spines['bottom'].set_linewidth(1.2)
            ax.spines['left'].set_linewidth(1.2)

            ax.plot(1, 0, ">k", transform=ax.get_yaxis_transform(), clip_on=False)
            ax.plot(0, 1, "^k", transform=ax.get_xaxis_transform(), clip_on=False)

            ax.set_xlim(0, limite_x)
            ax.set_xticks(range(0, limite_x + 1))
            ax.tick_params(axis='x', labelsize=tamanho_fonte_x)
            ax.set_xlabel("t", loc="right", fontsize=12)
            
            ax.set_ylim(0.5, num_tasks + 0.5)
            ax.set_yticks(range(1, num_tasks + 1))
            ax.set_yticklabels(task_ids, fontsize=tamanho_fonte_y)

            ax.grid(True, axis='x', linestyle=':', color='gray', alpha=0.7, zorder=0)

            export_fig.tight_layout()
            export_fig.savefig(file_path, format='png', bbox_inches='tight', dpi=300)
            
            QMessageBox.information(self, "Exportação Concluída", f"O diagrama foi exportado para:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro na Exportação", f"Erro: {str(e)}")