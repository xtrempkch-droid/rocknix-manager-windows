import sys
import os
import requests
import zipfile
import shutil
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QProgressBar, QMessageBox,
    QFrame, QAbstractItemView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
import qdarktheme  # Importado para suporte a temas automáticos

# Configurações do App
APP_NAME = "Rocknix Manager"
VERSION = "v0.1.1"
GITHUB_USER = "rocknix"
GITHUB_REPO = "distribution"

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            with open(self.dest_path, 'wb') as f:
                downloaded = 0
                for data in response.iter_content(chunk_size=4096):
                    downloaded += len(data)
                    f.write(data)
                    if total_size > 0:
                        self.progress.emit(int(downloaded * 100 / total_size))
            
            self.finished.emit(self.dest_path)
        except Exception as e:
            self.error.emit(str(e))

class RocknixManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"{APP_NAME} {VERSION}")
        self.resize(600, 450)

        # Widget Principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Cabeçalho
        header_label = QLabel(APP_NAME)
        header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)

        # Lista de Versões
        self.version_list = QListWidget()
        self.version_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.version_list.setAlternatingRowColors(True)
        layout.addWidget(QLabel("Versões Disponíveis (GitHub):"))
        layout.addWidget(self.version_list)

        # Barra de Progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Botões
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Atualizar Lista")
        self.refresh_btn.clicked.connect(self.fetch_versions)
        
        self.download_btn = QPushButton("Baixar e Instalar")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setEnabled(False)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.download_btn)
        layout.addLayout(btn_layout)

        # Status
        self.status_label = QLabel("Pronto")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.status_label)

        # Inicializar Lista
        self.version_list.itemSelectionChanged.connect(lambda: self.download_btn.setEnabled(True))
        self.fetch_versions()

    def fetch_versions(self):
        try:
            self.status_label.setText("Buscando versões...")
            url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases"
            response = requests.get(url)
            response.raise_for_status()
            releases = response.json()
            
            self.version_list.clear()
            self.releases_data = releases
            
            for rel in releases:
                self.version_list.addItem(rel['tag_name'])
            
            self.status_label.setText("Lista atualizada")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao buscar versões:\n{str(e)}")
            self.status_label.setText("Erro na busca")

    def start_download(self):
        selected_item = self.version_list.currentItem()
        if not selected_item:
            return

        tag = selected_item.text()
        # Encontrar o asset correto (exemplo simplificado: pega o primeiro asset zip)
        asset_url = None
        for rel in self.releases_data:
            if rel['tag_name'] == tag:
                for asset in rel.get('assets', []):
                    if asset['name'].endswith('.zip') or asset['name'].endswith('.img.gz'):
                        asset_url = asset['browser_download_url']
                        break
        
        if not asset_url:
            QMessageBox.warning(self, "Aviso", "Nenhum arquivo compatível encontrado nesta release.")
            return

        dest_path = os.path.join(os.getcwd(), os.path.basename(asset_url))
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.download_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        
        self.thread = DownloadThread(asset_url, dest_path)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.finished.connect(self.on_finished)
        self.thread.error.connect(self.on_error)
        self.thread.start()

    def on_finished(self, path):
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        QMessageBox.information(self, "Sucesso", f"Download concluído:\n{path}")
        self.status_label.setText("Download finalizado")

    def on_error(self, message):
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        QMessageBox.critical(self, "Erro de Download", message)
        self.status_label.setText("Erro no download")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Aplica o tema automaticamente baseando-se no sistema (Light/Dark)
    qdarktheme.setup_theme("auto")
    
    manager = RocknixManager()
    manager.show()
    sys.exit(app.exec())
