import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QStackedWidget
)
from PySide6.QtCore import Qt

from pages import ConfigPage, CPUsPage, TasksPage, GanttPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador de Escalonamento de Tempo Real - SO Multitarefa")
        self.resize(1150, 750)
        self.current_tick = 0
        self.init_hud_ui()
        
        # Conectar o sinal de configuração para atualizar as outras abas instantaneamente
        self.page_config.config_changed.connect(self.sync_all_pages)
        
        # Forçar primeira sincronização com a configuração padrão
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
        self.btn_play_pause = QPushButton("⏯ Play/Pause")
        self.btn_step_fwd = QPushButton("⏭ Avançar")
        self.btn_reset = QPushButton("🔄 Reiniciar")

        for btn in [self.btn_step_back, self.btn_play_pause, self.btn_step_fwd, self.btn_reset]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3E3E42; color: white; border: none; padding: 5px 10px; border-radius: 3px;
                }
                QPushButton:hover { background-color: #505054; }
            """)
            ctrl_layout.addWidget(btn)

        self.btn_step_fwd.clicked.connect(self.advance_tick)
        self.btn_step_back.clicked.connect(self.step_back_tick)
        self.btn_reset.clicked.connect(self.reset_tick)

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

        # Sidebar
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

        # Stack de Páginas Modulares
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
        self.lbl_timer = QLabel(f"RELÓGIO GLOBAL (TICK): {self.current_tick:04d}")
        self.lbl_timer.setStyleSheet("font-weight: bold; font-family: monospace;")

        bottom_hud_layout.addWidget(self.lbl_status_bar)
        bottom_hud_layout.addStretch(1)
        bottom_hud_layout.addWidget(self.lbl_timer)

        main_layout.addWidget(bottom_hud)

    def sync_all_pages(self, config: dict):
        """Notifica todas as páginas com os novos parâmetros carregados/alterados."""
        self.page_cpus.update_config(config)
        self.page_tasks.update_config(config)
        self.page_gantt.update_config(config)
        self.lbl_status_bar.setText(
            f"Configuração Ativa: {config['cpus']} CPU(s) | {len(config['tasks'])} Tarefas Periódicas [{config['algorithm']}]"
        )

    def switch_page(self, index: int, title: str, active_btn: QPushButton):
        self.stacked_widget.setCurrentIndex(index)
        self.lbl_page_title.setText(title)
        for btn in self.nav_buttons:
            btn.setChecked(btn == active_btn)

    def advance_tick(self):
        self.current_tick += 1
        self.update_timer_display()

    def step_back_tick(self):
        if self.current_tick > 0:
            self.current_tick -= 1
            self.update_timer_display()

    def reset_tick(self):
        self.current_tick = 0
        self.update_timer_display()

    def update_timer_display(self):
        self.lbl_timer.setText(f"RELÓGIO GLOBAL (TICK): {self.current_tick:04d}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())