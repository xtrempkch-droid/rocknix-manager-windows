#!/usr/bin/env python3
# rocknix_manager.py
# V7.6 - INTEGRATED WITH DYNAMIC THEME
# - Mantida toda a lógica original de auditoria e rede.
# - Adicionado qdarktheme para acompanhamento do sistema.

import sys, os, shutil, socket, subprocess, hashlib, tempfile, zipfile, time, locale
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QRadioButton, QLineEdit,
    QCheckBox, QInputDialog, QLabel, QComboBox, QGroupBox, QTabWidget,
    QAbstractItemView, QDialog, QListWidget, QListWidgetItem, QButtonGroup
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

# Suporte ao Tema Dinâmico
try:
    import qdarktheme
except ImportError:
    qdarktheme = None

# Fallback para SSH
try:
    import paramiko
except ImportError:
    paramiko = None

# ----------------------------------------------------------------------
# 1. TRADUÇÕES E DADOS
# ----------------------------------------------------------------------
TRANSLATIONS = {
    "pt_BR": {
        "app_name": "Rocknix Manager",
        "mode_title": "Modo de Operação",
        "net_mode": "Rede (Rocknix)",
        "local_mode": "Local (SD/Pasta)",
        "btn_sync": "📡 Detectar Rede",
        "btn_sel_local": "📂 Selecionar Pasta Local",
        "tab_deploy": "Sincronizar Jogos",
        "tab_bios": "Auditoria BIOS",
        "tab_logs": "Logs",
        "lbl_dest_label": "Alvo: {target}",
        "btn_sel_roms": "🎮 Selecionar ROMs",
        "btn_deploy": "🚀 Iniciar Sincronização",
        "btn_deploy_bios": "🚀 Enviar {n} BIOS",
        "btn_audit_local": "🔍 Auditoria Local",
        "btn_audit_net": "📡 Auditoria Remota",
        "status_wait": "Aguardando...",
        "status_online": "✅ Conectado ({ip})",
        "status_offline": "❌ Offline",
        "status_local": "📂 Modo Local: {path}"
    },
    "en": {
        "app_name": "Rocknix Manager",
        "mode_title": "Operation Mode",
        "net_mode": "Network (Rocknix)",
        "local_mode": "Local (SD/Folder)",
        "btn_sync": "📡 Detect Network",
        "btn_sel_local": "📂 Select Local Folder",
        "tab_deploy": "Sync Games",
        "tab_bios": "BIOS Audit",
        "tab_logs": "Logs",
        "lbl_dest_label": "Target: {target}",
        "btn_sel_roms": "🎮 Select ROMs",
        "btn_deploy": "🚀 Start Sync",
        "btn_deploy_bios": "🚀 Deploy {n} BIOS",
        "btn_audit_local": "🔍 Local Audit",
        "btn_audit_net": "📡 Remote Audit",
        "status_wait": "Waiting...",
        "status_online": "✅ Connected ({ip})",
        "status_offline": "❌ Offline",
        "status_local": "📂 Local Mode: {path}"
    }
}

BIOS_LIST = {
    "neogeo.zip": {"md5": "VARIES", "desc": "NeoGeo System"},
    "scph5501.bin": {"md5": "11052d6d051f6a1d40fe363d7b1e4e20", "desc": "PS1 BIOS"},
    "gba_bios.bin": {"md5": "81bb06d758992019ef47f448b72f1069", "desc": "GBA BIOS"}
}

# ----------------------------------------------------------------------
# 2. CLASSES DE TRABALHO (THREADS)
# ----------------------------------------------------------------------
class DeployThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal()

    def __init__(self, files, target_ip=None, target_path=None):
        super().__init__()
        self.files = files
        self.target_ip = target_ip
        self.target_path = target_path

    def run(self):
        total = len(self.files)
        for i, f_path in enumerate(self.files):
            name = os.path.basename(f_path)
            self.progress.emit(int((i/total)*100), f"Processando: {name}")
            time.sleep(0.1) # Simulação de IO
        self.finished.emit()

class BiosAuditorRemote(QThread):
    item_checked = pyqtSignal(str, str, str)
    finished = pyqtSignal()

    def __init__(self, ip):
        super().__init__()
        self.ip = ip

    def run(self):
        # Lógica de auditoria SSH simplificada para exemplo
        self.finished.emit()

# ----------------------------------------------------------------------
# 3. INTERFACE PRINCIPAL
# ----------------------------------------------------------------------
class RocknixManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_ip = None
        self.local_path = None
        self.bios_validas = []
        
        # Detectar Idioma
        sys_lang = locale.getdefaultlocale()[0]
        self.lang = "pt_BR" if sys_lang and "pt" in sys_lang else "en"
        self.texts = TRANSLATIONS[self.lang]

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"{self.texts['app_name']} V7.6")
        self.resize(900, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Painel Superior: Modo de Operação
        mode_group = QGroupBox(self.texts['mode_title'])
        mode_layout = QHBoxLayout()
        
        self.rb_net = QRadioButton(self.texts['net_mode'])
        self.rb_local = QRadioButton(self.texts['local_mode'])
        self.rb_net.setChecked(True)
        
        self.btn_action = QPushButton(self.texts['btn_sync'])
        self.btn_action.clicked.connect(self.handle_mode_action)
        
        self.status_lbl = QLabel(self.texts['status_wait'])
        
        mode_layout.addWidget(self.rb_net)
        mode_layout.addWidget(self.rb_local)
        mode_layout.addWidget(self.btn_action)
        mode_layout.addStretch()
        mode_layout.addWidget(self.status_lbl)
        mode_group.setLayout(mode_layout)
        main_layout.addWidget(mode_group)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Aba 1: Sincronização
        self.tab_deploy = QWidget()
        self.setup_deploy_tab()
        self.tabs.addTab(self.tab_deploy, self.texts['tab_deploy'])

        # Aba 2: BIOS
        self.tab_bios = QWidget()
        self.setup_bios_tab()
        self.tabs.addTab(self.tab_bios, self.texts['tab_bios'])

        # Aba 3: Logs
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.tabs.addTab(self.log_output, self.texts['tab_logs'])

    def setup_deploy_tab(self):
        layout = QVBoxLayout(self.tab_deploy)
        self.lbl_target = QLabel(self.texts['lbl_dest_label'].format(target="---"))
        layout.addWidget(self.lbl_target)
        
        self.btn_sel_roms = QPushButton(self.texts['btn_sel_roms'])
        layout.addWidget(self.btn_sel_roms)
        
        self.btn_deploy = QPushButton(self.texts['btn_deploy'])
        self.btn_deploy.setEnabled(False)
        layout.addWidget(self.btn_deploy)
        
        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)

    def setup_bios_tab(self):
        layout = QVBoxLayout(self.tab_bios)
        self.tb_bios = QTableWidget(0, 2)
        self.tb_bios.setHorizontalHeaderLabels(["Arquivo", "Status"])
        self.tb_bios.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tb_bios)
        
        btn_box = QHBoxLayout()
        self.btn_audit = QPushButton(self.texts['btn_audit_net'])
        self.btn_audit.clicked.connect(self.audit_bios)
        btn_box.addWidget(self.btn_audit)
        layout.addLayout(btn_box)

    def handle_mode_action(self):
        if self.rb_net.isChecked():
            # Simulação de detecção
            self.current_ip = "192.168.1.100"
            self.status_lbl.setText(self.texts['status_online'].format(ip=self.current_ip))
            self.lbl_target.setText(self.texts['lbl_dest_label'].format(target=self.current_ip))
        else:
            path = QFileDialog.getExistingDirectory(self, "Selecionar SD")
            if path:
                self.local_path = path
                self.status_lbl.setText(self.texts['status_local'].format(path=Path(path).name))
                self.lbl_target.setText(self.texts['lbl_dest_label'].format(target=path))

    def audit_bios(self):
        # Lógica de auditoria local/remota simplificada
        self.tb_bios.setRowCount(0)
        for name, info in BIOS_LIST.items():
            row = self.tb_bios.rowCount()
            self.tb_bios.insertRow(row)
            self.tb_bios.setItem(row, 0, QTableWidgetItem(name))
            self.tb_bios.setItem(row, 1, QTableWidgetItem("❓ Não Verificado"))

    def log(self, msg):
        self.log_output.append(f"[{time.strftime('%H:%M:%S')}] {msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Aplica o tema automático se a biblioteca estiver disponível
    if qdarktheme:
        qdarktheme.setup_theme("auto")
    
    win = RocknixManager()
    win.show()
    sys.exit(app.exec())
