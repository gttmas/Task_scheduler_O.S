import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer

from pages import ConfigPage, CPUsPage, TasksPage, GanttPage
from core import SimulationEngine


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Escalonamento de Tempo Real - SO Multitarefa")
        self.resize(1150, 750)

        # Instância central do Motor da Simulação
        self.engine = SimulationEngine()
        self.is_running = False
        self.current_config = {}

        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.advance_tick)

        self.init_hud_ui()

        # Conecta alterações de configuração ao reset do motor
        self.page_config.config_changed.connect(self.on_config_changed)
        self.page_config.emit_config_changed()

    def init_hud_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. HUD SUPERIOR
        top_hud = QFrame()
        top_hud.setStyleSheet("background-color: #2D2D30; color: white;")
        top_hud_layout = QHBoxLayout(top_hud)
        top_hud_layout.setContentsMargins(15, 8, 15, 8)

        lbl_logo = QLabel("<b>SIMULADOR SO</b>")
        lbl_logo.setStyleSheet("font-size: 14px; color: #007ACC;")

        self.lbl_page_title = QLabel("Configuração do Sistema")
        self.lbl_page_title.setAlignment(Qt.AlignCenter)
        self.lbl_page_title.setStyleSheet("font-size: 15px; font-weight: bold;")

        ctrl_layout = QHBoxLayout()
        self.btn_step_back = QPushButton("⏮ Voltar")
        self.btn_play_pause = QPushButton("▶ Play")
        self.btn_step_fwd = QPushButton("⏭ Avançar")
        self.btn_reset = QPushButton("🔄 Reiniciar")

        for btn in [self.btn_step_back, self.btn_play_pause, self.btn_step_fwd, self.btn_reset]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3E3E42; color: white; border: none; padding: 5px 12px; border-radius: 3px; font-weight: bold;
                }
                QPushButton:hover { background-color: #505054; }
            """)
            ctrl_layout.addWidget(btn)

        self.btn_play_pause.clicked.connect(self.toggle_play_pause)
        self.btn_step_fwd.clicked.connect(self.manual_step_forward)
        self.btn_step_back.clicked.connect(self.manual_step_back)
        self.btn_reset.clicked.connect(self.reset_simulation)

        top_hud_layout.addWidget(lbl_logo)
        top_hud_layout.addStretch(1)
        top_hud_layout.addWidget(self.lbl_page_title)
        top_hud_layout.addStretch(1)
        top_hud_layout.addLayout(ctrl_layout)

        main_layout.addWidget(top_hud)

        # 2. CORPO CENTRAL
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(160)
        sidebar.setStyleSheet("""
            QFrame { background-color: #252526; border-right: 1px solid #3F3F46; }
            QPushButton {
                background-color: transparent; color: #CCCCCC; text-align: left;
                padding: 12px 15px; border: none; font-size: 13px;
            }
            QPushButton:hover { background-color: #3E3E42; color: white; }
            QPushButton:checked { background-color: #094771; color: white; font-weight: bold; }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 10, 0, 10)
        sidebar_layout.setSpacing(2)

        btn_nav_config = QPushButton("⚙️ Configuração")
        btn_nav_cpus = QPushButton("💻 CPUs / Estado")
        btn_nav_tasks = QPushButton("📋 Tarefas (TCB)")
        btn_nav_gantt = QPushButton("📊 Diag. Gantt")

        for b in [btn_nav_config, btn_nav_cpus, btn_nav_tasks, btn_nav_gantt]:
            b.setCheckable(True)

        btn_nav_config.setChecked(True)

        sidebar_layout.addWidget(btn_nav_config)
        sidebar_layout.addWidget(btn_nav_cpus)
        sidebar_layout.addWidget(btn_nav_tasks)
        sidebar_layout.addWidget(btn_nav_gantt)
        sidebar_layout.addStretch(1)

        body_layout.addWidget(sidebar)

        self.stacked_widget = QStackedWidget()

        self.page_config = ConfigPage()
        self.page_cpus = CPUsPage()
        self.page_tasks = TasksPage()
        self.page_gantt = GanttPage()

        self.stacked_widget.addWidget(self.page_config)
        self.stacked_widget.addWidget(self.page_cpus)
        self.stacked_widget.addWidget(self.page_tasks)
        self.stacked_widget.addWidget(self.page_gantt)

        body_layout.addWidget(self.stacked_widget, 1)
        main_layout.addLayout(body_layout, 1)

        btn_nav_config.clicked.connect(lambda: self.switch_page(0, "Configuração do Sistema", btn_nav_config))
        btn_nav_cpus.clicked.connect(lambda: self.switch_page(1, "Monitor de Processadores (CPUs)", btn_nav_cpus))
        btn_nav_tasks.clicked.connect(lambda: self.switch_page(2, "Gerenciador de Tarefas (TCB)", btn_nav_tasks))
        btn_nav_gantt.clicked.connect(lambda: self.switch_page(3, "Diagrama de Gantt", btn_nav_gantt))

        self.nav_buttons = [btn_nav_config, btn_nav_cpus, btn_nav_tasks, btn_nav_gantt]

        # 3. HUD INFERIOR
        bottom_hud = QFrame()
        bottom_hud.setStyleSheet("background-color: #007ACC; color: white;")
        bottom_hud_layout = QHBoxLayout(bottom_hud)
        bottom_hud_layout.setContentsMargins(15, 4, 15, 4)

        self.lbl_status_bar = QLabel("Sistema Pronto")
        self.lbl_timer = QLabel("RELÓGIO GLOBAL (TICK): 0000")
        self.lbl_timer.setStyleSheet("font-weight: bold; font-family: monospace;")

        bottom_hud_layout.addWidget(self.lbl_status_bar)
        bottom_hud_layout.addStretch(1)
        bottom_hud_layout.addWidget(self.lbl_timer)

        main_layout.addWidget(bottom_hud)

    def on_config_changed(self, config_data: dict):
            """Diferencia carregamento de novo arquivo de alterações dinâmicas de CPUs."""

            self.current_config = config_data
            new_cpu_count = config_data.get("cpus", 1)
            
            # Se a quantidade de CPUs mudou com a simulação em andamento, faz ajuste dinâmico
            if self.engine.cpus and len(self.engine.cpus) != new_cpu_count and self.engine.current_tick > 0:
                self.engine.set_cpu_count(new_cpu_count)
            else:
                # Novo arquivo carregado ou reinício manual
                self.pause_simulation()
                self.engine.init_from_config(config_data)
                
            self.render_engine_state(self.engine.get_current_state())

    def render_engine_state(self, state: dict):
        """Envia o estado atual do motor para renderização em todas as abas."""
        self.page_cpus.render_state(state)
        self.page_tasks.render_state(state)
        self.page_config.render_state(state)
        self.lbl_timer.setText(f"RELÓGIO GLOBAL (TICK): {state['tick']:04d}")
        self.lbl_status_bar.setText(
            f"Configuração Ativa: {len(state['cpus'])} CPU(s) | {len(state['tcbs'])} Tarefas [{state['algorithm']}]"
        )

    def advance_tick(self):
        """Avança 1 tick no motor e re-renderiza a interface."""
        state = self.engine.step_forward()
        self.render_engine_state(state)

    def manual_step_forward(self):
        self.pause_simulation()
        self.advance_tick()

    def manual_step_back(self):
        self.pause_simulation()
        state = self.engine.step_back()
        self.render_engine_state(state)

    def reset_simulation(self):
        self.pause_simulation()
        self.engine.reset()
        self.render_engine_state(self.engine.get_current_state())

    def toggle_play_pause(self):
        if self.is_running:
            self.pause_simulation()
        else:
            self.start_simulation()

    def start_simulation(self):
        # Lê o modo escolhido na interface (Passo a Passo ou Execução Completa)
        modo_execucao = self.current_config.get("mode", "STEP")
        
        # CAMINHO 1: Execução Completa (Tudo de uma vez)
        if modo_execucao == "FULL":
            self.lbl_status_bar.setText("Processando Execução Completa...")
            
            # Pede para o motor calcular tudo no backend na mesma hora
            estado_final = self.engine.run_full_simulation()
            
            # Manda as abas desenharem o estado final (último tick)
            self.render_engine_state(estado_final)
            
            self.lbl_status_bar.setText("Simulação Completa Finalizada!")
            
        # CAMINHO 2: Passo a Passo (Avanço com o Timer)
        else:
            self.is_running = True
            self.btn_play_pause.setText("⏸ Pause")
            self.btn_play_pause.setStyleSheet("""
                QPushButton { background-color: #D35400; color: white; border: none; padding: 5px 12px; border-radius: 3px; font-weight: bold; }
                QPushButton:hover { background-color: #E67E22; }
            """)
            self.lbl_status_bar.setText("Simulação em Execução Automática (1 tick a cada 5s)...")
            self.timer.start()

    def pause_simulation(self):
        self.is_running = False
        self.timer.stop()
        self.btn_play_pause.setText("▶ Play")
        self.btn_play_pause.setStyleSheet("""
            QPushButton { background-color: #3E3E42; color: white; border: none; padding: 5px 12px; border-radius: 3px; font-weight: bold; }
            QPushButton:hover { background-color: #505054; }
        """)

    def switch_page(self, index: int, title: str, active_btn: QPushButton):
        self.stacked_widget.setCurrentIndex(index)
        self.lbl_page_title.setText(title)
        for btn in self.nav_buttons:
            btn.setChecked(btn == active_btn)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())