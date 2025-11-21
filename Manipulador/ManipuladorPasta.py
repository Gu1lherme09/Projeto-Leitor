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

    def carregar_estrutura(self, forcar_recriacao=False):
        """Carrega estrutura do cache ou cria nova árvore."""
        pasta_cache = os.path.join(os.getcwd(), "cache")
        os.makedirs(pasta_cache, exist_ok=True)
        cache_file = os.path.join(pasta_cache, "cache.json")

        # Se não for para forçar recriação e existir cache, tenta usar
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
                    # usa cache "novo"
                    self.raiz = Pasta.from_dict(data["estrutura"])
                    self.no_raiz = NoPasta(self.raiz)
                    print("✅ Estrutura carregada do cache.")
                    return
                else:
                    # cache velho, pergunta se usa mesmo assim
                    resposta = input(f"O cache tem {age_min:.1f} minutos. Deseja refazer? (s/n): ")
                    if resposta.lower() not in ['s', 'y', 'sim']:
                        self.raiz = Pasta.from_dict(data["estrutura"])
                        self.no_raiz = NoPasta(self.raiz)
                        print("✅ Estrutura carregada do cache antigo.")
                        return
                    # se respondeu que quer refazer, cai para recriação lá embaixo

            except Exception as e:
                print(f"Erro ao carregar cache: {e}")

        # Antes de tentar criar a Pasta a partir do caminho, garanta que o caminho existe
        # e trate o caso em que o caminho contém o nome do diretório atual duplicado.
        caminho_original = self.caminho
        if not os.path.exists(self.caminho):
            try:
                # Normaliza separadores
                normalized = self.caminho.replace("\\", os.sep).replace("/", os.sep)
                cwd_base = os.path.basename(os.getcwd())
                prefix = cwd_base + os.sep

                # Se o caminho começa com o nome da pasta atual (ex.: "Projeto-Leitor\\Arq")
                # e esse prefixo causa duplicação, remova o prefixo.
                if normalized.startswith(prefix):
                    candidate = normalized[len(prefix):]
                    if os.path.exists(candidate):
                        self.caminho = candidate
                        print(f"⚠️ Ajustado caminho de '{caminho_original}' para '{self.caminho}' (evitou duplicação).")
                    else:
                        os.makedirs(candidate, exist_ok=True)
                        self.caminho = candidate
                        print(f"⚠️ Criada pasta '{self.caminho}' (ajuste do caminho original '{caminho_original}').")
                else:
                    os.makedirs(self.caminho, exist_ok=True)
                    print(f"⚠️ Criada pasta '{self.caminho}' porque não existia.")
            except Exception as e:
                print(f"Erro ao preparar caminho '{self.caminho}': {e}")
                fallback = os.path.join(os.getcwd(), "Arq")
                os.makedirs(fallback, exist_ok=True)
                self.caminho = fallback
                print(f"⚠️ Usando pasta fallback '{self.caminho}'.")

        self.raiz = Pasta(self.caminho)
        self.no_raiz = NoPasta(self.raiz)
        self.salvar_cache()
        print("✅ Cache recriado.")


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
                    # atenção: cheque se sua classe Arquivo tem esse método com este nome
                    try:
                        arquivo._calcular_hash()
                    except AttributeError:
                        # se o método tiver outro nome, trate aqui
                        pass
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

    def buscar_pasta(self, termo):
        termo = termo.lower()
        resultados = []

        def rec(no, caminho):
            while no:
                pasta = no.pasta
                caminho_atual = os.path.join(caminho, pasta.nome)

                if termo in pasta.nome.lower():
                    resultados.append((pasta.nome, caminho_atual, pasta))

                if pasta.subpastas:
                    rec(pasta.subpastas, caminho_atual)

                no = no.proximo

        rec(self.no_raiz, "")

        if not resultados:
            print(f"\n🔍 Nenhuma pasta encontrada com '{termo}'.")
            resp = input("Deseja refazer o cache? (s/n): ").strip().lower()
            if resp in ["s", "sim", "y"]:
                self.carregar_estrutura(forcar_recriacao=True)
            return

        print(f"\n📁 Pastas encontradas:")
        for i, (nome, caminho, p) in enumerate(resultados, 1):
            print(f"{i}. {nome}  --> {caminho}")

        print("\nEscolha uma opção:")
        print("1 - Abrir uma pasta específica")
        print("2 - Abrir TODAS as pastas encontradas")
        print("ENTER - Não abrir nada")

        opcao = input("Opção: ").strip()

        if opcao == "":
            return

        if opcao == "2":
            print("\n📂 Abrindo TODAS as pastas encontradas...")
            for _, _, pasta_obj in resultados:
                print(f"\n📂 Conteúdo da pasta: {pasta_obj.nome}")
                self._mostrar_recursivo_pasta(pasta_obj, 0)
            return

        if opcao == "1":
            escolha = input("Digite o número da pasta que deseja abrir: ").strip()

            if escolha.isdigit():
                idx = int(escolha) - 1

                if 0 <= idx < len(resultados):
                    _, _, pasta_obj = resultados[idx]
                    print(f"\n📂 Conteúdo da pasta: {pasta_obj.nome}")
                    self._mostrar_recursivo_pasta(pasta_obj, 0)
                else:
                    print("❌ Número inválido!")
            else:
                print("❌ Entrada inválida!")
            return

        print("❌ Opção inválida.")

    def buscar_extensao(self, termo):
        termo = termo.lower().strip()

        if not termo.startswith("."):
            termo = "." + termo

        resultados = []

        for caminho_pasta, arquivo in self.raiz.coletar_arquivos():
            nome_ext = f"{arquivo.nome}.{arquivo.extensao}".lower()
            if nome_ext.endswith(termo):
                resultados.append((nome_ext, caminho_pasta))

        if not resultados:
            print(f"\n🔍 Nenhum arquivo encontrado com extensão '{termo}'.")
            resp = input("Deseja refazer o cache? (s/n): ").strip().lower()
            if resp in ["s", "sim", "y"]:
                self.carregar_estrutura(forcar_recriacao=True)
            return

        print(f"\n📄 Arquivos encontrados com extensão '{termo}':")
        for i, (nome, caminho) in enumerate(resultados, 1):
            print(f"{i}. {nome}  -->  {caminho}")

    def buscar_arquivo(self, termo):
        termo = termo.lower()
        resultados = []

        for caminho_pasta, arquivo in self.raiz.coletar_arquivos():
            nome = arquivo.nome.lower()

            if termo in nome:
                nome_ext = f"{arquivo.nome}.{arquivo.extensao}"
                resultados.append((nome_ext, caminho_pasta))

        if not resultados:
            print(f"\n🔍 Nenhum arquivo encontrado contendo '{termo}' no nome do arquivo.")
            resp = input("Deseja refazer o cache? (s/n): ").strip().lower()
            if resp in ["s", "sim", "y"]:
                self.carregar_estrutura(forcar_recriacao=True)
            return

        print(f"\n📄 Arquivos encontrados:")
        for i, (nome, caminho) in enumerate(resultados, 1):
            print(f"{i}. {nome}  -->  {caminho}")
            
    def mostrar_conteudo_pasta(self, pasta):
        print(f"\n📂 Conteúdo da pasta: {pasta.nome}")
        self._mostrar_recursivo_pasta(pasta, 0)

    def _mostrar_recursivo_pasta(self, pasta, nivel):
        print("  " * nivel + f"📁 {pasta.nome}")

        # arquivos da pasta
        for arq in pasta.arquivos:
            print("  " * (nivel + 1) + f"- {arq.nome}.{arq.extensao}")

        # subpastas (percorrendo a lista ligada)
        sub = pasta.subpastas
        while sub is not None:
            self._mostrar_recursivo_pasta(sub.pasta, nivel + 1)
            sub = sub.proximo
