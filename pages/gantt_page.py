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
    def __init__(self, parent=None): # Função init padrão da classe
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Função que inicia a interface da página de visualização do diagrama de gantt"""
        layout = QVBoxLayout(self) # definição da página gantt do modo vertical 
        layout.setContentsMargins(15, 15, 15, 15) # margens da página
        layout.setSpacing(12)

        gantt_box = QGroupBox("Visualização Gráfica da Execução ao Longo do Tempo") # legenda superior da página
        gantt_layout = QVBoxLayout(gantt_box)

        # ------------------------------------------------------------------------ criação do diagrama de gantt

        # características da página
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.figure.patch.set_facecolor('#1E1E1E') # cor do fundo da página
        self.ax = self.figure.add_subplot(111) # colocamos uma área para os eixos (axes)
        self.canvas = FigureCanvasQTAgg(self.figure) # comunicação entre MatPlotLib e PySide6 (tela em widget)

        # coloca o diagrama dentro de uma barra de rolagem
        # permite a visualização de gráficos muito grandes sem ficar espremido
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.canvas)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }") # tira a margem da área de rolagem
        
        gantt_layout.addWidget(self.scroll_area) # adiciona a área de scroll
        layout.addWidget(gantt_box, 1) # coloca a área do gantt

        # adiciona a área inferior
        bottom_box = QWidget()
        bottom_layout = QHBoxLayout(bottom_box)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        legend_box = QGroupBox("Legenda de Elementos Gráficos e Eventos")
        legend_layout = QVBoxLayout(legend_box)

        # alinha a primeira linha da legenda no centro
        row1_layout = QHBoxLayout()
        row1_layout.setAlignment(Qt.AlignCenter)
        row1_layout.setSpacing(30)

        # explica o que cada símbolo da primeira linha da legenda significa
        lbl_leg1 = QLabel("<span style='color:#2ECC71;'>■</span> Executando (Cor da Tarefa)") # tarefas coloridas estão sendo executadas naquele tick
        lbl_leg2 = QLabel("⬜ Fila de Prontas (Aguardando)") # tarefas brancas estão na fila de prontas
        lbl_leg3 = QLabel("▧ Suspensa") # tarefas hashuradas estão suspensas
        lbl_leg4 = QLabel("[Vazio] Concluída ou Não Iniciada") # tarefas sem representação estão concluídas ou não iniciadas

        # adiciona as legendas acima na primeira linha de legendas
        for lbl in [lbl_leg1, lbl_leg2, lbl_leg3, lbl_leg4]:
            lbl.setStyleSheet("font-size: 11px; font-weight: bold;")
            row1_layout.addWidget(lbl)

        # alinha a primeira linha da legenda no centro
        row2_layout = QHBoxLayout()
        row2_layout.setAlignment(Qt.AlignCenter)
        row2_layout.setSpacing(30)

        # explica o que cada símbolo da segunda linha da legenda significa
        lbl_ev1 = QLabel("<span style='color:#00FF00;'>▲</span> Chegada (Release)") # um triângulo verde representa a chegada das tarefas
        lbl_ev2 = QLabel("<span style='color:#00BFFF;'>■</span> Término") # um quadrado azul indica o fim de uma execução da tarefa
        lbl_ev3 = QLabel("<span style='color:#F39C12;'>■</span> Início Suspensão") # um quadrado laranja indica o momento que a task é supensa
        lbl_ev4 = QLabel("<span style='color:#F39C12;'>▶</span> Fim Suspensão") # um "play" laranja representa a task parando de ficar supensa
        lbl_ev5 = QLabel("<span style='color:#E74C3C;'>▼</span> Perda de Prazo") # um triângulo vermelho indica que a tarefa estourou o prazo

        # adiciona as legendas acima na segunda linha de legendas
        for lbl in [lbl_ev1, lbl_ev2, lbl_ev3, lbl_ev4, lbl_ev5]:
            lbl.setStyleSheet("font-size: 11px; font-weight: bold; background: transparent;")
            row2_layout.addWidget(lbl)

        # adiciona as linhas de legenda na caixa inferior
        legend_layout.addLayout(row1_layout)
        legend_layout.addLayout(row2_layout)

        # adiciona a caixa de legendas no widget
        bottom_layout.addWidget(legend_box, 1)

        # botão de salvamento do diagrama de gantt em uma imagem
        self.btn_export = QPushButton("💾 Exportar Imagem do Gantt (SVG)")
        self.btn_export.setStyleSheet("background-color: gray; color: white; font-weight: bold; padding: 10px; min-width: 200px;")
        self.btn_export.clicked.connect(self.exportar_imagem) # conecta o botão à função de salvar imagem
        bottom_layout.addWidget(self.btn_export) # adiciona o botão de salvamento no widget

        # adiciona o widget na página
        layout.addWidget(bottom_box)

    def render_state(self, state: dict):
        """Desenha o gráfico consumindo o histórico salvo pelo Motor.
        Parâmetro: dicionário contendo as informações da simulação"""
        
        if not state: # se não houver entrada, não executa
            return

        # ANÁLISE DE REQUISITO: só é possível salvar o diagrama como uma foto se a simulação estiver terminada,
        # o botão de salvamento fica cinza enquanto a simulação estiver em andamento.
        self.simulacao_finalizada = state.get("is_finished", False)
        if self.simulacao_finalizada:
            # deixa o botão verde caso a simulação esteja finalizada
            self.btn_export.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; padding: 10px; min-width: 200px;") 
        else:
            # deixa o botão cinza caso a simulação não esteja finalizada
            self.btn_export.setStyleSheet("background-color: gray; color: white; font-weight: bold; padding: 10px; min-width: 200px;")

        self.ax.clear() # limpa o gráfico da chamada anterior
        
        self.ax.set_facecolor('#1E1E1E') # define o fundo do diagrama como cinza escuro
        self.ax.tick_params(colors='white') # define as letras como branco para contraste
        for spine in self.ax.spines.values(): # define as bordas com um cinza mais claro
            spine.set_color('#555555')

        # define uma grade pontilhada para facilitar a visualização dos ticks
        self.ax.grid(True, axis='x', linestyle=':', color='#555555')

        #pega o histórico e a contagem de ticks atual salva no dicionário do motor da simulação enviado como parâmetro
        historico = state.get("history", [])
        tick_atual = state.get("tick", 0)

        # pega a lista de TCB's (informações das tarefas) do dicionário
        tcbs_atuais = state.get("tcbs", [])
        task_ids = [tcb.id for tcb in tcbs_atuais] # pega só os id's das tarefas 
        num_tasks = len(task_ids) 

        # --------------------------- guardando dados da simualação para a função de exportação da imagem ---------------------------

        #c ria um dicionário "export_data" para guardar algumas informações relevantes
        self._export_data = {
            "tick": tick_atual, # número do tick atual
            "task_ids": task_ids, # lista de id"s das tasks
            "history_primitives": [] # uma lista vazia que vai receber o histórico "limpo", com apenas dados primitivos, ou seja, 
                                     # apenas com os dados necessários para desenhar o gráfico
        }
        # inicia um loop que vai olhar "foto por foto" (os snapshots) de tudo o que aconteceu em cada segundo da simulação
        for snap in historico:
            self._export_data["history_primitives"].append({
                "tick": snap["tick"],
                # extrai apenas o status (se está executando), qual tarefa está rodando e o número da CPU
                "cpus": [{"status": c.status, "current_task_id": c.current_task_id, "cpu_id": c.cpu_id} for c in snap["cpus"]],
                # extrai id, ingresso, estado, cor, execucoes_concluidas e prazo_absoluto
                "tcbs": [{"id": t.id, "ingresso": t.ingresso, "estado": t.estado, "color": t.color, "execucoes_concluidas": t.execucoes_concluidas, "prazo_absoluto": t.prazo_absoluto} for t in snap["tcbs"]]
            })

        # ---------------------------------------------------------------------------------------------------------------------------
        
        # "mapinha" pra saber em qual altura (eixo Y) desenhar cada tarefa
        task_y_map = {tid: i + 1 for i, tid in enumerate(task_ids)}

        # Configurando os textos do eixo vertical
        self.ax.set_yticks(range(1, num_tasks + 1))
        self.ax.set_yticklabels(task_ids)
        self.ax.set_ylim(0.5, num_tasks + 0.5)

        # memória temporária para saber o estado da tarefa no instante imediatamente anterior ao atual
        prev_tcbs = {}

        # desenhando o histórico no diagrama de gantt
        for snap in historico:
            # pega os dados de cada instante do histórico
            t = snap["tick"]
            tcbs_snap = snap["tcbs"]
            cpus_snap = snap["cpus"]

            # descobre qual tarefa está em qual CPU naquele momento
            task_to_cpu = {}
            for cpu in cpus_snap: # procura por todas as cpus
                if cpu.status == "EXECUTANDO" and cpu.current_task_id: # se aquela cpu estiver executando:
                    task_to_cpu[cpu.current_task_id] = cpu.cpu_id      # salva o id da tarefa dentro dela

            # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ desenha cada tarefa no diagrama @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

            for tcb in tcbs_snap:
                tid = tcb.id
                if tid not in task_y_map: # se ela não tem espaço para ser desenhada (é inválida),
                    continue              # vai para a próxima
                
                y_pos = task_y_map[tid] # pega em qual altura aquela tarefa deve ser desenhada (no "mapinha")
                cor_tarefa = f"#{tcb.color.lstrip('#')}" # segurança para aceitar apenas cores válidas (sem "#" a mais)

                # ------------------------------- trecho que desenha os retângulos das tarefas ---------------------------
                if t >= tcb.ingresso: 

                    # se a tarefa está executando, pinta um retângulo da cor da task no tick
                    if tcb.estado == "EXECUTANDO":
                        self.ax.barh(y_pos, 1, left=t, color=cor_tarefa, edgecolor="black")

                        # escreve o número da cpu em que está sendo executada a task no retângulo
                        cpu_id = task_to_cpu.get(tid)
                        if cpu_id is not None:
                            self.ax.text(t + 0.5, y_pos, f"P{cpu_id}", 
                                         ha='center', va='center', 
                                         color='white', fontsize=7, fontweight='bold')

                    # se está na fila de prontas, pinta um retângulo branco no tick
                    elif tcb.estado == "PRONTA":
                        self.ax.barh(y_pos, 1, left=t, color="#FFFFFF", edgecolor="black")

                    # se está suspensa, pinta um retângulo hashurado no tick
                    elif tcb.estado == "SUSPENSA":
                        self.ax.barh(y_pos, 1, left=t, color="#555555", edgecolor="black", hatch="///")
                # ---------------------------------------------------------------------------------------------------------

                # pega o estado passado da tarefa atual para desenhar os eventos
                prev_tcb = prev_tcbs.get(tid)

                # ------------------------------- trecho que desenha os eventos com os símbolos ---------------------------

                # EVENTO: tarefa chegou na fila de prontas, analisado pelo instante de ingresso da task ou:
                # se estiver CONCLUÍDA no instante anterior e no atual PRONTA ou EXECUTANDO, ela voltou agora
                if t == tcb.ingresso or (prev_tcb and prev_tcb.estado == "CONCLUIDA" and tcb.estado in ["PRONTA", "EXECUTANDO"]):
                    # representado por um triângulo e uma linha verde no tick em que ocorre o evento
                    self.ax.text(t, y_pos + 0.38, "▲", color="#00FF00", ha="center", va="center", fontsize=9, zorder=4)
                    self.ax.vlines(t, ymin=y_pos - 0.38, ymax=y_pos + 0.38, color="#00FF00", linewidth=1.5, zorder=3)
                
                if prev_tcb:
                    # EVENTO: terminou uma de suas execuções, analisado por mudanças no 
                    # contador de execuções concluídas
                    if prev_tcb.execucoes_concluidas < tcb.execucoes_concluidas:
                        # representado por um quadrado azul e uma linha no tick em que ocorre o evento
                        self.ax.text(t, y_pos - 0.38, "■", color="#00BFFF", ha="center", va="center", fontsize=8, zorder=4)
                        self.ax.vlines(t, ymin=y_pos - 0.38, ymax=y_pos + 0.38, color="#00BFFF", linewidth=1.5, zorder=3)

                    # EVENTO: tarefa foi suspensa, analisado pelo estado da task no instante anterior
                    if prev_tcb.estado != "SUSPENSA" and tcb.estado == "SUSPENSA":
                        # representado por um quadrado laranja
                        self.ax.text(t, y_pos, "■", color="#F39C12", ha="center", va="center", fontsize=9, zorder=4)

                    # EVENTO: tarefa deixou de ser suspensa, analisado pelo estado da task no instante anterior
                    if prev_tcb.estado == "SUSPENSA" and tcb.estado not in ["SUSPENSA", "CANCELADA"]:
                        # representado por um "play" laranja
                        self.ax.text(t, y_pos, "▶", color="#F39C12", ha="center", va="center", fontsize=9, zorder=4)

                # EVENTO: tarefa estourou o prazo, analisado se o prazo é o instante atual e se ela não está concluída
                if t == tcb.prazo_absoluto and tcb.estado not in ["CONCLUIDA", "CANCELADA"]:
                    # representado por um triângulo vermelho
                    self.ax.text(t, y_pos + 0.38, "▼", color="#E74C3C", ha="center", va="center", fontsize=9, zorder=5)
                    self.ax.vlines(t, ymin=y_pos - 0.38, ymax=y_pos + 0.38, color="#E74C3C", linewidth=1.5, zorder=3)

                # Salva o estado de agora pra comparar na próxima volta do loop
                prev_tcbs[tid] = tcb
                # ---------------------------------------------------------------------------------------------------------

            # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

        # Configurando o tamanho da linha do tempo (eixo X)
        limite_x = max(15, tick_atual + 2) # Pelo menos 15 ticks, ou o tick atual + 2 de folga
        self.ax.set_xlim(0, limite_x)
        self.ax.set_xticks(range(0, limite_x + 1))
        self.ax.set_xlabel("Tempo (Ticks)", color='white')

        # controle para saber quando se deve ativar a funcionalidade da área de rolagem
        largura_minima = max(800, limite_x * 25)
        self.canvas.setMinimumWidth(largura_minima)
        altura_minima = max(300, num_tasks * 35)
        self.canvas.setMinimumHeight(altura_minima)
        
        self.figure.tight_layout() # "espreme" espaços inúteis
        self.canvas.draw() # mostra o diagrama na tela

    def exportar_imagem(self):
        """Exporta uma figura do diagrama de Gantt com os valores da simulação completa em formato SVG"""
        # controle para caso ocorra um erro com o motor da simulação, para que não seja salvo em imagens
        if not hasattr(self, '_export_data') or not self._export_data:
            QMessageBox.warning(self, "Aviso", "Não há dados de simulação para exportar.")
            return

        # mensagem de erro que só permite a imagem ser salva se a simulação estiver completa
        if not getattr(self, 'simulacao_finalizada', False):
            QMessageBox.warning(
                self, 
                "Erro", 
                "Conclua a simulação antes de exportar."
            )
            return

        # janela que permite escolher o nome do arquivo e onde salvar (Restrito a SVG)
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Diagrama de Gantt", "diagrama_gantt.svg", "Imagens Vetoriais (*.svg)"
        )

        # caso não seja possível, não procede com o processo de salvamento
        if not file_path:
            return

        try:
            # resgata o dicionário criado na função "render_state" que possui apenas os dados necessários
            data = self._export_data
            historico = data["history_primitives"]
            tick_atual = data["tick"]
            task_ids = data["task_ids"]

            # não permite desenhar se não existir nenhuma tarefa
            num_tasks = len(task_ids)
            if num_tasks == 0:
                return

            # cria um novo "mapinha" para o eixo y
            task_y_map = {tid: i + 1 for i, tid in enumerate(task_ids)}
            #define o tamanho máximo do diagrama a ser desenhado
            limite_x = max(15, tick_atual + 2)

            # calcula o tamanho da imagem e das fontes
            largura_fig = max(10, limite_x * 0.25)
            altura_fig = max(5, num_tasks * 0.4)
            tamanho_fonte_y = max(6, 12 - (num_tasks // 5))
            tamanho_fonte_x = max(6, 12 - (limite_x // 15))
            tamanho_fonte_cpu = max(5, 10 - (limite_x // 20))

            # Cria um gráfico novo, com fundo branco, só pra gerar o arquivo
            export_fig = Figure(figsize=(largura_fig, altura_fig))
            export_fig.patch.set_facecolor('white')
            ax = export_fig.add_subplot(111)
            ax.set_facecolor('white')

            # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ desenha cada tarefa no diagrama @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

            # Dicionário temporário para lembrar o estado anterior da tarefa e detectar eventos
            prev_tcbs = {}

            # a lógica aqui é identica à função "render_state"
            for snap in historico:
                t = snap["tick"]
                
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

                        elif tcb["estado"] == "SUSPENSA":
                            ax.barh(y_pos, 1, left=t, color="#555555", edgecolor="black", hatch="///")

                    prev_tcb = prev_tcbs.get(tid)
                    
                    # EVENTO: Chegada (▲ verde)
                    if t == tcb["ingresso"] or (prev_tcb and prev_tcb["estado"] == "CONCLUIDA" and tcb["estado"] in ["PRONTA", "EXECUTANDO"]):
                        ax.text(t, y_pos + 0.38, "▲", color="#00FF00", ha="center", va="center", fontsize=9, zorder=5)
                        ax.vlines(t, ymin=y_pos - 0.38, ymax=y_pos + 0.38, color="#00FF00", linewidth=1.5, zorder=4)
                    
                    if prev_tcb:
                        # EVENTO: Término (■ azul) - Usando .get() para evitar erro caso a chave não tenha sido salva
                        if prev_tcb.get("execucoes_concluidas", 0) < tcb.get("execucoes_concluidas", 0):
                            ax.text(t, y_pos - 0.38, "■", color="#00BFFF", ha="center", va="center", fontsize=8, zorder=5)
                            ax.vlines(t, ymin=y_pos - 0.38, ymax=y_pos + 0.38, color="#00BFFF", linewidth=1.5, zorder=4)
                        
                        # EVENTO: Início Suspensão (■ laranja)
                        if prev_tcb["estado"] != "SUSPENSA" and tcb["estado"] == "SUSPENSA":
                            ax.text(t, y_pos, "■", color="#F39C12", ha="center", va="center", fontsize=9, zorder=5)
                            
                        # EVENTO: Fim Suspensão (▶ laranja)
                        if prev_tcb["estado"] == "SUSPENSA" and tcb["estado"] not in ["SUSPENSA", "CANCELADA"]:
                            ax.text(t, y_pos, "▶", color="#F39C12", ha="center", va="center", fontsize=9, zorder=5)
                    
                    # EVENTO: Perda de Prazo (▼ vermelho)
                    prazo_abs = tcb.get("prazo_absoluto")
                    if prazo_abs is not None and t == prazo_abs and tcb["estado"] not in ["CONCLUIDA", "CANCELADA"]:
                        ax.text(t, y_pos + 0.38, "▼", color="#E74C3C", ha="center", va="center", fontsize=9, zorder=6)
                        ax.vlines(t, ymin=y_pos - 0.38, ymax=y_pos + 0.38, color="#E74C3C", linewidth=1.5, zorder=4)

                    # Salva o estado atual para comparar no próximo ciclo
                    prev_tcbs[tid] = tcb
            # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

            # tira as linhas da direita e de cima, deixando apenas as linhas inferior e esquerda (eixos)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('black')
            ax.spines['left'].set_color('black')
            ax.spines['bottom'].set_linewidth(1.2)
            ax.spines['left'].set_linewidth(1.2)

            # coloca setas nos eixos
            ax.plot(1, 0, ">k", transform=ax.get_yaxis_transform(), clip_on=False)
            ax.plot(0, 1, "^k", transform=ax.get_xaxis_transform(), clip_on=False)

            # ajusta os limites e os números
            ax.set_xlim(0, limite_x)
            ax.set_xticks(range(0, limite_x + 1))
            ax.tick_params(axis='x', labelsize=tamanho_fonte_x)
            ax.set_xlabel("t", loc="right", fontsize=12) # coloca o "t" de tempo no cantinho

            ax.set_ylim(0.5, num_tasks + 0.5)
            ax.set_yticks(range(1, num_tasks + 1))
            ax.set_yticklabels(task_ids, fontsize=tamanho_fonte_y)

            # ama grade suave no fundo
            ax.grid(True, axis='x', linestyle=':', color='gray', alpha=0.7, zorder=0)

            # ajusta os espaços e salva a imagem forçando o formato SVG (DPI foi removido por ser irrelevante para vetores)
            export_fig.tight_layout()
            export_fig.savefig(file_path, format='svg', bbox_inches='tight')

            # alerta o usuário que deu tudo certo
            QMessageBox.information(self, "Exportação Concluída", f"O diagrama foi exportado para:\n{file_path}")
            
        except Exception as e:
            # se der erro, também avisa o usuário
            QMessageBox.critical(self, "Erro na Exportação", f"Erro: {str(e)}")