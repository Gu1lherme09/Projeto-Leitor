class Arquivo:
    def __init__(self, nome: str, extensao: str, tamanho: int):
        self.nome = nome
        self.extensao = extensao
        self.tamanho = tamanho  # tamanho em bytes

    def __repr__(self):
        tamanho_kb = self.tamanho / 1024
        return f"{self.nome}.{self.extensao} ({tamanho_kb:.2f} KB)"

    def to_dict(self):
        # Converte para KB ao gerar o dicionário
        tamanho_kb = self.tamanho / 1024
        return {
            "nome": self.nome,
            "extensao": self.extensao,
            "tamanho_kb": round(tamanho_kb, 2)
        }
