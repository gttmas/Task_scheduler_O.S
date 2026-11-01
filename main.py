import sys 
from PySide6.QtWidgets import ( 
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QStackedWidget, QMessageBox
)
from PySide6.QtCore import Qt, QTimer 

from pages import ConfigPage, CPUsPage, TasksPage, GanttPage 
from core import SimulationEngine 

# classe da janela principal que unifica o sistema
class MainWindow(QMainWindow): 
    def __init__(self): # construtor da janela
        super().__init__() # inicializa a classe base do qmainwindow
        self.setWindowTitle("Simulador de Escalonamento de Tempo Real - SO Multitarefa") # define o titulo da janela
        self.resize(1150, 750) # define a largura e altura iniciais da janela

        self.engine = SimulationEngine() # instancia o motor da simulacao
        self.is_running = False # controle de estado se o relogio ta rodando ou pausado
        self.current_config = {} # guarda o dicionario com as configuracoes ativas

        self.timer = QTimer(self) # cria o temporizador do relogio global
        self.timer.setInterval(3000) # define o intervalo de 3 segundos por tick no modo automatico
        self.timer.timeout.connect(self.advance_tick) # avanca um tick a cada estouro do temporizador

        self.init_hud_ui() # desenha a interface topo menu lateral e telas

        # conecta os sinais das paginas visuais com as acoes do motor principal
        self.page_config.config_changed.connect(self.on_config_changed) # dispara quando altera configuracao
        self.page_tasks.manual_state_change.connect(self.apply_manual_task_state) # dispara ao alterar estado manual de tarefa
        self.page_tasks.add_task_requested.connect(self.on_dynamic_task_added) # dispara ao injetar nova tarefa
        self.page_tasks.task_properties_changed.connect(self.apply_task_properties_change) # dispara ao editar propriedades da tarefa
        self.page_config.emit_config_changed() # força a emissao da config inicial pra sincronizar tudo

    # desenha a estrutura visual com menus topo e painel central
    def init_hud_ui(self): 
        central_widget = QWidget() # widget central container da janela
        self.setCentralWidget(central_widget) 
        main_layout = QVBoxLayout(central_widget) # layout vertical principal
        main_layout.setContentsMargins(0, 0, 0, 0) # remove margens externas
        main_layout.setSpacing(0) # zera espacamento entre blocos

        top_hud = QFrame() # barra superior de titulo e controles
        top_hud.setStyleSheet("background-color: #2D2D30; color: white;")
        top_hud_layout = QHBoxLayout(top_hud) # layout horizontal da barra superior
        top_hud_layout.setContentsMargins(15, 8, 15, 8) # margens da barra superior

        lbl_logo = QLabel("<b>SIMULADOR SO</b>") 
        lbl_logo.setStyleSheet("font-size: 14px; color: #007ACC;") 

        self.lbl_page_title = QLabel("Configuração do Sistema") # titulo dinamico da pagina atual, começa na de config por que é onde abre o simulador
        self.lbl_page_title.setAlignment(Qt.AlignCenter)
        self.lbl_page_title.setStyleSheet("font-size: 15px; font-weight: bold;") 

        ctrl_layout = QHBoxLayout() # layout horizontal pros botoes de controle do tempo
        self.btn_step_back = QPushButton("⏮ Voltar") # botao de voltar tick
        self.btn_play_pause = QPushButton("▶ Play") # botao de dar play ou pause
        self.btn_step_fwd = QPushButton("⏭ Avançar") # botao de avancar tick
        self.btn_reset = QPushButton("🔄 Reiniciar") # botao de resetar simulacao

        # aplica estilo vizual nos botões
        for btn in [self.btn_step_back, self.btn_play_pause, self.btn_step_fwd, self.btn_reset]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3E3E42; color: white; border: none; padding: 5px 12px; border-radius: 3px; font-weight: bold;
                }
                QPushButton:hover { background-color: #505054; }
            """)
            ctrl_layout.addWidget(btn) # adiciona o botao no layout dos controles

        # conecta os cliques dos botoes aos metodos correspondentes
        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        self.btn_step_fwd.clicked.connect(self.manual_step_forward)
        self.btn_step_back.clicked.connect(self.manual_step_back)
        self.btn_reset.clicked.connect(self.reset_simulation)

        top_hud_layout.addWidget(lbl_logo) 
        top_hud_layout.addStretch(1) # espacador flexivel
        top_hud_layout.addWidget(self.lbl_page_title) 
        top_hud_layout.addStretch(1) 
        top_hud_layout.addLayout(ctrl_layout) 

        main_layout.addWidget(top_hud) # adiciona a barra do topo no layout principal

        body_layout = QHBoxLayout() # layout do corpo dividindo menu lateral e conteudo
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = QFrame() # painel lateral de navegacao entre páginas
        sidebar.setFixedWidth(160) # largura fixa do menu lateral e linha de baixo são as configs visuais
        sidebar.setStyleSheet("""
            QFrame { background-color: #252526; border-right: 1px solid #3F3F46; }
            QPushButton {
                background-color: transparent; color: #CCCCCC; text-align: left;
                padding: 12px 15px; border: none; font-size: 13px;
            }
            QPushButton:hover { background-color: #3E3E42; color: white; }
            QPushButton:checked { background-color: #094771; color: white; font-weight: bold; }
        """) 
        sidebar_layout = QVBoxLayout(sidebar) # layout vertical dos botoes de navegacao
        sidebar_layout.setContentsMargins(0, 10, 0, 10)
        sidebar_layout.setSpacing(2)

        btn_nav_config = QPushButton("⚙️ Configuração") # botao pra ir pra tela de config
        btn_nav_cpus = QPushButton("💻 CPUs / Estado") # botao pra ir pra tela de cpus
        btn_nav_tasks = QPushButton("📋 Tarefas (TCB)") # botao pra ir pra tela de tarefas
        btn_nav_gantt = QPushButton("📊 Diag. Gantt") # botao pra ir pro grafico de gantt

        # marca os botoes como alternaveis pra manter o destaque do ativo
        for b in [btn_nav_config, btn_nav_cpus, btn_nav_tasks, btn_nav_gantt]:
            b.setCheckable(True)

        btn_nav_config.setChecked(True) # marca navegacao de config como selecionada por padrao

        sidebar_layout.addWidget(btn_nav_config) # adiciona os botoes na barra lateral
        sidebar_layout.addWidget(btn_nav_cpus)
        sidebar_layout.addWidget(btn_nav_tasks)
        sidebar_layout.addWidget(btn_nav_gantt)
        sidebar_layout.addStretch(1) # empurra os botoes pro topo do menu

        body_layout.addWidget(sidebar) # adiciona o menu lateral no corpo

        self.stacked_widget = QStackedWidget() # container que alterna entre as paginas

        self.page_config = ConfigPage() # instancia pagina de configuracoes
        self.page_cpus = CPUsPage() # instancia pagina de monitoramento de cpus
        self.page_tasks = TasksPage() # instancia pagina de gerenciamento de tarefas
        self.page_gantt = GanttPage() # instancia pagina do diagrama de gantt

        # empilha as 4 telas no container principal
        self.stacked_widget.addWidget(self.page_config)
        self.stacked_widget.addWidget(self.page_cpus)
        self.stacked_widget.addWidget(self.page_tasks)
        self.stacked_widget.addWidget(self.page_gantt)

        body_layout.addWidget(self.stacked_widget, 1) # adiciona as paginas esticando no corpo
        main_layout.addLayout(body_layout, 1) # adiciona o corpo no layout principal

        # conecta os botoes de navegacao pras mudancas de tela correspondentes
        btn_nav_config.clicked.connect(lambda: self.switch_page(0, "Configuração do Sistema", btn_nav_config))
        btn_nav_cpus.clicked.connect(lambda: self.switch_page(1, "Monitor de Processadores (CPUs)", btn_nav_cpus))
        btn_nav_tasks.clicked.connect(lambda: self.switch_page(2, "Gerenciador de Tarefas (TCB)", btn_nav_tasks))
        btn_nav_gantt.clicked.connect(lambda: self.switch_page(3, "Diagrama de Gantt", btn_nav_gantt))

        self.nav_buttons = [btn_nav_config, btn_nav_cpus, btn_nav_tasks, btn_nav_gantt] # guarda a lista de botoes do menu

        bottom_hud = QFrame() # barra inferior do rodape
        bottom_hud.setStyleSheet("background-color: #007ACC; color: white;") # estilo azul do rodape
        bottom_hud_layout = QHBoxLayout(bottom_hud) # layout horizontal do rodape
        bottom_hud_layout.setContentsMargins(15, 4, 15, 4)

        self.lbl_status_bar = QLabel("Sistema Pronto") # texto de status do sistema no rodape
        self.lbl_timer = QLabel("RELÓGIO GLOBAL (TICK): 0000") # contador visual de ticks no rodape
        self.lbl_timer.setStyleSheet("font-weight: bold; font-family: monospace;") 

        bottom_hud_layout.addWidget(self.lbl_status_bar) # bota texto de status na esquerda
        bottom_hud_layout.addStretch(1) # espacador flexivel
        bottom_hud_layout.addWidget(self.lbl_timer) # bota relogio na direita

        main_layout.addWidget(bottom_hud) # adiciona a barra do rodape no layout principal

    # método que aplica alteracao manual de estado de tarefa
    #recebe o id da task que será alterada e o seu novo estado
    def apply_manual_task_state(self, task_id: str, new_state: str): 
        self.pause_simulation() # pausa o tempo pra aplicar a mudanca
        self.engine.modify_task_state_manually(task_id, new_state) # chama função que faz alteração por meio da instancia do motor
        self.render_engine_state(self.engine.get_current_state()) # redesenha as telas com o novo estado
        self.lbl_status_bar.setText(f"Ação Manual: Tarefa {task_id} alterada para {new_state}.") # atualiza status no rodape

    # processa a injecao de uma nova tarefa em tempo de execucao
    #recebe como entrada o dicionário do estado da simulação contendo as infos como lista de tarefas, num de cpus, ...
    def on_dynamic_task_added(self, task_data: dict): 
        self.pause_simulation() # pausa o tempo antes de alterar
        success, msg, _ = self.engine.add_task_dynamically(task_data) # tenta cadastrar a tarefa no motor
        
        self.render_engine_state(self.engine.get_current_state()) # redesenha todas as telas
        log_level = "SUCCESS" if success else "ERROR" # define tipo do log de acordo com sucesso ou erro
        self.page_config.log_message(msg, log_level) # escreve o resultado no console da pagina de config
        self.lbl_status_bar.setText(msg) # atualiza a mensagem no rodape
        
        if not success: # se o motor rejeitar a tarefa por regra do escalonador
            QMessageBox.warning(self, "Injeção Rejeitada", msg, QMessageBox.Ok) # mostra popup de alerta do erro

    # método que altera duracao periodo ou prazo da tarefa
    def apply_task_properties_change(self, old_task_id: str, new_params: dict): 
        self.pause_simulation() # pausa a simulacao
        success, msg = self.engine.update_task_properties_manually(old_task_id, new_params) # aplica alteracao através do motor
        
        self.render_engine_state(self.engine.get_current_state()) # redesenha as paginas
        log_level = "SUCCESS" if success else "ERROR"
        self.page_config.log_message(msg, log_level) # registra log de sucesso ou erro
        self.lbl_status_bar.setText(msg) # exibe mensagem no rodape
        
        if not success: # se violar regras de prazo ou duracao
            QMessageBox.warning(self, "Alteração Rejeitada", msg, QMessageBox.Ok) # avisa popup de erro

    # método que atualiza o backend quando o usuario altera configuracoes
    #recebe como entrada o dicionário do estado da simulação contendo as infos como lista de tarefas, num de cpus, ...
    def on_config_changed(self, config_data: dict): 
        self.current_config = config_data # salva a configuracao nova
        new_cpu_count = config_data.get("cpus", 1) # extrai quantidade de cpus desejadas
        
        if self.engine.cpus and len(self.engine.cpus) != new_cpu_count and self.engine.current_tick > 0: # se o simulador ja ta rodando e so mudou cpus
            self.engine.set_cpu_count(new_cpu_count) # ajusta a quantidade de cpus sem perder o tick atual
        else: # se trocou algoritmo ou ta no inicio
            self.pause_simulation() # pausa tempo
            self.engine.init_from_config(config_data) # reinicia o motor do zero com as novas configs, assim impede que rode 3 ticks mude o alg e de bug
            
        self.render_engine_state(self.engine.get_current_state()) # redesenha as telas

    # método que atualiza simultaneamente todas as abas da interface
    #recebe como entrada o dicionário do estado da simulação contendo as infos como lista de tarefas, num de cpus, ...
    def render_engine_state(self, state: dict): 
        self.page_cpus.render_state(state) 
        self.page_tasks.render_state(state) 
        self.page_config.render_state(state) 
        self.page_gantt.render_state(state) 
        self.lbl_timer.setText(f"RELÓGIO GLOBAL (TICK): {state['tick']:04d}") # atualiza relogio com 4 digitos
        
        # atualiza resumo de cpus tarefas e algoritmo ativo no rodape
        self.lbl_status_bar.setText( 
            f"Configuração Ativa: {len(state['cpus'])} CPU(s) | {len(state['tcbs'])} Tarefas [{state['algorithm']}]"
        )

    def advance_tick(self): # avanca um ciclo de relogio no motor
        state = self.engine.step_forward() # executa proximo tick na simulação
        self.render_engine_state(state) # redesenha na tela

     # método do passo a passo pra frente disparado pelo botao de avancar
    def manual_step_forward(self):
        self.pause_simulation() 
        self.advance_tick() 

    # passo a passo pra tras disparado pelo botao de voltar
    def manual_step_back(self): 
        self.pause_simulation()
        state = self.engine.step_back() 
        self.render_engine_state(state) 

    # método que reseta a simulacao pro tick inicial
    def reset_simulation(self): 
        self.pause_simulation()
        self.engine.reset() # restaura motor pro estado zero
        self.render_engine_state(self.engine.get_current_state()) # atualiza interface zerada

    # alterna entre rodar e pausar a simulacao
    def toggle_play_pause(self): 
        if self.is_running: 
            self.pause_simulation()
        else:
            self.start_simulation() 

    # método que  inicia a simulacao de acordo com o modo escolhido
    def start_simulation(self): 
        modo_execucao = self.current_config.get("mode", "STEP") # pega o modo selecionado
        
        if modo_execucao == "FULL": 
            self.lbl_status_bar.setText("Processando Execução Completa...") 
            estado_final = self.engine.run_full_simulation() # processa todos os ticks de uma vez no motor
            self.render_engine_state(estado_final) # exibe o resultado final de uma vez
            self.lbl_status_bar.setText("Simulação Completa Finalizada!")
        else: 
            self.is_running = True # marca estado como executando
            self.btn_play_pause.setText("⏸ Pause") # muda texto do botao pra pause
            self.btn_play_pause.setStyleSheet("""
                QPushButton { background-color: #D35400; color: white; border: none; padding: 5px 12px; border-radius: 3px; font-weight: bold; }
                QPushButton:hover { background-color: #E67E22; }
            """) 
            self.lbl_status_bar.setText("Simulação em Execução Automática...") 
            self.timer.start() # liga o temporizador pra avancar os ticks sozinhos

    # método que para a simulacao
    def pause_simulation(self): 
        self.is_running = False # marca estado como parado
        self.timer.stop() # desliga o temporizador
        self.btn_play_pause.setText("▶ Play") # restaura texto do botao pra play
        self.btn_play_pause.setStyleSheet("""
            QPushButton { background-color: #3E3E42; color: white; border: none; padding: 5px 12px; border-radius: 3px; font-weight: bold; }
            QPushButton:hover { background-color: #505054; }
        """)

    # método que troca a tela visivel e marca o botao do menu
    # recebe como entrada o botã clicado, o indice e o título da pg
    def switch_page(self, index: int, title: str, active_btn: QPushButton): 
        self.stacked_widget.setCurrentIndex(index) # troca indice no container de telas
        self.lbl_page_title.setText(title) # atualiza titulo no topo da janela
        for btn in self.nav_buttons: # marca apenas o botao clicado como ativo no menu
            btn.setChecked(btn == active_btn)

# ponto de entrada padrao do programa
if __name__ == "__main__": 
    app = QApplication(sys.argv) # cria instancia da aplicacao qt
    window = MainWindow() # cria a janela principal
    window.show() # exibe a janela na tela
    sys.exit(app.exec()) # inicia o loop de eventos do qt, termina quando fecha a janela