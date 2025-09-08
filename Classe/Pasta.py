import os
from Classe.Arquivo import Arquivo
from ListaEncadeada.NoPasta import NoPasta

class Pasta:
    def __init__(self, caminho: str):
        self.nome = os.path.basename(caminho)
        self.arquivos = []
        self.subpastas = None  # raiz da lista encadeada de subpastas
        self._ler_conteudo(caminho)

    def _ler_conteudo(self, caminho: str):
        anterior = None
        for item in os.listdir(caminho):
            full_path = os.path.join(caminho, item)
            if os.path.isfile(full_path):
                nome, extensao = os.path.splitext(item)
                extensao = extensao.lstrip(".")
                tamanho = os.path.getsize(full_path)
                self.arquivos.append(Arquivo(nome, extensao, tamanho))
            elif os.path.isdir(full_path):
                nova_pasta = Pasta(full_path)
                novo_no = NoPasta(nova_pasta)
                if self.subpastas is None:
                    self.subpastas = novo_no
                else:
                    anterior.proximo = novo_no
                anterior = novo_no

    def __repr__(self):
        return f"Pasta({self.nome}, arquivos={self.arquivos})"

    def to_dict(self):
        """Transforma a pasta e suas subpastas em dicionário"""
        return {
            "nome": self.nome,
            "arquivos": [a.to_dict() for a in self.arquivos],
            "subpastas": self._subpastas_to_list(self.subpastas)
        }

    def _subpastas_to_list(self, no):
        """Percorre lista encadeada de subpastas e gera lista de dicionários"""
        resultado = []
        atual = no
        while atual:
            resultado.append(atual.pasta.to_dict())
            atual = atual.proximo
        return resultado
