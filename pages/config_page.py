import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QSpinBox, QRadioButton, QFileDialog, QTableWidget, 
    QTableWidgetItem, QHeaderView, QTextEdit, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


class ConfigPage(QWidget):
    """Página de Configuração e Carga de Ficheiros com Emissão de Sinais."""
    
    # Sinal emitido sempre que qualquer configuração/ficheiro mudar
    config_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file_path = None
        self.tasks_data = []
        self.init_ui()
        self.connect_signals()
        self.load_default_config()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 1. BLOCO DE FICHEIRO
        file_box = QGroupBox("Arquivo de Configuração")
        file_layout = QHBoxLayout(file_box)

        self.lbl_file_status = QLabel("Arquivo Atual: Configuração Padrão (Sistema)")
        self.lbl_file_status.setStyleSheet("font-weight: bold; color: #2B579A;")

        btn_load_file = QPushButton("📁 Carregar Arquivo (.txt)")
        btn_load_file.clicked.connect(self.select_file)

        btn_restore_default = QPushButton("🔄 Restaurar Padrões")
        btn_restore_default.clicked.connect(self.load_default_config)

        file_layout.addWidget(self.lbl_file_status, 1)
        file_layout.addWidget(btn_load_file)
        file_layout.addWidget(btn_restore_default)
        main_layout.addWidget(file_box)

        # 2. BLOCO DE PARÂMETROS GERAIS
        params_box = QGroupBox("Parâmetros Gerais do Sistema Operacional (Linha 1)")
        params_layout = QHBoxLayout(params_box)

        params_layout.addWidget(QLabel("Algoritmo:"))
        self.combo_algorithm = QComboBox()
        self.combo_algorithm.addItems(["RM (Rate Monotonic)", "EDF (Earliest Deadline First)"])
        params_layout.addWidget(self.combo_algorithm)

        params_layout.addWidget(QLabel("Quantum (ticks):"))
        self.spin_quantum = QSpinBox()
        self.spin_quantum.setRange(1, 100)
        self.spin_quantum.setValue(1)
        params_layout.addWidget(self.spin_quantum)

        params_layout.addWidget(QLabel("Qtd. CPUs:"))
        self.spin_cpus = QSpinBox()
        self.spin_cpus.setRange(1, 64)
        self.spin_cpus.setValue(2)
        params_layout.addWidget(self.spin_cpus)

        params_layout.addWidget(QLabel("Modo:"))
        self.radio_step = QRadioButton("Passo a Passo (Debugger)")
        self.radio_full = QRadioButton("Execução Completa")
        self.radio_step.setChecked(True)
        params_layout.addWidget(self.radio_step)
        params_layout.addWidget(self.radio_full)

        main_layout.addWidget(params_box)

        # 3. TABELA + CONSOLE DE LOGS
        splitter = QSplitter(Qt.Vertical)

        # Sub-Bloco A: Tabela de Pré-visualização
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        tasks_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_tasks_title = QLabel("Resumo das Tarefas Carregadas")
        lbl_tasks_title.setStyleSheet("font-weight: bold;")
        tasks_layout.addWidget(lbl_tasks_title)

        self.table_tasks = QTableWidget()
        self.table_tasks.setColumnCount(7)
        self.table_tasks.setHorizontalHeaderLabels([
            "ID", "Cor (RGB Hex)", "Ingresso", "Duração", "Período", "Prazo (Deadline)", "Eventos"
        ])
        self.table_tasks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_tasks.setEditTriggers(QTableWidget.NoEditTriggers)
        tasks_layout.addWidget(self.table_tasks)

        splitter.addWidget(tasks_widget)

        # Sub-Bloco B: Console de Logs
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)

        lbl_log_title = QLabel("Console de Status, Validações e Erros de Carregamento")
        lbl_log_title.setStyleSheet("font-weight: bold;")
        log_layout.addWidget(lbl_log_title)

        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E; color: #D4D4D4;
                font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;
                border: 1px solid #3C3C3C;
            }
        """)
        log_layout.addWidget(self.txt_logs)

        splitter.addWidget(log_widget)
        splitter.setSizes([200, 150])

        main_layout.addWidget(splitter, 1)

    def connect_signals(self):
        """Conecta eventos dos controles na tela para notificar alterações em tempo real."""
        self.spin_cpus.valueChanged.connect(self.emit_config_changed)
        self.combo_algorithm.currentIndexChanged.connect(self.emit_config_changed)
        self.spin_quantum.valueChanged.connect(self.emit_config_changed)
        self.radio_step.toggled.connect(self.emit_config_changed)

    def emit_config_changed(self):
        """Monta o dicionário com o estado atual da configuração e emite o sinal."""
        config_data = {
            "cpus": self.spin_cpus.value(),
            "algorithm": self.combo_algorithm.currentText(),
            "quantum": self.spin_quantum.value(),
            "mode": "STEP" if self.radio_step.isChecked() else "FULL",
            "tasks": self.tasks_data
        }
        self.config_changed.emit(config_data)

    def log_message(self, message: str, level: str = "INFO"):
        colors = {
            "SUCCESS": "#4EC9B0", "INFO": "#9CDCFE",
            "WARNING": "#CE9178", "ERROR": "#F44747"
        }
        color_hex = colors.get(level.upper(), "#D4D4D4")
        prefix = f"[{level.upper()}]"
        formatted_html = f'<span style="color: {color_hex}; font-weight: bold;">{prefix}</span> <span style="color: #D4D4D4;">{message}</span><br>'
        self.txt_logs.append(formatted_html)

    def load_default_config(self):
        self.current_file_path = None
        self.lbl_file_status.setText("Arquivo Atual: Configuração Padrão (Sistema)")
        self.txt_logs.clear()
        self.log_message("Restaurando configuração inicial padrão...", "INFO")

        default_text = """RM; 1; 2
T1; FF5733; 0; 2; 10; 6; -
T2; 33FF57; 0; 2; 10; 8; -
T3; 3357FF; 0; 8; 20; 16; -"""

        self.parse_config_text(default_text, source_name="Configuração Padrão")

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo de Configuração", "", "Arquivos de Texto (*.txt);;Todos os Arquivos (*)"
        )
        if file_path:
            self.load_file_from_path(file_path)

    def load_file_from_path(self, path: str):
        self.txt_logs.clear()
        self.log_message(f"Tentando carregar arquivo: {path}", "INFO")

        try:
            if not os.path.exists(path):
                raise FileNotFoundError("O arquivo especificado não foi encontrado.")

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.current_file_path = path
            self.lbl_file_status.setText(f"Arquivo Atual: {os.path.basename(path)}")
            self.parse_config_text(content, source_name=os.path.basename(path))

        except PermissionError:
            self.log_message(f"Erro de Permissão: O aplicativo não possui acesso de leitura para '{path}'.", "ERROR")
        except Exception as e:
            self.log_message(f"Falha ao carregar arquivo: {str(e)}", "ERROR")

    def parse_config_text(self, text: str, source_name: str):
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        if not lines:
            self.log_message("Erro: O arquivo de configuração está vazio.", "ERROR")
            return

        # --- VALIDAÇÃO DO REQUISITO 3.3.1 (MÍNIMO DE 2 LINHAS) ---
        if len(lines) < 2:
            self.log_message("Erro [Requisito 3.3.1]: O arquivo de configuração deve ter PELO MENOS 2 LINHAS (Linha 1: Parâmetros do SO, Linhas seguintes: Tarefas).", "ERROR")
            return

        line_1 = lines[0].rstrip(';')
        parts_1 = [p.strip() for p in line_1.split(';')]

        if len(parts_1) < 3:
            self.log_message("Erro na Linha 1: Parâmetros globais incompletos. Esperado 'algoritmo; quantum; cpus'.", "ERROR")
            return

        self.spin_cpus.blockSignals(True)
        self.combo_algorithm.blockSignals(True)
        self.spin_quantum.blockSignals(True)

        algo_raw, quantum_raw, cpus_raw = parts_1[0], parts_1[1], parts_1[2]

        if "RM" in algo_raw.upper():
            self.combo_algorithm.setCurrentIndex(0)
        elif "EDF" in algo_raw.upper():
            self.combo_algorithm.setCurrentIndex(1)
        else:
            self.log_message(f"Aviso: Algoritmo '{algo_raw}' desconhecido. Assumindo RM por padrão.", "WARNING")
            self.combo_algorithm.setCurrentIndex(0)

        try:
            val_quantum = int(quantum_raw)
            if val_quantum < 1:
                self.log_message(f"Aviso: Quantum ({val_quantum}) deve ser >= 1. Ajustado para 1.", "WARNING")
                val_quantum = 1
            self.spin_quantum.setValue(val_quantum)

            val_cpus = int(cpus_raw)
            if val_cpus < 1:
                self.log_message(f"Aviso: Quantidade de CPUs ({val_cpus}) deve ser >= 1. Ajustado para 1 CPU.", "WARNING")
                val_cpus = 1
            self.spin_cpus.setValue(val_cpus)

        except ValueError:
            self.log_message("Erro na Linha 1: Quantum ou CPUs não correspondem a valores numéricos válidos.", "ERROR")
            self.spin_cpus.blockSignals(False)
            self.combo_algorithm.blockSignals(False)
            self.spin_quantum.blockSignals(False)
            return

        self.spin_cpus.blockSignals(False)
        self.combo_algorithm.blockSignals(False)
        self.spin_quantum.blockSignals(False)

        parsed_tasks = []
        ignored_aperiodic_count = 0
        error_count = 0

        for line_num, line in enumerate(lines[1:], start=2):
            clean_line = line.rstrip(';')
            parts = [p.strip() for p in clean_line.split(';')]

            if len(parts) < 6:
                self.log_message(f"Aviso [Linha {line_num}]: Formato inválido (menos de 6 campos). Linha ignorada: '{line}'", "WARNING")
                error_count += 1
                continue

            t_id, t_color = parts[0], parts[1]

            try:
                t_ingresso, t_duracao = int(parts[2]), int(parts[3])
                t_periodo, t_prazo = int(parts[4]), int(parts[5])
                t_eventos = parts[6] if len(parts) > 6 else "-"
            except ValueError:
                self.log_message(f"Erro [Linha {line_num}]: Parâmetros numéricos inválidos na tarefa '{t_id}'.", "ERROR")
                error_count += 1
                continue

            # --- VALIDAÇÕES DE PERÍODO (REQUISITO 3.3 E 4.4) ---
            if t_periodo == 0:
                ignored_aperiodic_count += 1
                self.log_message(f"Aviso [Projeto A]: A tarefa '{t_id}' é Aperiódica (Período: 0) e foi IGNORADA.", "WARNING")
                continue
            elif t_periodo < 0:
                error_count += 1
                self.log_message(f"Erro [Linha {line_num}]: Período negativo ({t_periodo}) na tarefa '{t_id}' é inválido (Requisito 3.3).", "ERROR")
                continue

            parsed_tasks.append({
                "id": t_id, "color": t_color, "ingresso": t_ingresso,
                "duracao": t_duracao, "periodo": t_periodo, "prazo": t_prazo, "eventos": t_eventos
            })

        self.tasks_data = parsed_tasks
        self.update_tasks_table()

        if len(self.tasks_data) == 0:
            self.log_message("Aviso [Requisito 3.3.1]: Nenhuma tarefa válida foi encontrada/carregada do arquivo.", "WARNING")
        else:
            self.log_message(f"Sucesso: Configuração de '{source_name}' carregada com sucesso!", "SUCCESS")
            self.log_message(f"Resumo: {len(self.tasks_data)} tarefas periódicas ativas carregadas.", "INFO")

        if ignored_aperiodic_count > 0:
            self.log_message(f"Nota: Total de {ignored_aperiodic_count} tarefa(s) aperiódica(s) desconsiderada(s).", "WARNING")

        self.emit_config_changed()

    def render_state(self, state: dict):
        if not state:
            return

        cpus_list = state.get("cpus", [])
        if hasattr(self, "spin_cpus") and cpus_list:
            self.spin_cpus.blockSignals(True)
            self.spin_cpus.setValue(len(cpus_list))
            self.spin_cpus.blockSignals(False)

        algo = state.get("algorithm", "")
        if hasattr(self, "combo_algorithm") and algo:
            self.combo_algorithm.blockSignals(True)
            if "RM" in algo.upper():
                self.combo_algorithm.setCurrentIndex(0)
            elif "EDF" in algo.upper():
                self.combo_algorithm.setCurrentIndex(1)
            self.combo_algorithm.blockSignals(False)

        quantum = state.get("quantum")
        if hasattr(self, "spin_quantum") and quantum is not None:
            self.spin_quantum.blockSignals(True)
            self.spin_quantum.setValue(quantum)
            self.spin_quantum.blockSignals(False)

    def update_tasks_table(self):
        self.table_tasks.setRowCount(len(self.tasks_data))
        for row, task in enumerate(self.tasks_data):
            self.table_tasks.setItem(row, 0, QTableWidgetItem(str(task["id"])))
            
            color_hex = f"#{task['color'].lstrip('#')}"
            item_color = QTableWidgetItem(color_hex)
            item_color.setBackground(QColor(color_hex))
            item_color.setForeground(QColor("#000000" if color_hex.upper() in ["#FFFFFF", "#FFF"] else "#FFFFFF"))
            self.table_tasks.setItem(row, 1, item_color)

            self.table_tasks.setItem(row, 2, QTableWidgetItem(str(task["ingresso"])))
            self.table_tasks.setItem(row, 3, QTableWidgetItem(str(task["duracao"])))                                                                                        
            self.table_tasks.setItem(row, 4, QTableWidgetItem(str(task["periodo"])))
            self.table_tasks.setItem(row, 5, QTableWidgetItem(str(task["prazo"])))
            self.table_tasks.setItem(row, 6, QTableWidgetItem(str(task["eventos"])))                                                                                                                                        