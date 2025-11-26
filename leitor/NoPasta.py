class NoPasta:
    def __init__(self, pasta):
        self.pasta = pasta
        self.proximo = None  # irmão (próxima pasta no mesmo nível)
        self.filho = None    # subpasta (lista de filhos)