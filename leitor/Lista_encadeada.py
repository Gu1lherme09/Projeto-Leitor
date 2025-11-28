from .NoPasta import NoPasta
from .Pasta import Pasta

class ListaPastas:
    # Representa uma lista encadeada de objetos Pasta, usando NoPasta como nós.
    # Esta estrutura é usada internamente para gerenciar subpastas de forma hierárquica.
    def __init__(self):
        self.inicio = None # O primeiro nó da lista.
        self.fim = None    # O último nó da lista, para adição eficiente.

    def adicionar(self, pasta: Pasta):
        # Adiciona uma nova Pasta ao final da lista encadeada.
        novo_no = NoPasta(pasta)
        if self.inicio is None:
            self.inicio = novo_no
            self.fim = novo_no
        else:
            self.fim.proximo = novo_no
            self.fim = novo_no

    def mostrar(self):
        # Percorre e imprime cada Pasta na lista (principalmente para depuração).
        atual = self.inicio
        while atual:
            print(atual.pasta)
            atual = atual.proximo
