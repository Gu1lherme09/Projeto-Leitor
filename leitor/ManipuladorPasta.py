# Manipulador/ManipuladorPasta.py
import json
import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from .Pasta import Pasta
from .NoPasta import NoPasta

class ManipuladorPasta:
    def __init__(self, caminho, interativo=True):
        self.caminho = caminho
        self.raiz = None
        self.no_raiz = None
        self.carregar_estrutura(interativo=interativo)

    
    def carregar_estrutura(self, forcar_recriacao=False, interativo=True):
        """Carrega estrutura do cache ou cria nova árvore."""
        pasta_cache = os.path.join(os.getcwd(), "cache")
        os.makedirs(pasta_cache, exist_ok=True)
        cache_file = os.path.join(pasta_cache, "cache.json")

        if not forcar_recriacao and os.path.exists(cache_file):
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
                    if interativo:
                        resposta = input(f"O cache tem {age_min:.1f} minutos. Deseja refazer? (s/n): ")
                        if resposta.lower() not in ['s', 'y', 'sim']:
                            self.raiz = Pasta.from_dict(data["estrutura"])
                            self.no_raiz = NoPasta(self.raiz)
                            print("✅ Estrutura carregada do cache antigo.")
                            return
                    else:
                        # modo web: usa cache antigo SEM perguntar
                        self.raiz = Pasta.from_dict(data["estrutura"])
                        self.no_raiz = NoPasta(self.raiz)
                        print("✅ Estrutura carregada do cache (modo web).")
                        return

            except Exception as e:
                print(f"Erro ao carregar cache: {e}")

        self.raiz = Pasta(self.caminho)
        self.no_raiz = NoPasta(self.raiz)
        self.salvar_cache()
        print("✅ Cache recriado.")


    def salvar_cache(self, extra_meta=None):
        pasta_cache = os.path.join(os.getcwd(), "cache")
        os.makedirs(pasta_cache, exist_ok=True)
        cache_file = os.path.join(pasta_cache, "cache.json")

        data = {
            "data": datetime.now(timezone(timedelta(hours=-3))).strftime('%d_%m_%Y,%H:%M'),
            "estrutura": self.raiz.to_dict(),
        }

        if extra_meta:
            data.update(extra_meta)  # ex: {"hash_calculado": True}

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def detectar_duplicatas(self):
        """
        Detecta arquivos duplicados usando apenas MD5.
        Otimização: primeiro agrupa por tamanho para reduzir hashes desnecessários.
        """
        from .Arquivo import Arquivo  # garantir import local

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

