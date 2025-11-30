# ControladorProjeto.py
from .ManipuladorPasta import ManipuladorPasta

class ControladorProjeto:
    def __init__(self):
        self.caminho_pasta = "./Arq"
        self.manipulador = ManipuladorPasta(self.caminho_pasta)

    def executar(self):
        print("\nExibindo estrutura da pasta:")
        self.manipulador.mostrar()
        print("\nDeseja verificar arquivos duplicados? (s/n): ", end="")
        if input().lower() in ['s', 'y', 'sim']:
            self.manipulador.detectar_duplicatas()
        while True:
            print("\nDeseja buscar um arquivo ou pasta? (s/n): ", end="")
            if input().lower() not in ['s', 'y', 'sim']:
                break

            termo = input("Digite o nome ou parte do nome para buscar: ")
            self.manipulador.buscar(termo)


