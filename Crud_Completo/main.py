import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import os

ARQUIVO_EXCEL = "dados.xlsx"

class CRUDApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cadastro")
        self.setFixedSize(700, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: #f5f5f5;
                font-family: 'Segoe UI';
            }
            QPushButton {
                background-color: #3c3f58;
                color: white;
                padding: 10px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #5a5e85;
            }
            QLineEdit {
                background-color: #2a2d3e;
                border: 1px solid #5a5e85;
                padding: 6px;
                color: white;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #3c3f58;
                color: white;
                padding: 5px;
                border: none;
            }
        """)

        self.dados = self.carregar_dados()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QHBoxLayout()
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome")
        self.idade_input = QLineEdit()
        self.idade_input.setPlaceholderText("Idade")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        form_layout.addWidget(self.nome_input)
        form_layout.addWidget(self.idade_input)
        form_layout.addWidget(self.email_input)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Adicionar")
        self.btn_add.clicked.connect(self.adicionar_dado)
        self.btn_update = QPushButton("Atualizar")
        self.btn_update.clicked.connect(self.atualizar_dado)
        self.btn_delete = QPushButton("Excluir")
        self.btn_delete.clicked.connect(self.excluir_dado)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_update)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(3)
        self.tabela.setHorizontalHeaderLabels(["Nome", "Idade", "Email"])
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSelectionBehavior(self.tabela.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.cellClicked.connect(self.selecionar_linha)
        layout.addWidget(self.tabela)

        self.setLayout(layout)
        self.atualizar_tabela()

    def carregar_dados(self):
        if os.path.exists(ARQUIVO_EXCEL):
            return pd.read_excel(ARQUIVO_EXCEL)
        else:
            return pd.DataFrame(columns=["Nome", "Idade", "Email"])

    def salvar_dados(self):
        self.dados.to_excel(ARQUIVO_EXCEL, index=False)

    def atualizar_tabela(self):
        self.tabela.setRowCount(len(self.dados))
        for i, row in self.dados.iterrows():
            self.tabela.setItem(i, 0, QTableWidgetItem(str(row["Nome"])))
            self.tabela.setItem(i, 1, QTableWidgetItem(str(row["Idade"])))
            self.tabela.setItem(i, 2, QTableWidgetItem(str(row["Email"])))

    def adicionar_dado(self):
        nome = self.nome_input.text()
        idade = self.idade_input.text()
        email = self.email_input.text()
        if nome and idade and email:
            self.dados.loc[len(self.dados)] = [nome, idade, email]
            self.salvar_dados()
            self.atualizar_tabela()
            self.nome_input.clear()
            self.idade_input.clear()
            self.email_input.clear()
        else:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos.")

    def selecionar_linha(self, row, col):
        self.nome_input.setText(self.tabela.item(row, 0).text())
        self.idade_input.setText(self.tabela.item(row, 1).text())
        self.email_input.setText(self.tabela.item(row, 2).text())
        self.row_selected = row

    def atualizar_dado(self):
        try:
            row = self.row_selected
            self.dados.loc[row] = [
                self.nome_input.text(),
                self.idade_input.text(),
                self.email_input.text()
            ]
            self.salvar_dados()
            self.atualizar_tabela()
        except AttributeError:
            QMessageBox.warning(self, "Erro", "Selecione um registro para atualizar.")

    def excluir_dado(self):
        try:
            row = self.row_selected
            self.dados.drop(index=row, inplace=True)
            self.dados.reset_index(drop=True, inplace=True)
            self.salvar_dados()
            self.atualizar_tabela()
            self.nome_input.clear()
            self.idade_input.clear()
            self.email_input.clear()
        except AttributeError:
            QMessageBox.warning(self, "Erro", "Selecione um registro para excluir.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CRUDApp()
    window.show()
    sys.exit(app.exec_())
