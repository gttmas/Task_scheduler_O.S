from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QScrollArea, QGridLayout, QFrame
)
from core import CPU


class CPUsPage(QWidget):
    """Página de Monitoramento das CPUs e Ociosidade."""
    
    def __init__(self, parent=None): # função padrão de inicialização da classe
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Função que inicia a interface da página de visualização das CPU's """
        layout = QVBoxLayout(self) # definição da página de cpu no modo vertical
        layout.setContentsMargins(15, 15, 15, 15) # margens da página
        layout.setSpacing(12)

        # widget superior para dar um panorama geral de todos os processadores
        summary_box = QGroupBox("Métricas Globais dos Processadores")
        summary_layout = QHBoxLayout(summary_box) # itens lado a lado (Horizontal)

        # textos com os dados (são atualizados com o tempo)
        self.lbl_active_cpus = QLabel("CPUs Executando: 0 / 0")
        self.lbl_global_idle = QLabel("Tempo Total Ocioso/Desligado: 0 ticks")

        # deixa o tempo ocioso em destaque (laranja)
        self.lbl_global_idle.setStyleSheet("color: #D35400; font-weight: bold;")

        # adiciona os textos no widget
        summary_layout.addWidget(self.lbl_active_cpus)
        summary_layout.addWidget(self.lbl_global_idle)
        summary_layout.addStretch(1)

        # adiciona o widget superior na página
        layout.addWidget(summary_box)

        # widget central que guarda os retângulos (cartões) com informações de cada CPU
        cpus_box = QGroupBox("Estado dos Processadores (Cores)")
        cpus_box_layout = QVBoxLayout(cpus_box)

        # cria uma barra de rolagem para permitir a visualização de simulações com várias cpus
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()

        # QGridLayout é como uma tabela, com itens em linhas e colunas
        self.grid_cpus = QGridLayout(scroll_widget)
        self.grid_cpus.setSpacing(15)

        # adiciona o widget dos cartões de cpu na página
        scroll.setWidget(scroll_widget)
        cpus_box_layout.addWidget(scroll)
        layout.addWidget(cpus_box, 1)

        # widget inferior que mostra a fila de tarefas prontas
        queue_box = QGroupBox("Fila Global de Prontos (Aguardando Escalonamento)")
        queue_layout = QHBoxLayout(queue_box)
        self.lbl_ready_queue = QLabel("Fila de Prontos: [ Vazia ]")
        self.lbl_ready_queue.setStyleSheet("font-family: monospace; font-size: 13px; color: #27AE60;")
        queue_layout.addWidget(self.lbl_ready_queue)

        # adiciona o widget na página
        layout.addWidget(queue_box)

    def render_state(self, state: Dict[str, Any]):
        """Renderiza as CPUs e a Fila de Prontos com base no snapshot do motor.
         Parâmetro: Dicionário com as informações do estado atual da simulação"""

        # pega a lista de cpus e a fila de tarefas prontas do dicionário
        cpus_list: List[CPU] = state.get("cpus", [])
        ready_queue = state.get("ready_queue", [])

        # apaga os cartões de CPU desenhados na chamada anterior da função para que não fiquem se sobrepondo
        while self.grid_cpus.count():
            item = self.grid_cpus.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # calculo para a definição dos parâmetros mostrados no widget superior
        total_cpus = len(cpus_list) #número total de cpus
        active_cpus = sum(1 for c in cpus_list if c.status == CPU.STATUS_EXECUTANDO) # pega o número de quantas cpus estão ativas
        total_idle = sum(c.idle_ticks for c in cpus_list) # soma o tempo ocioso total de todas as cpus

        # atualiza os valores do widget superior com os valores no tick atual
        self.lbl_active_cpus.setText(f"CPUs Executando: {active_cpus} / {total_cpus}")
        self.lbl_global_idle.setText(f"Tempo Total Ocioso/Desligado: {total_idle} ticks")

        # ---------------------------------- define o espaço para desenhar os cartões de cpu ----------------------------------

        # se tiver 3 ou mais CPUs, divide em 3 colunas. Se tiver menos, usa equivalente à quantidade.
        cols = 3 if total_cpus >= 3 else total_cpus

        for i, cpu in enumerate(cpus_list): # para cada cpu:

            # chama a função para criar o cartão para a cpu
            card = self.create_cpu_card(cpu)
            # adiciona o cartão ao widget central
            self.grid_cpus.addWidget(card, i // cols, i % cols)

        # --------------------------------------------- atualiza a fila de prontos -------------------------------------------

        if ready_queue:

            # pega o id de cada tarefa presente na fila de prontas
            task_ids = [tcb.id for tcb in ready_queue]

            # atualiza os valores do widget inferior com os id's no tick atual
            self.lbl_ready_queue.setText(f"Fila de Prontos ({len(task_ids)}): [ {', '.join(task_ids)} ]")

        else:
            # caso a fila esteja vazia, avisa ao usuário
            self.lbl_ready_queue.setText("Fila de Prontos (0): [ Vazia ]")

        # --------------------------------------------------------------------------------------------------------------------


    def create_cpu_card(self, cpu: CPU) -> QFrame:
        """Função que cria o cartão com os dados da CPU para mostrar na página
         Parâmetro: Objeto da classe CPU com seus dados
         Retorna: O cartão da CPU"""

        # cria o cartão
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)

        # dicionário de cores para os possíveis status da CPU
        status_colors = {
            CPU.STATUS_EXECUTANDO: "#2ECC71",
            CPU.STATUS_DESLIGADA:     "#F1C40F",
        }

        # segurança: caso seja um estado inexistente/inválido, pinta de branco
        status_color = status_colors.get(cpu.status, "#FFFFFF")

        # define o estilo do cartão (fundo escuro, borda arredondada)
        card.setStyleSheet("""
            QFrame {
                background-color: #2D2D30; border: 1px solid #3F3F46; border-radius: 6px; padding: 10px;
            }
        """)

        # define o layout do cartão como vertical
        card_layout = QVBoxLayout(card)

        # label com o título do cartão (número da CPU)
        lbl_header = QLabel(f"<b>PROCESSADOR CPU #{cpu.cpu_id:02d}</b>")
        lbl_header.setStyleSheet("color: #007ACC; font-size: 14px;")

        # label com o status atual da CPU
        lbl_status = QLabel(f"Status: <b style='color: {status_color};'>{cpu.status}</b>")

        # label que mostra qual task está executando na CPU (ou "nenhuma" caso esteja vazia)
        task_id = cpu.current_task_id if cpu.current_task_id else "Nenhuma"
        lbl_task = QLabel(f"Tarefa Atual: <b>{task_id}</b>")
        lbl_idle = QLabel(f"Tempo Ocioso/Desligado: <b>{cpu.idle_ticks}</b> ticks")

        # adiciona os textos ao widget do cartão da CPU
        card_layout.addWidget(lbl_header)
        card_layout.addWidget(lbl_status)
        card_layout.addWidget(lbl_task)
        card_layout.addWidget(lbl_idle)

        # retorna o cartão da CPU
        return card