import json
import os
from datetime import datetime, timezone, timedelta
from Classe.Pasta import Pasta
from ListaEncadeada.NoPasta import NoPasta

def mostrar_pasta(no, nivel=0):
    while no:
        print("   " * nivel + f"📁 {no.pasta.nome}")
        for arq in no.pasta.arquivos:
            print("   " * (nivel+1) + f"- {arq}")
        if no.pasta.subpastas:
            mostrar_pasta(no.pasta.subpastas, nivel+1)
        no = no.proximo

class ManipuladorPasta:
    def __init__(self, caminho):
        self.caminho = caminho
        self.raiz = None
        self.no_raiz = None
        self.carregar_estrutura()

    def carregar_estrutura(self):
        pasta_cache = os.path.join(os.getcwd(), "cache")
        os.makedirs(pasta_cache, exist_ok=True)
        
        cache_files = [f for f in os.listdir(pasta_cache) if f.startswith("cache_") and f.endswith(".json")]
        if cache_files:
            cache_files.sort(key=lambda f: os.path.getmtime(os.path.join(pasta_cache, f)), reverse=True)
            latest_file = cache_files[0]
            
            timestamp_str = latest_file[6:-5]
            try:
                dt = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
                dt = dt.replace(tzinfo=timezone(timedelta(hours=-3)))  # Define fuso de Brasília
                now = datetime.now(timezone(timedelta(hours=-3)))  # Horário atual em Brasília
                age_min = (now - dt).total_seconds() / 60
                
                if age_min <= 30:
                    caminho_arquivo = os.path.join(pasta_cache, latest_file)
                    with open(caminho_arquivo, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.raiz = Pasta.from_dict(data)
                    self.no_raiz = NoPasta(self.raiz)
                    print("✅ Estrutura carregada do cache.")
                    return
                else:
                    resposta = input(f"O cache tem {age_min:.1f} minutos. Deseja refazer? (s/n): ")
                    if resposta.lower() in ['s', 'y', 'sim']:
                        self.raiz = Pasta(self.caminho)
                        self.no_raiz = NoPasta(self.raiz)
                        self.salvar_cache()
                        return
                    else:
                        caminho_arquivo = os.path.join(pasta_cache, latest_file)
                        with open(caminho_arquivo, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        self.raiz = Pasta.from_dict(data)
                        self.no_raiz = NoPasta(self.raiz)
                        print("✅ Estrutura carregada do cache antigo.")
                        return
            except ValueError as e:
                print(f"Erro ao processar timestamp do arquivo {latest_file}: {e}")
                pass
            except Exception as e:
                print(f"Erro ao carregar cache {latest_file}: {e}")
                pass
        
        self.raiz = Pasta(self.caminho)
        self.no_raiz = NoPasta(self.raiz)
        self.salvar_cache()

    def salvar_cache(self):
        pasta_cache = os.path.join(os.getcwd(), "cache")
        timestamp = datetime.now(timezone(timedelta(hours=-3))).strftime('%Y-%m-%d_%H-%M-%S')  # Horário de Brasília
        caminho_arquivo = os.path.join(pasta_cache, f"cache_{timestamp}.json")
        
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            json.dump(self.raiz.to_dict(), f, indent=4, ensure_ascii=False)
        
        print(f"✅ Cache salvo em {caminho_arquivo}")

    def mostrar(self):
        mostrar_pasta(self.no_raiz)