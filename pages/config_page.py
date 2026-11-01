import os 
from PySide6.QtWidgets import ( 
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QSpinBox, QRadioButton, QFileDialog, QTableWidget, 
    QTableWidgetItem, QHeaderView, QTextEdit, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor 


class ConfigPage(QWidget): 
    """página de configuração"""
    
    # sinal emitido sempre que qualquer configuração/ficheiro mudar
    config_changed = Signal(dict) # sinal que avisa quando muda alguma config repassando o dicionario

    def __init__(self, parent=None): 
        super().__init__(parent) 
        self.current_file_path = None # guarda o caminho do arquivo aberto
        self.tasks_data = [] # lista com as tarefas
        self.init_ui() # monta a interface grafica
        self.connect_signals() # conecta os cliques e mudancas nos campos aos metodos
        self.load_default_config() # carrega as configuracoes padrao inicial

    def init_ui(self):
        main_layout = QVBoxLayout(self) # layout vertical principal
        main_layout.setSpacing(12) # espacamento interno entre blocos
        main_layout.setContentsMargins(15, 15, 15, 15) # margem das bordas da tela

        #bloco da config
        file_box = QGroupBox("Arquivo de Configuração") # caixinha de agrupamento de arquivo
        file_layout = QHBoxLayout(file_box) # layout horizontal interno da caixa de arquivo

        self.lbl_file_status = QLabel("Arquivo Atual: Configuração Padrão (Sistema)") # texto mostrando o arquivo atual
        self.lbl_file_status.setStyleSheet("font-weight: bold; color: #2B579A;") # estilo em negrito e azul

        btn_load_file = QPushButton("📁 Carregar Arquivo (.txt)") # botao pra buscar arquivo txt
        btn_load_file.clicked.connect(self.select_file) # conecta a função que executa a funcionalidade

        btn_restore_default = QPushButton("🔄 Restaurar Padrões") # botao de resetar pra padrao
        btn_restore_default.clicked.connect(self.load_default_config) # conecta clique pra restaurar padrão

        # adiciona os componentes visuais ao layout
        file_layout.addWidget(self.lbl_file_status, 1) 
        file_layout.addWidget(btn_load_file) 
        file_layout.addWidget(btn_restore_default) 
        main_layout.addWidget(file_box) 

        # visualização dos parâmetros gerais do sistema
        params_box = QGroupBox("Parâmetros Gerais do Sistema Operacional") 
        params_layout = QHBoxLayout(params_box) # layout horizontal dos parametros

        params_layout.addWidget(QLabel("Algoritmo:")) 
        self.combo_algorithm = QComboBox() # menu suspenso de algoritmos
        self.combo_algorithm.addItems(["RM (Rate Monotonic)", "EDF (Earliest Deadline First)"]) # adiciona opcoes rm e edf
        params_layout.addWidget(self.combo_algorithm) # bota menu suspenso no layout

        params_layout.addWidget(QLabel("Quantum (ticks):"))
        self.spin_quantum = QSpinBox() 
        self.spin_quantum.setRange(1, 100) # limita de 1 a 100
        self.spin_quantum.setValue(1) # valor inicial padrao 1
        params_layout.addWidget(self.spin_quantum) # bota campo de quantum no layout

        params_layout.addWidget(QLabel("Qtd. CPUs:"))
        self.spin_cpus = QSpinBox() 
        self.spin_cpus.setRange(1, 64) # limita de 1 a 64
        self.spin_cpus.setValue(2) # valor inicial padrao 2
        params_layout.addWidget(self.spin_cpus) # bota campo de cpus no layout

        params_layout.addWidget(QLabel("Modo:")) 
        self.radio_step = QRadioButton("Passo a Passo (Debugger)") # botao de passo a passo
        self.radio_full = QRadioButton("Execução Completa") # botao de execucao direta
        self.radio_step.setChecked(True) # marca passo a passo por padrao
        params_layout.addWidget(self.radio_step) # adiciona opcao passo a passo
        params_layout.addWidget(self.radio_full) # adiciona opcao execucao completa

        main_layout.addWidget(params_box) # adiciona caixa de parametros no layout principal

        # tabela de tarefas e logs
        splitter = QSplitter(Qt.Vertical) # divisor ajustavel na vertical

        # tabela de visualização básica
        tasks_widget = QWidget() # container da tabela de tarefas
        tasks_layout = QVBoxLayout(tasks_widget) # layout vertical do container
        tasks_layout.setContentsMargins(0, 0, 0, 0) # limpa margens do container
        
        lbl_tasks_title = QLabel("Resumo das Tarefas Carregadas") 
        lbl_tasks_title.setStyleSheet("font-weight: bold;") 
        tasks_layout.addWidget(lbl_tasks_title) 

        self.table_tasks = QTableWidget() 
        self.table_tasks.setColumnCount(7) # define 7 colunas padrões, que serão as infos das tasks passadas pelo arquivo de config
        self.table_tasks.setHorizontalHeaderLabels([ 
            "ID", "Cor (RGB Hex)", "Ingresso", "Duração", "Período", "Prazo (Deadline)", "Eventos"
        ])
        self.table_tasks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # ajusta largura das colunas
        self.table_tasks.setEditTriggers(QTableWidget.NoEditTriggers) # impede edicao manual nas celulas
        tasks_layout.addWidget(self.table_tasks)

        splitter.addWidget(tasks_widget) # adiciona parte da tabela no divisor

        # console de Logs
        log_widget = QWidget() # container do console de logs
        log_layout = QVBoxLayout(log_widget) # layout vertical do console
        log_layout.setContentsMargins(0, 0, 0, 0) # limpa margens

        lbl_log_title = QLabel("Console de Status, Validações e Erros de Carregamento")
        lbl_log_title.setStyleSheet("font-weight: bold;") 
        log_layout.addWidget(lbl_log_title) 

        self.txt_logs = QTextEdit() # caixa de texto pros logs
        self.txt_logs.setReadOnly(True) # trava pra apenas leitura
        self.txt_logs.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E; color: #D4D4D4;
                font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;
                border: 1px solid #3C3C3C;
            }
        """) 
        log_layout.addWidget(self.txt_logs) 

        splitter.addWidget(log_widget) # adiciona parte de logs no divisor
        splitter.setSizes([200, 150]) # define proporcao inicial entre tabela e logs

        main_layout.addWidget(splitter, 1) # coloca o divisor no layout principal esticando

    #método que conecta alteracoes da tela pra avisar o resto do sistema
    def connect_signals(self): 
        self.spin_cpus.valueChanged.connect(self.emit_config_changed) # dispara quando muda cpus
        self.combo_algorithm.currentIndexChanged.connect(self.emit_config_changed) # dispara quando muda algoritmo
        self.spin_quantum.valueChanged.connect(self.emit_config_changed) # dispara quando muda quantum
        self.radio_step.toggled.connect(self.emit_config_changed) # dispara quando troca o modo

    # método que pega as configs e manda no sinal
    def emit_config_changed(self): 
        config_data = { 
            "cpus": self.spin_cpus.value(), 
            "algorithm": self.combo_algorithm.currentText(), 
            "quantum": self.spin_quantum.value(), 
            "mode": "STEP" if self.radio_step.isChecked() else "FULL", 
            "tasks": self.tasks_data 
        }
        self.config_changed.emit(config_data) # emite sinal repassando o dicionario

    # dispara linhas formatadas no console de logs, recebe como entrada um str indicando que tipo de log é e o próprio log
    def log_message(self, message: str, level: str = "INFO"): 
        # cores pra cada tipo de log
        colors = { 
            "SUCCESS": "#4EC9B0", "INFO": "#9CDCFE",
            "WARNING": "#CE9178", "ERROR": "#F44747"
        }
        color_hex = colors.get(level.upper(), "#D4D4D4") # escolhe a cor ou usa cinza padrao
        prefix = f"[{level.upper()}]" # cria a tag de prefixo para ficar bonito tipo: [INFO], [ERROR], [WARNING]
        formatted_html = f'<span style="color: {color_hex}; font-weight: bold;">{prefix}</span> <span style="color: #D4D4D4;">{message}</span><br>' # monta html colorido
        self.txt_logs.append(formatted_html) # imprime a linha no console
    
    # método que carrega as configuracoes padrao iniciais
    def load_default_config(self): 
        self.current_file_path = None # limpa arquivo selecionado
        self.lbl_file_status.setText("Arquivo Atual: Configuração Padrão (Sistema)") # reseta texto de status
        self.txt_logs.clear() # limpa logs antigos
        self.log_message("Restaurando configuração inicial padrão...", "INFO") # grava aviso no log

        default_text = """RM; 1; 2
T1; FF5733; 0; 2; 10; 6; -
T2; 33FF57; 0; 2; 10; 8; -
T3; 3357FF; 0; 8; 20; 16; -""" # texto base com config padrao

        self.parse_config_text(default_text, source_name="Configuração Padrão") # processa o texto padrao

    # abre janela pro usuario escolher arquivo no pc
    def select_file(self): 
        file_path, _ = QFileDialog.getOpenFileName( # abre dialogo de arquivos
            self, "Selecionar Arquivo de Configuração", "", "Arquivos de Texto (*.txt);;Todos os Arquivos (*)"
        )
        if file_path: # se o usuario escolheu algum arquivo
            self.load_file_from_path(file_path) # carrega o arquivo do caminho escolhido

    def load_file_from_path(self, path: str): # le o arquivo do disco
        self.txt_logs.clear() # limpa historico de logs
        self.log_message(f"Tentando carregar arquivo: {path}", "INFO") # loga tentativa

        try:
            if not os.path.exists(path): # se arquivo nao existir
                raise FileNotFoundError("O arquivo especificado não foi encontrado.") # dispara erro

            with open(path, 'r', encoding='utf-8') as f: # abre arquivo pra leitura
                content = f.read() # le todo texto do arquivo

            self.current_file_path = path # salva o caminho lido
            self.lbl_file_status.setText(f"Arquivo Atual: {os.path.basename(path)}") # atualiza nome na tela
            self.parse_config_text(content, source_name=os.path.basename(path)) # chama função que processa o conteudo lido

        except PermissionError: # se nao tiver permissao
            self.log_message(f"Erro de Permissão: O aplicativo não possui acesso de leitura para '{path}'.", "ERROR")
        except Exception as e: # se der qualquer outro erro
            self.log_message(f"Falha ao carregar arquivo: {str(e)}", "ERROR")

    # função que processa o texto de configuração, recebe como entrada o conteudo do arquivo e o path
    def parse_config_text(self, text: str, source_name: str):  
        lines = [line.strip() for line in text.splitlines() if line.strip()] # divide por linhas e remove vazias

        if not lines: # se tiver vazio
            self.log_message("Erro: O arquivo de configuração está vazio.", "ERROR") # avisa erro no log
            return

        
        if len(lines) < 2: # checa se tem menos de 2 linhas, se não tiver não tem tarrefas gera erro (requisito 3.3.1)
            self.log_message("Erro: O arquivo de configuração deve ter PELO MENOS 2 LINHAS (Linha 1: Parâmetros do SO, Linhas seguintes: Tarefas).", "ERROR") 
            return

        line_1 = lines[0].rstrip(';') # pega primeira linha e tira ponto e virgula final caso tenha
        parts_1 = [p.strip() for p in line_1.split(';')] # separa partes por ponto e virgula

        if len(parts_1) < 3: # se faltar parametro na linha 1
            self.log_message("Erro na Linha 1: Parâmetros globais incompletos. Esperado 'algoritmo; quantum; cpus'.", "ERROR") 
            return

        self.spin_cpus.blockSignals(True) # trava sinais pra nao disparar eventos no preenchimento
        self.combo_algorithm.blockSignals(True) # trava sinais do algoritmo
        self.spin_quantum.blockSignals(True) # trava sinais do quantum

        algo_raw, quantum_raw, cpus_raw = parts_1[0], parts_1[1], parts_1[2] # pega as tres configs da linha 1

        if "RM" in algo_raw.upper(): # se for rm
            self.combo_algorithm.setCurrentIndex(0) # seleciona rm
        elif "EDF" in algo_raw.upper(): # se for edf
            self.combo_algorithm.setCurrentIndex(1) # seleciona edf
        else: # se for algo invalido
            self.log_message(f"Aviso: Algoritmo '{algo_raw}' desconhecido. Assumindo RM por padrão.", "WARNING") # avisa e assume rm
            self.combo_algorithm.setCurrentIndex(0)

        try:
            val_quantum = int(quantum_raw) # converte quantum pra inteiro
            if val_quantum < 1: # se for menor que 1
                self.log_message(f"Aviso: Quantum ({val_quantum}) deve ser >= 1. Ajustado para 1.", "WARNING") # ajusta pra 1
                val_quantum = 1
            self.spin_quantum.setValue(val_quantum) # ajusta valor no campo

            val_cpus = int(cpus_raw) # converte cpus pra inteiro
            if val_cpus < 1: # se for menor que 1
                self.log_message(f"Aviso: Quantidade de CPUs ({val_cpus}) deve ser >= 1. Ajustado para 1 CPU.", "WARNING") # ajusta pra 1
                val_cpus = 1
            self.spin_cpus.setValue(val_cpus) # ajusta valor no campo

        except ValueError: # se falhar ao converter numero
            self.log_message("Erro na Linha 1: Quantum ou CPUs não correspondem a valores numéricos válidos.", "ERROR") 
            self.spin_cpus.blockSignals(False) # destrava sinais antes de sair
            self.combo_algorithm.blockSignals(False)
            self.spin_quantum.blockSignals(False)
            return

        self.spin_cpus.blockSignals(False) # destrava sinais das cpus
        self.combo_algorithm.blockSignals(False) # destrava sinais do algoritmo
        self.spin_quantum.blockSignals(False) # destrava sinais do quantum

        parsed_tasks = [] # lista de tarefas interpretadas com sucesso
        ignored_aperiodic_count = 0 # contador de aperiodicas ignoradas
        error_count = 0 # contador de erros de tarefas

        for line_num, line in enumerate(lines[1:], start=2): # percorre da segunda linha em diante
            clean_line = line.rstrip(';') # limpa ponto e virgula no final
            parts = [p.strip() for p in clean_line.split(';')] # separa campos da tarefa

            if len(parts) < 6: # se faltar campos na tarefa
                self.log_message(f"Aviso [Linha {line_num}]: Formato inválido (menos de 6 campos). Linha ignorada: '{line}'", "WARNING") # avisa formato ruim
                error_count += 1 # conta erro
                continue # pula pra proxima linha

            t_id, t_color = parts[0], parts[1] # extrai id e cor

            # valida se a cor fornecida no arquivo é válida
            if not QColor(f"#{t_color.lstrip('#')}").isValid():
                self.log_message(f"Erro [Linha {line_num}]: A cor '{t_color}' da tarefa '{t_id}' é inválida. Tarefa ignorada.", "ERROR")
                error_count += 1
                continue

            try:
                t_ingresso, t_duracao = int(parts[2]), int(parts[3]) # converte ingresso e duracao
                t_periodo, t_prazo = int(parts[4]), int(parts[5]) # converte periodo e prazo
                t_eventos = parts[6] if len(parts) > 6 else "-" # pega eventos se houver ou bota hifen, no caso ainda não temos né
            except ValueError: # se falhar ao converter inteiros
                self.log_message(f"Erro [Linha {line_num}]: Parâmetros numéricos inválidos na tarefa '{t_id}'.", "ERROR") # loga erro
                error_count += 1
                continue

            if t_periodo == 0: # se periodo for zero é aperiodica
                ignored_aperiodic_count += 1 # incrementa contagem
                self.log_message(f"Aviso: A tarefa '{t_id}' é Aperiódica (Período: 0) e foi IGNORADA.", "WARNING") # loga aviso que ignorou
                continue
            elif t_periodo < 0: # se periodo for negativo
                error_count += 1 # incrementa erros
                self.log_message(f"Erro [Linha {line_num}]: Período negativo ({t_periodo}) na tarefa '{t_id}' é inválido.", "ERROR") 
                continue

            parsed_tasks.append({ # adiciona tarefa validada na lista
                "id": t_id, "color": t_color, "ingresso": t_ingresso,
                "duracao": t_duracao, "periodo": t_periodo, "prazo": t_prazo, "eventos": t_eventos
            })

        self.tasks_data = parsed_tasks # guarda tarefas processadas na classe
        self.update_tasks_table() # atualiza a tabela da tela com as tarefas

        if len(self.tasks_data) == 0: # se nao carregou nenhuma tarefa
            self.log_message("Aviso: Nenhuma tarefa válida foi encontrada/carregada do arquivo.", "WARNING")
        else:
            self.log_message(f"Sucesso: Configuração de '{source_name}' carregada com sucesso!", "SUCCESS") 
            self.log_message(f"Resumo: {len(self.tasks_data)} tarefas periódicas ativas carregadas.", "INFO") # resumo de contagem

        if ignored_aperiodic_count > 0: # se teve aperiodicas ignoradas
            self.log_message(f"Nota: Total de {ignored_aperiodic_count} tarefa(s) aperiódica(s) desconsiderada(s).", "WARNING") # da o log do total delas

        self.emit_config_changed() # avisa o sistema que a config mudou

    # método que atualiza tela com informacoes que vem do motor, ou seja, de outras pgs
    # recebe como esntrada o dicionário com as informações atuais da simulação
    def render_state(self, state: dict): 
        if not state: # se o estado atual tiver vazio nao faz nada
            return

        cpus_list = state.get("cpus", []) # busca cpus no dicionario passado
        if hasattr(self, "spin_cpus") and cpus_list: # se o campo de cpus existir
            self.spin_cpus.blockSignals(True) # trava sinais
            self.spin_cpus.setValue(len(cpus_list)) # atualiza valor de cpus na tela
            self.spin_cpus.blockSignals(False) # destrava sinais

        algo = state.get("algorithm", "") # busca algoritmo no dicionario
        if hasattr(self, "combo_algorithm") and algo: # se o combo existir
            self.combo_algorithm.blockSignals(True) # trava sinais
            if "RM" in algo.upper(): # marca rm se for o caso
                self.combo_algorithm.setCurrentIndex(0)
            elif "EDF" in algo.upper(): # marca edf se for o caso
                self.combo_algorithm.setCurrentIndex(1)
            self.combo_algorithm.blockSignals(False) # destrava sinais

        quantum = state.get("quantum") # busca quantum no dicionario
        if hasattr(self, "spin_quantum") and quantum is not None: # se existir valor de quantum
            self.spin_quantum.blockSignals(True) # trava sinais
            self.spin_quantum.setValue(quantum) # atualiza campo de quantum
            self.spin_quantum.blockSignals(False) # destrava sinais

    # método que redesenha a tabela de tarefas com base na lista tasks_data
    def update_tasks_table(self): 
        self.table_tasks.setRowCount(len(self.tasks_data)) # ajusta quantidade de linhas

        # percorre as tarefas da lista preenchendo a tabela
        for row, task in enumerate(self.tasks_data): 
            self.table_tasks.setItem(row, 0, QTableWidgetItem(str(task["id"]))) # bota id na coluna 0
            
            color_hex = f"#{task['color'].lstrip('#')}" # formata string com cerquilha de cor hex
            item_color = QTableWidgetItem(color_hex) 
            item_color.setBackground(QColor(color_hex)) # pinta fundo da célula com a cor da tarefa
            item_color.setForeground(QColor("#000000" if color_hex.upper() in ["#FFFFFF", "#FFF"] else "#FFFFFF")) # ajusta texto pra preto ou branco por contraste
            
            #preenche cada célula da coluna com sua respectiva informação
            self.table_tasks.setItem(row, 1, item_color) 
            self.table_tasks.setItem(row, 2, QTableWidgetItem(str(task["ingresso"]))) 
            self.table_tasks.setItem(row, 3, QTableWidgetItem(str(task["duracao"]))) 
            self.table_tasks.setItem(row, 4, QTableWidgetItem(str(task["periodo"])))
            self.table_tasks.setItem(row, 5, QTableWidgetItem(str(task["prazo"]))) 
            self.table_tasks.setItem(row, 6, QTableWidgetItem(str(task["eventos"]))) 