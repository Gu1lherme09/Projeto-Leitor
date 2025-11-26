import os
from Classe.Arquivo import Arquivo
from ListaEncadeada.NoPasta import NoPasta

class Pasta:
    def __init__(self, caminho: str):
        self.nome = os.path.basename(caminho)
        self.caminho_completo = caminho
        self.arquivos = []
        self.subpastas = None
        self._ler_conteudo(caminho)

    def _ler_conteudo(self, caminho: str):
        anterior = None
        for item in os.listdir(caminho):
            full_path = os.path.join(caminho, item)
            if os.path.isfile(full_path):
                nome, extensao = os.path.splitext(item)
                extensao = extensao.lstrip(".")
                tamanho = os.path.getsize(full_path)
                self.arquivos.append(Arquivo(nome, extensao, tamanho, full_path))
            elif os.path.isdir(full_path):
                nova_pasta = Pasta(full_path)
                novo_no = NoPasta(nova_pasta)
                if self.subpastas is None:
                    self.subpastas = novo_no
                else:
                    anterior.proximo = novo_no
                anterior = novo_no

    def __repr__(self):
        return f"Pasta({self.nome}, arquivos={len(self.arquivos)})"

    def to_dict(self):
        return {
            "nome": self.nome,
            "caminho_completo": self.caminho_completo,
            "arquivos": [a.to_dict() for a in self.arquivos],
            "subpastas": self._subpastas_to_list(self.subpastas)
        }

    def _subpastas_to_list(self, no):
        resultado = []
        atual = no
        while atual:
            resultado.append(atual.pasta.to_dict())
            atual = atual.proximo
        return resultado

    @classmethod
    def from_dict(cls, data):
        pasta = cls(data["caminho_completo"])
        pasta.arquivos = [Arquivo.from_dict(a) for a in data["arquivos"]]
        anterior = None
        for subpasta_data in data["subpastas"]:
            subpasta = Pasta.from_dict(subpasta_data)
            novo_no = NoPasta(subpasta)
            if pasta.subpastas is None:
                pasta.subpastas = novo_no
            else:
                anterior.proximo = novo_no
            anterior = novo_no
        return pasta

    def coletar_arquivos(self):
        arquivos = [(self.caminho_completo, arquivo) for arquivo in self.arquivos]
        atual = self.subpastas
        while atual:
            arquivos.extend(atual.pasta.coletar_arquivos())
            atual = atual.proximo
        return arquivos