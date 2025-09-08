from Manipulador.ManipuladorPasta import ManipuladorPasta

class ControladorProjeto:
    def __init__(self):
        self.caminho_pasta = "./Arq"
        self.manipulador = ManipuladorPasta(self.caminho_pasta)

    def executar(self):
        print("\nExibindo estrutura da pasta:")
        self.manipulador.mostrar()