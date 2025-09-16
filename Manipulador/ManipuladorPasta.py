# Manipulador/ManipuladorPasta.py
import json
import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from Classe.Pasta import Pasta
from ListaEncadeada.NoPasta import NoPasta


def mostrar_pasta(no, nivel=0):
    """Exibe a árvore de pastas e arquivos de forma hierárquica."""
    while no:
        print("  " * nivel + f"📁 {no.pasta.nome}")
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

    def carregar_estrutura(self):
        """Carrega estrutura do cache ou cria nova árvore."""
        pasta_cache = os.path.join(os.getcwd(), "cache")
        os.makedirs(pasta_cache, exist_ok=True)
        cache_file = os.path.join(pasta_cache, "cache.json")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                timestamp_str = data.get("data", "")
                dt = datetime.strptime(timestamp_str, '%d_%m_%Y,%H:%M')
                dt = dt.replace(tzinfo=timezone(timedelta(hours=-3)))
                now = datetime.now(timezone(timedelta(hours=-3)))
                age_min = (now - dt).total_seconds() / 60

                if age_min <= 30:
                    self.raiz = Pasta.from_dict(data["estrutura"])
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
                        self.raiz = Pasta.from_dict(data["estrutura"])
                        self.no_raiz = NoPasta(self.raiz)
                        print("✅ Estrutura carregada do cache antigo.")
                        return
            except Exception as e:
                print(f"Erro ao carregar cache: {e}")

        # Caso não exista cache
        self.raiz = Pasta(self.caminho)
        self.no_raiz = NoPasta(self.raiz)
        self.salvar_cache()

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
        print(f"✅ Cache salvo em {cache_file}")

    def mostrar(self):
        """Mostra a árvore de arquivos e pastas."""
        mostrar_pasta(self.no_raiz)

    def detectar_duplicatas(self):
        """
        Detecta arquivos duplicados usando apenas MD5.
        Otimização: primeiro agrupa por tamanho para reduzir hashes desnecessários.
        """
        from Classe.Arquivo import Arquivo  # garantir import local

        tamanho_dict = defaultdict(list)
        for caminho_pasta, arquivo in self.raiz.coletar_arquivos():
            # garantir que caminho exista
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
                # calcular hash se ainda não calculado
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
            print("\n✅ Nenhum arquivo duplicado encontrado.")
            return

        print("\n📑 Arquivos duplicados encontrados (usando MD5):")
        for tamanho, hash_value, grupo in duplicatas:
            print(f"\nTamanho: {tamanho} bytes  - Hash: {hash_value}")
            for i, (caminho, arquivo) in enumerate(grupo, 1):
                caminho_relativo = os.path.relpath(os.path.join(caminho, f"{arquivo.nome}.{arquivo.extensao}"), self.caminho)
                print(f" {i}. {arquivo.nome}.{arquivo.extensao} em {caminho_relativo}")

        print(f"\n📈 Estatísticas:")
        print(f" Arquivos duplicados: {total_duplicados}")
        print(f" Espaço desperdiçado: {espaco_duplicado / (1024 * 1024):.2f} MB")
