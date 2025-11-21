# ControladorProjeto.py
from Manipulador.ManipuladorPasta import ManipuladorPasta

class ControladorProjeto:
    def __init__(self):
        self.caminho_pasta = "Projeto-Leitor\Arq"
        self.manipulador = ManipuladorPasta(self.caminho_pasta)

    def executar(self):
        print("\nExibindo estrutura da pasta:")
        self.manipulador.mostrar()
        print("\nDeseja verificar arquivos duplicados? (s/n): ", end="")
        if input().lower() in ['s', 'y', 'sim']:
            self.manipulador.detectar_duplicatas()
        while True:
            print("\nDeseja buscar algo? (s/n): ", end="")
            if input().lower() not in ['s', 'y', 'sim']:
                break

            print("\nTipos de busca:")
            print("1 - Buscar pasta")
            print("2 - Buscar arquivo pelo nome")
            print("3 - Buscar por extensão")
            op = input("Escolha uma opção (1/2/3): ")

            termo = input("Digite o termo de busca: ")

            if op == "1":
                self.manipulador.buscar_pasta(termo)
            elif op == "2":
                self.manipulador.buscar_arquivo(termo)
            elif op == "3":
                self.manipulador.buscar_extensao(termo)
            else:
                print("❌ Opção inválida.")


