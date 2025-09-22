# Manipulador/ManipuladorPasta.py
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from Classe.Pasta import Pasta
from ListaEncadeada.NoPasta import NoPasta


def mostrar_pasta(no, nivel=0):
    """Exibe a árvore de pastas e arquivos de forma hierárquica."""
    while no:
        print("  " * nivel + f"Pasta: {no.pasta.nome}")
        for arq in no.pasta.arquivos:
            print("  " * (nivel + 1) + f"- {arq}")
        if no.pasta.subpastas:
            mostrar_pasta(no.pasta.subpastas, nivel + 1)
        no = no.proximo


class ManipuladorPasta:
    def __init__(self, caminho):
        self.caminho = caminho
        self.raiz = None
        self.no_raiz = None
        self.carregar_estrutura()

    def _carregar_cache_antigo(self, cache_file):
        """Carrega o cache antigo e o retorna como um dicionário de arquivos."""
        if not os.path.exists(cache_file):
            return {}
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                dados_cache = json.load(f)
            
            cache_map = {}
            def extrair_arquivos(pasta_dict):
                for arq_dict in pasta_dict.get("arquivos", []):
                    caminho = arq_dict.get("caminho_completo")
                    if caminho:
                        cache_map[caminho] = arq_dict
                for subpasta_dict in pasta_dict.get("subpastas", []):
                    extrair_arquivos(subpasta_dict)

            extrair_arquivos(dados_cache["estrutura"])
            print(f"Cache antigo encontrado com {len(cache_map)} arquivos.")
            return cache_map
        except Exception as e:
            print(f"Aviso: Nao foi possivel ler o cache antigo. Um novo sera criado. Erro: {e}")
            return {}

    def carregar_estrutura(self):
        """Carrega a estrutura de pastas"""
        pasta_cache = os.path.join(os.getcwd(), "cache")
        os.makedirs(pasta_cache, exist_ok=True)
        cache_file = os.path.join(pasta_cache, "cache.json")

        mapa_cache_antigo = self._carregar_cache_antigo(cache_file)
        
        print("Analisando estrutura de pastas atual...")
        self.raiz = Pasta(self.caminho)
        
        arquivos_para_hashear = []
        for _, arquivo_novo in self.raiz.coletar_arquivos():
            caminho_novo = arquivo_novo.caminho_completo
            if caminho_novo in mapa_cache_antigo:
                arquivo_antigo = mapa_cache_antigo[caminho_novo]
                if arquivo_novo.tamanho == arquivo_antigo.get("tamanho"):
                    hash_antigo = arquivo_antigo.get("hash_md5")
                    if hash_antigo:
                        arquivo_novo.hash_md5 = hash_antigo
                        continue
            
            arquivos_para_hashear.append(arquivo_novo)

        if arquivos_para_hashear:
            print(f"{len(arquivos_para_hashear)} arquivos novos ou modificados para calcular o hash.")
        else:
            print("Nenhum arquivo novo ou modificado detectado.")

        self.no_raiz = NoPasta(self.raiz)
        self.salvar_cache()
        print("Estrutura de arquivos carregada e cache atualizado.")

    def calcular_tamanho_total_cache(self):
        """Calcula o tamanho total de todos os arquivos na estrutura carregada."""
        if not self.raiz:
            return 0
        return sum(arquivo.tamanho for _, arquivo in self.raiz.coletar_arquivos())

    def salvar_cache(self):
        """Salva a estrutura atual no cache JSON."""
        pasta_cache = os.path.join(os.getcwd(), "cache")
        cache_file = os.path.join(pasta_cache, "cache.json")
        timestamp = datetime.now(timezone(timedelta(hours=-3))).strftime('%d_%m_%Y,%H:%M')
        data = {
            "data": timestamp,
            "estrutura": self.raiz.to_dict()
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Cache salvo em {cache_file}")

    def mostrar(self):
        """Mostra a árvore de arquivos e pastas."""
        mostrar_pasta(self.no_raiz)

    def detectar_duplicatas(self):
        """Detecta arquivos duplicados e imprime os resultados."""
        from Classe.Arquivo import Arquivo

        tamanho_dict = defaultdict(list)
        if not self.raiz:
            self.carregar_estrutura()

        for caminho_pasta, arquivo in self.raiz.coletar_arquivos():
            if arquivo.caminho_completo and os.path.exists(arquivo.caminho_completo):
                tamanho_dict[arquivo.tamanho].append((caminho_pasta, arquivo))

        duplicatas = []
        total_duplicados = 0
        espaco_duplicado = 0

        for tamanho, arquivos in tamanho_dict.items():
            if len(arquivos) < 2:
                continue

            hash_dict = defaultdict(list)
            for caminho, arquivo in arquivos:
                if not arquivo.hash_md5:
                    arquivo._calcular_hash()
                if arquivo.hash_md5:
                    hash_dict[arquivo.hash_md5].append((caminho, arquivo))

            for hash_value, grupo in hash_dict.items():
                if len(grupo) > 1:
                    duplicatas.append((tamanho, hash_value, grupo))
                    total_duplicados += len(grupo) - 1
                    espaco_duplicado += (len(grupo) - 1) * tamanho
        
        if not duplicatas:
            print("\nNenhum arquivo duplicado encontrado.")
            return

        print("\nArquivos duplicados encontrados (usando MD5):")
        for tamanho, hash_value, grupo in duplicatas:
            print(f"\nTamanho: {tamanho} bytes  - Hash: {hash_value}")
            for i, (caminho, arquivo) in enumerate(grupo, 1):
                caminho_relativo = os.path.relpath(os.path.join(caminho, f"{arquivo.nome}.{arquivo.extensao}"), self.caminho)
                print(f" {i}. {arquivo.nome}.{arquivo.extensao} em {caminho_relativo}")

        print(f"\nEstatisticas:")
        print(f" Arquivos duplicados: {total_duplicados}")
        print(f" Espaco desperdicado: {espaco_duplicado / (1024 * 1024):.2f} MB")
