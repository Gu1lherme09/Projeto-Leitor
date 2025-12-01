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
        Detecta arquivos duplicados usando MD5. Garante que todos os arquivos
        tenham seu hash calculado se a função for chamada.
        """
        from .Arquivo import Arquivo

        todos_arquivos = self.raiz.coletar_arquivos()

        # 1. Garante que todos os arquivos tenham hash calculado
        for _, arquivo in todos_arquivos:
            if not arquivo.hash_md5:
                if arquivo.caminho_completo and os.path.exists(arquivo.caminho_completo):
                    arquivo._calcular_hash()

        # 2. Agrupa arquivos por hash (ignorando arquivos sem hash)
        hash_dict = defaultdict(list)
        for caminho_pasta, arquivo in todos_arquivos:
            if arquivo.hash_md5:
                hash_dict[arquivo.hash_md5].append((caminho_pasta, arquivo))

        # 3. Filtra os grupos que de fato são duplicados
        duplicatas = []
        total_duplicados = 0
        espaco_duplicado = 0
        for hash_value, grupo in hash_dict.items():
            if len(grupo) > 1:
                tamanho = grupo[0][1].tamanho  # Tamanho é o mesmo para todos no grupo
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
                        tamanho_total = self.calcular_tamanho_pasta(pasta)
                        resultados.append({
                            "nome": pasta.nome,
                            "caminho": caminho_atual,
                            "tamanho_total": tamanho_total
                        })

                    if pasta.subpastas:
                        rec(pasta.subpastas, caminho_atual)

                    no = no.proximo

            rec(self.no_raiz, "")

            return {
                "status": "ok" if resultados else "vazio",
                "termo": termo,
                "quantidade": len(resultados),
                "resultados": resultados
            }


    def buscar_extensao(self, termo):
        termo = termo.lower().strip()

        if not termo.startswith("."):
            termo = "." + termo

        resultados = []

        for caminho_pasta, arquivo in self.raiz.coletar_arquivos():
            nome_ext = f"{arquivo.nome}.{arquivo.extensao}".lower()
            if nome_ext.endswith(termo):
                resultados.append({
                    "nome": f"{arquivo.nome}.{arquivo.extensao}",
                    "caminho": caminho_pasta,
                    "tamanho": arquivo.tamanho
                })

        return {
            "status": "ok" if resultados else "vazio",
            "termo": termo,
            "quantidade": len(resultados),
            "resultados": resultados
        }


    def buscar_arquivo(self, termo):
        termo = termo.lower()
        resultados = []

        for caminho_pasta, arquivo in self.raiz.coletar_arquivos():
            nome = arquivo.nome.lower()

            if termo in nome:
                nome_ext = f"{arquivo.nome}.{arquivo.extensao}"
                resultados.append({
                    "nome": nome_ext,
                    "caminho": caminho_pasta,
                    "tamanho": arquivo.tamanho
                })

        return {
            "status": "ok" if resultados else "vazio",
            "termo": termo,
            "quantidade": len(resultados),
            "resultados": resultados
        }


    def mostrar_conteudo_pasta(self, pasta):
        """Agora retorna JSON também."""
        return self._montar_json_pasta(pasta)


    def _montar_json_pasta(self, pasta):
        subpastas_json = []

        sub = pasta.subpastas
        while sub is not None:
            subpastas_json.append(self._montar_json_pasta(sub.pasta))
            sub = sub.proximo

        return {
            "nome": pasta.nome,
            "arquivos": [
                {
                    "nome": arq.nome,
                    "extensao": arq.extensao,
                    "tamanho": arq.tamanho
                }
                for arq in pasta.arquivos
            ],
            "subpastas": subpastas_json
        }


    def calcular_tamanho_pasta(self, pasta):
        total = 0

        for arq in pasta.arquivos:
            total += arq.tamanho

        sub = pasta.subpastas
        while sub is not None:
            total += self.calcular_tamanho_pasta(sub.pasta)
            sub = sub.proximo

        return total

    def buscar_avancado(self, nome="", extensao="", tamanho_min="", tamanho_max="", hash_md5="", somente_cache=False):
        nome = nome.lower().strip()
        extensao = extensao.lower().strip().replace(" ", "")
        hash_md5 = hash_md5.lower().strip()

        # NOVA FUNÇÃO: aceita tanto número (int) quanto string antiga ("30mb")
        def parse_tamanho(valor):
            if not valor:  # None, "", 0
                return None
            try:
                # Caso 1: já vem como número (int/float) → nosso novo padrão do JS
                if isinstance(valor, (int, float)):
                    return int(valor)
                # Caso 2: ainda vem como string (ex: "30mb", "5 gb", "1000") → compatibilidade
                if isinstance(valor, str):
                    valor = valor.strip().lower().replace(" ", "").replace(",", ".")
                    mult = 1
                    original = valor

                    if valor.endswith("kb"):
                        mult = 1024
                        valor = valor[:-2]
                    elif valor.endswith("mb"):
                        mult = 1024**2
                        valor = valor[:-2]
                    elif valor.endswith("gb"):
                        mult = 1024**3
                        valor = valor[:-2]
                    elif valor.endswith("b"):
                        valor = valor[:-1]

                    # Remove tudo que não for número ou ponto
                    num_str = ''.join(c for c in valor if c.isdigit() or c == '.')
                    if not num_str:
                        return None
                    return int(float(num_str) * mult)
            except:
                pass
            return None  # Qualquer erro → ignora o filtro

        # Converte os filtros de tamanho
        t_min = parse_tamanho(tamanho_min)
        t_max = parse_tamanho(tamanho_max)

        resultados = []

        for caminho_pasta, arquivo in self.raiz.coletar_arquivos():
            nome_ext = f"{arquivo.nome}.{arquivo.extensao}".lower()

            # Filtro por nome
            if nome and nome not in arquivo.nome.lower():
                continue

            # Filtro por extensão
            if extensao:
                ext_user = extensao.lstrip(".").lower()
                ext_real = arquivo.extensao.lstrip(".").lower()
                if ext_user != ext_real:
                    continue

            # Filtro por tamanho
            if t_min is not None and arquivo.tamanho < t_min:
                continue
            if t_max is not None and arquivo.tamanho > t_max:
                continue

            # Filtro por hash MD5
            if hash_md5:
                if not arquivo.hash_md5:
                    try:
                        arquivo._calcular_hash()
                    except:
                        continue  # Se não conseguir calcular, pula
                if hash_md5 not in (arquivo.hash_md5 or "").lower():
                    continue

            # Adiciona resultado
            resultados.append({
                "nome": f"{arquivo.nome}.{arquivo.extensao}",
                "caminho": caminho_pasta,
                "extensao": arquivo.extensao,
                "tamanho": arquivo.tamanho,           # em bytes
                "hash_md5": arquivo.hash_md5 or "",
                "modificacao": None,
                "origem": "cache" 
            })

        return {
            "status": "ok" if resultados else "vazio",
            "quantidade": len(resultados),
            "resultados": resultados
        }
