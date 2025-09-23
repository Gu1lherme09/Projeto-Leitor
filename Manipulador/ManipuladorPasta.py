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
        self.caminho_analisado = caminho
        self.floresta_cache = []
        self.carregar_estrutura()

    def _carregar_cache_antigo(self, cache_file):
        """Carrega a floresta de pastas do cache."""
        if not os.path.exists(cache_file):
            return []
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                dados_cache = json.load(f)
            
            floresta = [Pasta.from_dict(p) for p in dados_cache.get("estruturas", [])]
            print(f"Cache antigo encontrado com {len(floresta)} estruturas raiz.")
            return floresta
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Aviso: Nao foi possivel ler o cache antigo. Um novo sera criado. Erro: {e}")
            return []

    def carregar_estrutura(self):
        """Carrega e funde a estrutura de pastas de forma inteligente e cumulativa."""
        pasta_cache = os.path.join(os.getcwd(), "cache")
        os.makedirs(pasta_cache, exist_ok=True)
        cache_file = os.path.join(pasta_cache, "cache.json")

        self._mostrar_progresso(0.05, "Iniciando carregamento da estrutura...")
        self.floresta_cache = self._carregar_cache_antigo(cache_file)
        caminho_analise_norm = os.path.normpath(self.caminho_analisado)
        self._mostrar_progresso(0.20, "Verificando ancestrais comuns e fusao...")

        # Verifica se o novo caminho já está contido em alguma árvore existente
        for raiz in self.floresta_cache:
            if caminho_analise_norm.startswith(os.path.normpath(raiz.caminho_completo)):
                print("O caminho especificado já está (ou é subpasta de) uma estrutura em cache. Nenhuma ação necessária.")
                return # Para evitar re-análise e duplicatas

        # Lógica de fusão: Encontra um novo caminho raiz se necessário
        caminhos_a_unir = [c for c in self.floresta_cache if os.path.commonpath([c.caminho_completo, caminho_analise_norm]) == os.path.dirname(c.caminho_completo) or os.path.commonpath([c.caminho_completo, caminho_analise_norm]) == os.path.dirname(caminho_analise_norm)]
        
        if caminhos_a_unir:
            todos_caminhos = [c.caminho_completo for c in caminhos_a_unir] + [caminho_analise_norm]
            novo_caminho_raiz = os.path.commonpath(todos_caminhos)
            
            print(f"Detectado um ancestral comum. A nova raiz da análise será: {novo_caminho_raiz}")
            
            # Remove as estruturas que serão fundidas
            self.floresta_cache = [c for c in self.floresta_cache if c not in caminhos_a_unir]
            
            # O novo caminho de análise se torna o ancestral comum
            self.caminho_analisado = novo_caminho_raiz
            caminho_analise_norm = os.path.normpath(self.caminho_analisado)

        self._mostrar_progresso(0.30, "Filtrando cache existente...")

        # Remove estruturas que são subpastas do novo caminho de análise
        floresta_filtrada = [c for c in self.floresta_cache if not os.path.normpath(c.caminho_completo).startswith(caminho_analise_norm + os.sep)]
        removidas = len(self.floresta_cache) - len(floresta_filtrada)
        if removidas > 0:
            print(f"Foram removidas {removidas} estruturas de cache antigas que serão substituídas pela nova análise.")
        self.floresta_cache = floresta_filtrada
        self._mostrar_progresso(0.40, "Analisando nova estrutura...")

        # Análise da nova estrutura (ou da raiz comum)
        mapa_cache_antigo = self._mapear_arquivos_floresta(self.floresta_cache + caminhos_a_unir)
        print(f"Analisando {self.caminho_analisado}...")
        nova_estrutura = Pasta(self.caminho_analisado)

        # Reuso de Hash
        arquivos_para_hashear = []
        for _, arquivo_novo in nova_estrutura.coletar_arquivos():
            if arquivo_novo.caminho_completo in mapa_cache_antigo:
                arquivo_antigo = mapa_cache_antigo[arquivo_novo.caminho_completo]
                if arquivo_novo.tamanho == arquivo_antigo.tamanho and arquivo_antigo.hash_md5:
                    arquivo_novo.hash_md5 = arquivo_antigo.hash_md5
                    continue
            arquivos_para_hashear.append(arquivo_novo)

        if arquivos_para_hashear:
            print(f"Calculando hash para {len(arquivos_para_hashear)} arquivos novos ou modificados.")
            total_arquivos = len(arquivos_para_hashear)
            for i, arquivo in enumerate(arquivos_para_hashear):
                arquivo._calcular_hash()
                percentual = (i + 1) / total_arquivos
                self._mostrar_progresso(percentual, f"Analisando: {arquivo.nome}.{arquivo.extensao}")
            print()
        else:
            print("Nenhum arquivo novo ou modificado detectado.")

        self._mostrar_progresso(0.80, "Hashing concluido.")
        self.floresta_cache.append(nova_estrutura)
        self._mostrar_progresso(0.90, "Salvando cache...")
        self.salvar_cache()
        print("Estrutura de arquivos carregada e cache atualizado.")
        self._mostrar_progresso(1.0, "")

    def calcular_tamanho_total_cache(self):
        """Calcula o tamanho total de todos os arquivos em todas as estruturas."""
        total_tamanho = 0
        for raiz in self.floresta_cache:
            total_tamanho += sum(arquivo.tamanho for _, arquivo in raiz.coletar_arquivos())
        return total_tamanho

    def salvar_cache(self):
        """Salva a floresta de estruturas no cache JSON."""
        pasta_cache = os.path.join(os.getcwd(), "cache")
        cache_file = os.path.join(pasta_cache, "cache.json")
        timestamp = datetime.now(timezone(timedelta(hours=-3))).strftime('%d_%m_%Y,%H:%M')
        
        data = {
            "data": timestamp,
            "estruturas": [p.to_dict() for p in self.floresta_cache]
        }
        
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Cache salvo em {cache_file}")

    def mostrar(self):
        """Mostra as árvores de arquivos e pastas de todas as estruturas."""
        if not self.floresta_cache:
            print("Nenhuma estrutura de pasta para exibir.")
            return

        print("\n--- Estruturas de Pasta ---")
        for i, raiz in enumerate(self.floresta_cache):
            print(f"\nEstrutura {i+1}: {raiz.caminho_completo}")
            mostrar_pasta(NoPasta(raiz)) # mostrar_pasta espera um NoPasta
        print("------------------------------------")

    def detectar_duplicatas(self):
        """Detecta arquivos duplicados e imprime os resultados."""
        from Classe.Arquivo import Arquivo

        tamanho_dict = defaultdict(list)
        if not self.floresta_cache:
            print("\nNenhuma estrutura de pasta para verificar.")
            return

        print("Coletando arquivos de todas as estruturas:")
        for raiz in self.floresta_cache:
            for caminho_pasta, arquivo in raiz.coletar_arquivos():
                if arquivo.caminho_completo and os.path.exists(arquivo.caminho_completo):
                    tamanho_dict[arquivo.tamanho].append((caminho_pasta, arquivo))

        duplicatas = []
        total_duplicados = 0
        espaco_duplicado = 0

        # Filtrar por tamanho
        arquivos_a_hashear = [item for sublist in tamanho_dict.values() if len(sublist) > 1 for item in sublist]
        
        if not arquivos_a_hashear:
            print("\nNenhum arquivo com tamanho duplicado encontrado.")
            return
            
        print(f"Encontrados {len(arquivos_a_hashear)} arquivos com tamanhos duplicados. Calculando hashes para verificação...")

        hash_dict = defaultdict(list)
        total_arquivos = len(arquivos_a_hashear)
        for i, (caminho, arquivo) in enumerate(arquivos_a_hashear):
            if not arquivo.hash_md5:
                arquivo._calcular_hash()
            if arquivo.hash_md5:
                hash_dict[arquivo.hash_md5].append((caminho, arquivo))
            
            percentual = (i + 1) / total_arquivos
            self._mostrar_progresso(percentual, f"Verificando: {arquivo.nome}.{arquivo.extensao}")
        print()

        for hash_value, grupo in hash_dict.items():
            if len(grupo) > 1:
                tamanho = grupo[0][1].tamanho
                duplicatas.append((tamanho, hash_value, grupo))
                total_duplicados += len(grupo) - 1
                espaco_duplicado += (len(grupo) - 1) * tamanho
        
        if not duplicatas:
            print("\nNenhum arquivo duplicado encontrado após verificação de hash.")
            return

        print("\nArquivos duplicados encontrados (usando MD5):")
        for tamanho, hash_value, grupo in duplicatas:
            print(f"\nTamanho: {tamanho / (1024*1024):.2f} MB  - Hash: {hash_value}")
            for i, (caminho, arquivo) in enumerate(grupo, 1):
                print(f" {i}. {arquivo.caminho_completo}")

        print(f"\nEstatisticas:")
        print(f" Arquivos duplicados: {total_duplicados}")
        print(f" Espaco desperdicado: {espaco_duplicado / (1024 * 1024):.2f} MB")

    def _mostrar_progresso(self, percentual, info_extra="", largura=40):
        """Exibe uma barra de progresso no console."""
        blocos = int(round(largura * percentual))
        texto_barra = "█" * blocos + " " * (largura - blocos)
        # Garante que a info extra não ultrapasse o limite do console
        info_extra = info_extra[:50].ljust(50)
        sys.stdout.write(f'\rProgresso: [{texto_barra}] {int(percentual * 100)}% - {info_extra}')
        sys.stdout.flush()
        if percentual == 1.0:
            sys.stdout.write('\n')

    def _mapear_arquivos_floresta(self, floresta):
        """Cria um mapa de todos os arquivos na floresta para reuso de hash."""
        mapa = {}
        for raiz in floresta:
            for _, arquivo in raiz.coletar_arquivos():
                if arquivo.caminho_completo:
                    mapa[arquivo.caminho_completo] = arquivo
        return mapa
