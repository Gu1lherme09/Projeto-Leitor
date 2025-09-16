# ControladorProjeto.py
from Manipulador.ManipuladorPasta import ManipuladorPasta

class ControladorProjeto:
    def __init__(self):
        self.caminho_pasta = "./Arq"
        self.manipulador = ManipuladorPasta(self.caminho_pasta)

    def executar(self):
        print("\nExibindo estrutura da pasta:")
        self.manipulador.mostrar()
        print("\nDeseja verificar arquivos duplicados? (s/n): ", end="")
        if input().lower() in ['s', 'y', 'sim']:
            # agora sempre usa MD5
            self.manipulador.detectar_duplicatas()
