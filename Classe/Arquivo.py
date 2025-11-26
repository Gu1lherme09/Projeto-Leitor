# Classe/Arquivo.py
import hashlib
import os

class Arquivo:
    def __init__(self, nome: str, extensao: str, tamanho: int, caminho_completo: str = None):
        self.nome = nome
        self.extensao = extensao
        self.tamanho = tamanho  # tamanho em bytes
        self.caminho_completo = caminho_completo
        self.hash_md5 = None

    def _calcular_hash(self):
        """Calcula o hash MD5 do arquivo baseado no seu conteúdo"""
        try:
            hash_md5 = hashlib.md5()
            if not self.caminho_completo or not os.path.exists(self.caminho_completo):
                self.hash_md5 = None
                return
            with open(self.caminho_completo, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):  # Bloco de 64 KB
                    hash_md5.update(chunk)
            self.hash_md5 = hash_md5.hexdigest()
        except Exception as e:
            print(f"Erro ao calcular hash de {self.caminho_completo}: {e}")
            self.hash_md5 = None

    def comparar_byte_a_byte(self, outro_arquivo):
        """Compara dois arquivos byte a byte, retornando cedo na primeira diferença"""
        if self.tamanho != outro_arquivo.tamanho:
            return False
        try:
            with open(self.caminho_completo, "rb") as f1, open(outro_arquivo.caminho_completo, "rb") as f2:
                while True:
                    chunk1 = f1.read(65536)  # Bloco de 64 KB
                    chunk2 = f2.read(65536)
                    if chunk1 != chunk2:
                        return False
                    if not chunk1:  # Fim do arquivo
                        return True
        except Exception as e:
            print(f"Erro ao comparar {self.caminho_completo} com {outro_arquivo.caminho_completo}: {e}")
            return False

    def __repr__(self):
        hash_str = f" [hash={self.hash_md5[:8]}...]" if self.hash_md5 else ""
        return f"{self.nome}.{self.extensao} ({self.tamanho} bytes){hash_str}"

    # ================================
    # Métodos de serialização / cache
    # ================================

    def to_dict(self):
        """Converte o objeto em dicionário para salvar no cache"""
        return {
            "nome": self.nome,
            "extensao": self.extensao,
            "tamanho": self.tamanho,
            "hash_md5": self.hash_md5,
            "caminho_completo": self.caminho_completo
        }

    @classmethod
    def from_dict(cls, data):
        """Cria um objeto Arquivo a partir de um dicionário"""
        arquivo = cls(
            nome=data["nome"],
            extensao=data["extensao"],
            tamanho=data["tamanho"],
            caminho_completo=data.get("caminho_completo")
        )
        arquivo.hash_md5 = data.get("hash_md5")
        return arquivo
