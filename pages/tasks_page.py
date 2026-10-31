from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
    QPushButton, QLineEdit, QSpinBox
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from core.tcb import TaskControlBlock


class TasksPage(QWidget):
    """página de gerenciamento, exibição, criação e edição de tarefas """

    # sinal que carrega 2 strings e é ativo quando o usuário muda o estado de um task
    manual_state_change = Signal(str, str) #str1 = id e str2 = novo estado 
    add_task_requested = Signal(dict)  # sinal, ativa ao clicar o botão de adicionar tarefa, passo o dicionário de info da nova task
    # sinal ativo quando muda o estado de uma tarefa
    task_properties_changed = Signal(str, dict)   #str1 = id, e dicionário de infos da tarefa


    def __init__(self, parent=None):
        super().__init__(parent)
        self.dynamic_task_count = 1  #serve para controle interno do número de id das tasks
        self.current_tcbs: List[TaskControlBlock] = []#cria lista de tcbs vazia
        self.init_ui()#chama o método que faz a montagem da interface visualmente 

    # método que faz a contrução dos elementos visuais da página
    def init_ui(self):
        #define um layout vertical e associa ele a tela, definindo o espaçamento externo de 15 pixels nas bordas
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)#espaçamento entre elementos

        # cria um quadro contornado com título na borda superior
        tcb_box = QGroupBox("Blocos de Controle de Tarefa (TCB)")
        tcb_layout = QVBoxLayout(tcb_box)#define o layout interno do tcb_box

        #cria tabela interativa, reserva 9 colunas, uma pra cada informação da tcb
        self.table_tcb = QTableWidget()
        self.table_tcb.setColumnCount(9)
        self.table_tcb.setHorizontalHeaderLabels([
            "ID", "Estado Atual", "CPU", "Ingresso", "Duração Restante",
            "Período", "Próximo Release", "Prazo Absoluto", "Execuções"
        ])
        #faz com que as colunas 9 colunas ajustem o tamanho automaticamente pra não ficar feio
        self.table_tcb.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) 
        tcb_layout.addWidget(self.table_tcb)
        layout.addWidget(tcb_box, 1)#insere no tcb_box

        # layout de inserir tarefa em tempo de execução
        #cria uma caixa de agrupamento visual com o título e bota o layout interno como horizontal
        add_box = QGroupBox("➕ Injetar Nova Tarefa em Tempo de Execução")
        add_layout = QHBoxLayout(add_box)

        #campo para selecionar o id das tarefas existentes, começa na t1 por padrã e tem tamanho visual de 50 pixels, fixo
        add_layout.addWidget(QLabel("ID:"))
        self.txt_id = QLineEdit("TD1")
        self.txt_id.setFixedWidth(50)
        add_layout.addWidget(self.txt_id)

        #campo de duração com alcance entre -10 e 100 (obs: daria pra colocar 0 como limite inferior, mas deixamos para demonstrar avisos visuais)
        add_layout.addWidget(QLabel("Duração:"))
        self.spin_duracao = QSpinBox()
        self.spin_duracao.setRange(-10, 100)  
        self.spin_duracao.setValue(2)#valor padrão inicial
        add_layout.addWidget(self.spin_duracao)

        #campo de período com alcance entre -10 e 100 (obs: daria pra colocar 0 como limite inferior, mas deixamos para demonstrar avisos visuais)
        add_layout.addWidget(QLabel("Período:"))
        self.spin_periodo = QSpinBox()
        self.spin_periodo.setRange(-10, 200)  # Permite <= 0 para testar a rejeição
        self.spin_periodo.setValue(10)
        add_layout.addWidget(self.spin_periodo)

        add_layout.addWidget(QLabel("Prazo:"))
        self.spin_prazo = QSpinBox()
        self.spin_prazo.setRange(-10, 200) 
        self.spin_prazo.setValue(4)#valor padrão inicial
        add_layout.addWidget(self.spin_prazo)
        
        #campo da cor
        add_layout.addWidget(QLabel("Cor (Hex):"))
        self.txt_color = QLineEdit("E74C3C")#valor padrão inicial
        self.txt_color.setFixedWidth(65)#tamanho fixo do elemento viusal
        add_layout.addWidget(self.txt_color)

        #botão que salva a tarefa nova, com titulozinho, conecta a função que executa sua funcionalidade
        btn_add = QPushButton("Injetar Tarefa")
        btn_add.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; padding: 5px 10px;")
        btn_add.clicked.connect(self.on_add_task_clicked)
        add_layout.addWidget(btn_add)
        layout.addWidget(add_box)

        #cria uma caixa de agrupamento visual com o título e bota o layout interno como horizontal
        edit_box = QGroupBox("Alterar Características da Tarefa")
        edit_layout = QHBoxLayout(edit_box)

        #menuzinho com id das tarefas existentes listados
        edit_layout.addWidget(QLabel("Selecionar Tarefa:"))
        self.combo_edit_task = QComboBox()
        self.combo_edit_task.currentIndexChanged.connect(self.on_edit_task_selected)#sempre que muda a tarefa selecionada, recarrega os outros dados
        edit_layout.addWidget(self.combo_edit_task)

        #duração da tarefa, com um limite de alteração
        edit_layout.addWidget(QLabel("Duração:"))
        self.spin_edit_duracao = QSpinBox()
        self.spin_edit_duracao.setRange(-10, 200) 
        edit_layout.addWidget(self.spin_edit_duracao)

        #periodo
        edit_layout.addWidget(QLabel("Período:"))
        self.spin_edit_periodo = QSpinBox()
        self.spin_edit_periodo.setRange(-10, 200)  
        edit_layout.addWidget(self.spin_edit_periodo)

        #prazo
        edit_layout.addWidget(QLabel("Prazo:"))
        self.spin_edit_prazo = QSpinBox()
        self.spin_edit_prazo.setRange(-10, 200)
        edit_layout.addWidget(self.spin_edit_prazo)

        #cor, com tamanho visual fixo de 65 pixels
        edit_layout.addWidget(QLabel("Cor (Hex):"))
        self.txt_edit_color = QLineEdit()
        self.txt_edit_color.setFixedWidth(65)
        edit_layout.addWidget(self.txt_edit_color)

        #botão que liga o sinal, que emite as alterações na tarefa para a função
        btn_save_edit = QPushButton("💾 Salvar Alterações")
        btn_save_edit.setStyleSheet("background-color: #D35400; color: white; font-weight: bold; padding: 5px 10px;")# define cor, fonte, ...
        btn_save_edit.clicked.connect(self.on_save_edit_clicked)#conecta o botão a função
        edit_layout.addWidget(btn_save_edit)
        layout.addWidget(edit_box)

        # layout visual painel de modificação dos estados
        debug_box = QGroupBox("Painel de Modificação Manual de Estado")
        debug_layout = QHBoxLayout(debug_box)

        #igual aos combobox dos ultimos layouts
        debug_layout.addWidget(QLabel("Selecionar Tarefa:"))
        self.combo_select_task = QComboBox()
        debug_layout.addWidget(self.combo_select_task)

        #mostra texto junto com o lugar onde seleciona o estado que se quer por na tarefa
        debug_layout.addWidget(QLabel("Novo Estado:"))
        self.combo_new_state = QComboBox()
        self.combo_new_state.addItems(["PRONTA", "SUSPENSA", "CANCELADA"])
        debug_layout.addWidget(self.combo_new_state)

        #botão que chama a função que tem essa funcionalidade implementada, definindo configs visuais
        self.btn_apply = QPushButton("✏️ Modificar Estado")
        self.btn_apply.setStyleSheet("background-color: #007ACC; color: white; font-weight: bold;")
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        debug_layout.addWidget(self.btn_apply)
        debug_layout.addStretch(1)
        layout.addWidget(debug_box)

    # método que pega os dados digitados, limpa e prepara a interface pra proxima task
    def on_add_task_clicked(self):
        #pega os valores dos dados recebidos, e limpa espaços brancos em texto, se tiver
        task_data = {
            "id": self.txt_id.text().strip() or f"TD{self.dynamic_task_count}",
            "color": self.txt_color.text().strip() or "E74C3C",
            "duracao": self.spin_duracao.value(),
            "periodo": self.spin_periodo.value(),
            "prazo": self.spin_prazo.value(),
            "eventos": "-"#por enquanto ignoramos
        }
        self.dynamic_task_count += 1 #incrementa variável interna do num de tarefas
        self.txt_id.setText(f"TD{self.dynamic_task_count}")#atualiza automaticamente a contagem do id, assim adiciono, a 1, e já atualiza pra poder adicionar a 2
        self.add_task_requested.emit(task_data)#manda as informações pro sinal que emite sinalização pro motor da sim, que instancia uma tcb nova

    #métod chamado ao selecionar uma tarefa diferente em uma combobox, que basicamente atualiza as infos com as corretas da tcb
    def on_edit_task_selected(self):
        selected_id = self.combo_edit_task.currentText()#ve o id selecionado
        tcb = next((t for t in self.current_tcbs if t.id == selected_id), None)#procura pelo id da tcb na lista
        if tcb:#se achar preenche os campos corretamente
            self.txt_edit_color.setText(tcb.color)
            self.spin_edit_duracao.setValue(tcb.duracao_total)
            self.spin_edit_periodo.setValue(tcb.periodo)
            self.spin_edit_prazo.setValue(tcb.prazo_relativo)

    #método acionado ao salvar alterações, pega as informações novas e envia ao motor pelo sinal task_properties_changed
    def on_save_edit_clicked(self):
        #pega o id atual na combo box, se estiver vazio retorna
        task_id = self.combo_edit_task.currentText()
        if not task_id:
            return
        
        #novos parametros colocados pelo usuário na interface
        new_params = {
            "color": self.txt_edit_color.text().strip(),
            "duracao": self.spin_edit_duracao.value(),
            "periodo": self.spin_edit_periodo.value(),
            "prazo": self.spin_edit_prazo.value()
        }
        #emite sinal pro motor, passando id e os parametros novos
        self.task_properties_changed.emit(task_id, new_params)

    #ativado quando muda o estado da tarefa, e basicamente pega o estado selecionado pra task selecionada e emite um sinal com essas infos pro motor
    def on_apply_clicked(self):
        task_id = self.combo_select_task.currentText()
        new_state = self.combo_new_state.currentText()
        if task_id and new_state:
            self.manual_state_change.emit(task_id, new_state)

    #método que atualiza a interface da tabela a cada tick, preservando alterações feitas pelo usuário
    #suas entradas são a instancia da classe, e as informações do tick atual por meio do dicionário
    def render_state(self, state: Dict[str, Any]):
        #pega lista de tcbs, se não tiver retorna lista vazia
        tcbs: List[TaskControlBlock] = state.get("tcbs", [])
        self.current_tcbs = tcbs 
        #define o número de linhas da tabela com base no numero de tarefas
        self.table_tcb.setRowCount(len(tcbs))

        #antes de atualizar a página salva qual tarefa tinha sido selecionada na modificação de elementos e estado, pare evitar reseleção
        current_state_selection = self.combo_select_task.currentText()
        current_edit_selection = self.combo_edit_task.currentText()

        #silencia sinais e eventos do Qt para evitar que as caixas fiquem vazias visualmente em qualquer momento.
        self.combo_select_task.blockSignals(True)
        self.combo_edit_task.blockSignals(True)

        #limpa os dados da tabela
        self.combo_select_task.clear()
        self.combo_edit_task.clear()

        #loop que percore a lista de tcbs
        for row, tcb in enumerate(tcbs):
            #atribui o valor de id para cada combo box com base no id anterior ao tick
            self.combo_select_task.addItem(tcb.id)
            self.combo_edit_task.addItem(tcb.id)

            #preenche a primeira célula com a string do id
            self.table_tcb.setItem(row, 0, QTableWidgetItem(tcb.id))

            #define a cor do texto para cada estado de tarefa possível
            item_status = QTableWidgetItem(tcb.estado)
            status_colors = {
                "PRONTA": "#F1C40F", "EXECUTANDO": "#2ECC71",
                "SUSPENSA": "#E67E22", "CONCLUIDA": "#95A5A6", "CANCELADA": "#E74C3C"
            }
            item_status.setForeground(QColor(status_colors.get(tcb.estado, "#FFFFFF")))
            self.table_tcb.setItem(row, 1, item_status)

            #aloca cada tarefa que estava em uma cpu na cpu correta (só visualmente, a alocação real não é aqui)
            cpu_text = f"CPU #{tcb.cpu_alocada:02d}" if tcb.cpu_alocada else "-"
            self.table_tcb.setItem(row, 2, QTableWidgetItem(cpu_text))
            #atribui nas cédulas os valores das tarefas percorridas na lista, usando seus valores do tick atual
            self.table_tcb.setItem(row, 3, QTableWidgetItem(str(tcb.ingresso)))
            self.table_tcb.setItem(row, 4, QTableWidgetItem(f"{tcb.duracao_restante} / {tcb.duracao_total}"))
            self.table_tcb.setItem(row, 5, QTableWidgetItem(str(tcb.periodo)))
            self.table_tcb.setItem(row, 6, QTableWidgetItem(str(tcb.proximo_release)))
            self.table_tcb.setItem(row, 7, QTableWidgetItem(str(tcb.prazo_absoluto)))
            self.table_tcb.setItem(row, 8, QTableWidgetItem(f"{tcb.execucoes_concluidas} / {tcb.limite_execucoes}"))


        idx_state = self.combo_select_task.findText(current_state_selection) # procura onde ta a tarefa no menu de estado
        if idx_state >= 0: # confere se a tarefa ainda ta na lista
            self.combo_select_task.setCurrentIndex(idx_state) # devolve a selecao pra tarefa
        self.combo_select_task.blockSignals(False) # destrava os sinais desse menu

        idx_edit = self.combo_edit_task.findText(current_edit_selection) # procura a tarefa no menu de edicao
        if idx_edit >= 0: # ve se a tarefa ainda existe nesse tick
            self.combo_edit_task.setCurrentIndex(idx_edit) # marca a tarefa de novo
        elif self.combo_edit_task.count() > 0: # se a tarefa sumiu mas tem outras na fila
            self.combo_edit_task.setCurrentIndex(0) # seleciona a primeira que aparecer

        self.combo_edit_task.blockSignals(False) # destrava os sinais do menu de edicao
        self.on_edit_task_selected() # puxa os dados novos pra tela