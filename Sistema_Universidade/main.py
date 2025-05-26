import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox
)

class SistemaNotas(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Notas")
        self.setGeometry(100, 100, 800, 600)

        self.dados = pd.DataFrame(columns=["Matrícula", "Nome", "Curso", "N1", "N2", "N3", "Média", "Status"])
        self.arquivo_csv = "dados_notas.csv"
        self.carregar_dados()

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Entradas de dados
        self.matricula_input = QLineEdit()
        self.matricula_input.setPlaceholderText("Matrícula")
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome")
        self.curso_input = QLineEdit()
        self.curso_input.setPlaceholderText("Curso")
        self.n1_input = QLineEdit()
        self.n1_input.setPlaceholderText("Nota N1")
        self.n2_input = QLineEdit()
        self.n2_input.setPlaceholderText("Nota N2")
        self.n3_input = QLineEdit()
        self.n3_input.setPlaceholderText("Nota N3")

        layout.addWidget(self.matricula_input)
        layout.addWidget(self.nome_input)
        layout.addWidget(self.curso_input)
        layout.addWidget(self.n1_input)
        layout.addWidget(self.n2_input)
        layout.addWidget(self.n3_input)

        # Botões
        botoes_layout = QHBoxLayout()
        adicionar_btn = QPushButton("Adicionar")
        adicionar_btn.clicked.connect(self.adicionar_dado)
        atualizar_btn = QPushButton("Atualizar")
        atualizar_btn.clicked.connect(self.atualizar_dado)
        deletar_btn = QPushButton("Deletar")
        deletar_btn.clicked.connect(self.deletar_dado)

        botoes_layout.addWidget(adicionar_btn)
        botoes_layout.addWidget(atualizar_btn)
        botoes_layout.addWidget(deletar_btn)

        layout.addLayout(botoes_layout)

        # Tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(len(self.dados.columns))
        self.tabela.setHorizontalHeaderLabels(self.dados.columns)
        self.tabela.cellClicked.connect(self.carregar_dado_selecionado)
        layout.addWidget(self.tabela)

        self.atualizar_tabela()

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def carregar_dados(self):
        if os.path.exists(self.arquivo_csv):
            self.dados = pd.read_csv(self.arquivo_csv)

    def salvar_dados(self):
        self.dados.to_csv(self.arquivo_csv, index=False)

    def atualizar_tabela(self):
        self.tabela.setRowCount(len(self.dados))
        for i, row in self.dados.iterrows():
            for j, col in enumerate(self.dados.columns):
                self.tabela.setItem(i, j, QTableWidgetItem(str(row[col])))

    def carregar_dado_selecionado(self, row, column):
        self.matricula_input.setText(str(self.tabela.item(row, 0).text()))
        self.nome_input.setText(str(self.tabela.item(row, 1).text()))
        self.curso_input.setText(str(self.tabela.item(row, 2).text()))
        self.n1_input.setText(str(self.tabela.item(row, 3).text()))
        self.n2_input.setText(str(self.tabela.item(row, 4).text()))
        self.n3_input.setText(str(self.tabela.item(row, 5).text()))

    def calcular_media_status(self, n1, n2, n3):
        media = (n1 + n2 + n3) / 3
        status = "Aprovado" if media >= 60 else "Reprovado"
        return media, status

    def adicionar_dado(self):
        matricula = self.matricula_input.text().strip()
        nome = self.nome_input.text().strip()
        curso = self.curso_input.text().strip()
        n1_text = self.n1_input.text().replace(',', '.').strip()
        n2_text = self.n2_input.text().replace(',', '.').strip()
        n3_text = self.n3_input.text().replace(',', '.').strip()

        if not (matricula and nome and curso and n1_text and n2_text and n3_text):
            QMessageBox.warning(self, "Erro", "Todos os campos devem ser preenchidos.")
            return

        try:
            n1 = float(n1_text)
            n2 = float(n2_text)
            n3 = float(n3_text)
        except ValueError:
            QMessageBox.warning(self, "Erro", "Digite notas válidas (ex: 85.5 ou 85,5).")
            return

        media, status = self.calcular_media_status(n1, n2, n3)

        self.dados.loc[len(self.dados)] = [
            matricula, nome, curso, n1, n2, n3, round(media, 2), status
        ]
        self.salvar_dados()
        self.atualizar_tabela()
        self.limpar_campos()

    def atualizar_dado(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Erro", "Nenhum item selecionado para atualizar.")
            return

        matricula = self.matricula_input.text().strip()
        nome = self.nome_input.text().strip()
        curso = self.curso_input.text().strip()
        n1_text = self.n1_input.text().replace(',', '.').strip()
        n2_text = self.n2_input.text().replace(',', '.').strip()
        n3_text = self.n3_input.text().replace(',', '.').strip()

        if not (matricula and nome and curso and n1_text and n2_text and n3_text):
            QMessageBox.warning(self, "Erro", "Todos os campos devem ser preenchidos.")
            return

        try:
            n1 = float(n1_text)
            n2 = float(n2_text)
            n3 = float(n3_text)
        except ValueError:
            QMessageBox.warning(self, "Erro", "Digite notas válidas.")
            return

        media, status = self.calcular_media_status(n1, n2, n3)

        self.dados.iloc[row] = [matricula, nome, curso, n1, n2, n3, round(media, 2), status]
        self.salvar_dados()
        self.atualizar_tabela()
        self.limpar_campos()

    def deletar_dado(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Erro", "Nenhum item selecionado para deletar.")
            return

        self.dados = self.dados.drop(self.dados.index[row]).reset_index(drop=True)
        self.salvar_dados()
        self.atualizar_tabela()
        self.limpar_campos()

    def limpar_campos(self):
        self.matricula_input.clear()
        self.nome_input.clear()
        self.curso_input.clear()
        self.n1_input.clear()
        self.n2_input.clear()
        self.n3_input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = SistemaNotas()
    janela.show()
    sys.exit(app.exec_())
