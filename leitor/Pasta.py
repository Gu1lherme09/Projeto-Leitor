import os
from .Arquivo import Arquivo
from .NoPasta import NoPasta

class Pasta:
    def __init__(self, caminho: str, ler_conteudo: bool = True):
        self.nome = os.path.basename(caminho)
        self.caminho_completo = caminho
        self.arquivos = []
        self.subpastas = None
        if ler_conteudo:
            self._ler_conteudo(caminho)

    def _ler_conteudo(self, caminho: str):
        anterior = None

        # 🔒 protege o os.listdir
        try:
            itens = os.listdir(caminho)
        except PermissionError:
            print(f"[PERMISSÃO NEGADA] Não foi possível listar: {caminho}")
            return
        except OSError as e:
            print(f"[ERRO OS] Erro ao listar {caminho}: {e}")
            return

        for item in itens:
            full_path = os.path.join(caminho, item)

            # Arquivo normal
            if os.path.isfile(full_path):
                try:
                    nome, extensao = os.path.splitext(item)
                    extensao = extensao.lstrip(".")
                    tamanho = os.path.getsize(full_path)
                    self.arquivos.append(Arquivo(nome, extensao, tamanho, full_path))
                except (PermissionError, OSError) as e:
                    print(f"[ERRO ARQUIVO] Ignorando {full_path}: {e}")
                continue

            # Subpasta
            if os.path.isdir(full_path):
                try:
                    nova_pasta = Pasta(full_path)  # continua recursivo
                except PermissionError as e:
                    print(f"[PERMISSÃO NEGADA] Ignorando pasta {full_path}: {e}")
                    continue
                except OSError as e:
                    print(f"[ERRO OS] Ignorando pasta {full_path}: {e}")
                    continue

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
    def from_dict(cls, data: dict):
        """
        Reconstrói a árvore de Pasta a partir do dict (cache.json),
        sem reler o disco de novo.
        """
        # NÃO ler conteúdo aqui
        pasta = cls(data["caminho_completo"], ler_conteudo=False)

        # arquivos vindos do cache
        pasta.arquivos = [Arquivo.from_dict(a) for a in data.get("arquivos", [])]

        # subpastas vindas do cache (lista encadeada)
        pasta.subpastas = None
        anterior = None

        for subpasta_data in data.get("subpastas", []):
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
