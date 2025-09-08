from ListaEncadeada.NoPasta import NoPasta
from Classe.Pasta import Pasta

class ListaPastas:
    def __init__(self):
        self.inicio = None
        self.fim = None

    def adicionar(self, pasta: Pasta):
        novo_no = NoPasta(pasta)
        if self.inicio is None:
            self.inicio = novo_no
            self.fim = novo_no
        else:
            self.fim.proximo = novo_no
            self.fim = novo_no

    def mostrar(self):
        atual = self.inicio
        while atual:
            print(atual.pasta)
            atual = atual.proximo
