# ControladorProjeto.py
import shutil
import os
from Manipulador.ManipuladorPasta import ManipuladorPasta

class ControladorProjeto:
    def __init__(self):
        self.caminho_pasta = "./Arq"
        self.manipulador = ManipuladorPasta(self.caminho_pasta)

    def verificar_espaco_livre(self):
        """Verifica o espaço livre no disco e compara com o tamanho do cache."""
        try:
            total, usado, livre = shutil.disk_usage(os.path.abspath(self.caminho_pasta))
            tamanho_cache_bytes = self.manipulador.calcular_tamanho_total_cache()
            
            print("\nAnalise de Espaco em Disco:")
            print(f"  - Espaco livre no disco: {livre / (1024**3):.2f} GB")
            print(f"  - Espaco total ocupado pela pasta '{self.caminho_pasta}': {tamanho_cache_bytes / (1024**2):.2f} MB")
            
            if tamanho_cache_bytes > livre:
                print("  - Atencao: O tamanho da pasta analisada é maior que o espaco livre em disco!")

        except FileNotFoundError:
            print(f"\nErro: Nao foi possivel analisar o espaco em disco. O caminho '{self.caminho_pasta}' existe?")
        except Exception as e:
            print(f"\nOcorreu um erro inesperado ao verificar o espaco em disco: {e}")


    def executar(self):
        # Tarefa 5: Verificar espaço livre antes de outras operações
        self.verificar_espaco_livre()

        print("\nExibindo estrutura da pasta:")
        self.manipulador.mostrar()
        print("\nDeseja verificar arquivos duplicados? (s/n): ", end="")
        if input().lower() in ['s', 'y', 'sim']:
            # agora sempre usa MD5
            self.manipulador.detectar_duplicatas()
