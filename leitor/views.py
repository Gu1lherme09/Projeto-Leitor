# leitor/leitor/views.py
from datetime import datetime
import os
import json
from collections import defaultdict
import shutil

from django.conf import settings
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages

from .Pasta import Pasta  # ajusta se o nome/pacote for outro
from .ManipuladorPasta import ManipuladorPasta


CACHE_PATH = os.path.join(settings.BASE_DIR, "Cache", "cache.json")

def carregar_raiz_do_cache():
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    estrutura = data.get("estrutura")
    raiz = Pasta.from_dict(estrutura)  # recria árvore sem reler disco :contentReference[oaicite:1]{index=1}
    return raiz, data


def salvar_cache_atualizado(raiz, meta, extra_meta=None):
    """
    Atualiza o cache.json mantendo os metadados antigos
    e escrevendo a estrutura atual (com hashes novos).
    """
    # copia tudo, menos a estrutura antiga
    data = {k: v for k, v in meta.items() if k != "estrutura"}
    data["estrutura"] = raiz.to_dict()
    if extra_meta:
        data.update(extra_meta)

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def carregar_raiz_do_cache():
    """
    Tenta carregar a raiz a partir do cache.json.
    Se o arquivo não existir ou estiver inválido, retorna (None, None).
    """
    if not os.path.exists(CACHE_PATH):
        # ainda não foi gerado cache
        return None, None

    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        estrutura = data.get("estrutura")
        if not estrutura:
            # arquivo existe, mas não tem estrutura válida
            return None, data

        raiz = Pasta.from_dict(estrutura)
        return raiz, data

    except (json.JSONDecodeError, OSError, KeyError, TypeError):
        # cache corrompido ou ilegível
        return None, None


def home(request):
    raiz, meta = carregar_raiz_do_cache()
     # 👉 Se ainda não existe cache.json ou está inválido
    if raiz is None:
        contexto = {
            "total_arquivos": 0,
            "total_tamanho_gb": 0,
            "extensoes_unicas": 0,
            "top_extensoes": [],
            "outros_gb": 0,
            "hash_disponivel": False,
            "total_duplicados": None,
            "espaco_duplicado_gb": None,
            "espaco_ocupado_gb": 0,
            "espaco_livre_gb": 0,
            "sem_cache": True,  # flag pra mostrar aviso no template se quiser
        }
        return render(request, "home/home.html", contexto)

    arquivos = raiz.coletar_arquivos()

    total_arquivos = len(arquivos)
    total_tamanho_bytes = sum(arq.tamanho for _, arq in arquivos)
    total_tamanho_gb = total_tamanho_bytes / (1024 ** 3) if total_tamanho_bytes else 0

    # Buckets de tamanho para o gráfico de pizza por tamanho
    bucket_maior_1gb_bytes = 0
    bucket_100mb_1gb_bytes = 0
    bucket_menor_100mb_bytes = 0

    UM_GB = 1024 ** 3
    CEM_MB = 100 * 1024 ** 2

    for _, arq in arquivos:
        if arq.tamanho > UM_GB:
            bucket_maior_1gb_bytes += arq.tamanho
        elif arq.tamanho >= CEM_MB:
            bucket_100mb_1gb_bytes += arq.tamanho
        else:
            bucket_menor_100mb_bytes += arq.tamanho

    bucket_maior_1gb_gb   = bucket_maior_1gb_bytes   / (1024 ** 3) if bucket_maior_1gb_bytes else 0
    bucket_100mb_1gb_gb   = bucket_100mb_1gb_bytes   / (1024 ** 3) if bucket_100mb_1gb_bytes else 0
    bucket_menor_100mb_gb = bucket_menor_100mb_bytes / (1024 ** 3) if bucket_menor_100mb_bytes else 0

    extensoes_set = {arq.extensao.lower() for _, arq in arquivos}
    extensoes_unicas = len(extensoes_set)

    ext_tamanhos = defaultdict(int)
    for _, arq in arquivos:
        ext_tamanhos[arq.extensao.lower()] += arq.tamanho

    ordenadas = sorted(ext_tamanhos.items(), key=lambda x: x[1], reverse=True)
    top5 = ordenadas[:5]
    outros_total = sum(t for _, t in ordenadas[5:])

    top_extensoes = [
        {"ext": ext, "gb": tamanho / (1024 ** 3)}
        for ext, tamanho in top5
    ]
    outros_gb = outros_total / (1024 ** 3) if outros_total else 0

    root_path = raiz.caminho_completo or ""
    drive, _ = os.path.splitdrive(root_path)
    if drive:
        base_disk_path = drive + os.sep 
    else:
        base_disk_path = os.path.abspath(root_path) if root_path else settings.BASE_DIR

    try:
        total_disk, used_disk, free_disk = shutil.disk_usage(base_disk_path)
        total_disk_gb = total_disk / (1024 ** 3)
        free_disk_gb = free_disk / (1024 ** 3)
    except Exception:
        total_disk_gb = total_tamanho_gb
        free_disk_gb = 0

    espaco_ocupado_gb = total_tamanho_gb
    espaco_livre_gb = max(total_disk_gb - espaco_ocupado_gb, 0)


    contexto = {
        "total_arquivos": total_arquivos,
        "total_tamanho_gb": total_tamanho_gb,
        "extensoes_unicas": extensoes_unicas,
        "top_extensoes": top_extensoes,
        "outros_gb": outros_gb,
        # duplicados desativado aqui
        "hash_disponivel": False,
        "total_duplicados": None,
        "espaco_duplicado_gb": None,
        # dados do gráfico
        "espaco_ocupado_gb": espaco_ocupado_gb,
        "espaco_livre_gb": espaco_livre_gb,
        "bucket_maior_1gb_gb": bucket_maior_1gb_gb,
        "bucket_100mb_1gb_gb": bucket_100mb_1gb_gb,
        "bucket_menor_100mb_gb": bucket_menor_100mb_gb,
    }
    return render(request, "home/home.html", contexto)

def pesquisar(request):
    return render(request,"abas/buscar_arquivos.html")


def duplicados(request):
    raiz, meta = carregar_raiz_do_cache()
    if raiz is None:
        contexto = {
            "total_duplicados": 0,
            "total_grupos": 0,
            "espaco_duplicado_gb": 0,
            "grupos": [],
            "hash_disponivel": False,
            "sem_cache": True,
        }
        return render(request, "abas/duplicados.html", contexto)
    arquivos = raiz.coletar_arquivos()  # [(caminho_pasta, Arquivo), ...]

    # Descobrir se o cache já tem hash:
    # 1) se existir flag "hash_calculado" no cache.json (quando você salvar com ela)
    # 2) se não tiver flag, checa se há pelo menos 1 arquivo com hash_md5 preenchido
    flag_cache = meta.get("hash_calculado")
    any_hash = any(a.hash_md5 for _, a in arquivos)
    hash_disponivel = bool(flag_cache) or any_hash

    # Se clicou em "Recalcular duplicados" (POST)
    if request.method == "POST":
        # Recalcula MD5 de TODOS os arquivos que têm caminho válido
        for _, arq in arquivos:
            if arq.caminho_completo and os.path.exists(arq.caminho_completo):
                arq._calcular_hash()  # Atualiza arq.hash_md5 :contentReference[oaicite:2]{index=2}

        hash_disponivel = True
        # Salva de volta no cache, marcando que o hash foi calculado
        salvar_cache_atualizado(raiz, meta, extra_meta={"hash_calculado": True})

    # Se depois disso ainda não tiver hash, NÃO faz busca por duplicados
    if not hash_disponivel:
        contexto = {
            "total_duplicados": 0,
            "total_grupos": 0,
            "espaco_duplicado_gb": 0,
            "grupos": [],
            "hash_disponivel": False,
        }
        return render(request, "abas/duplicados.html", contexto)

    # A partir daqui: já TEM hash no cache → agora sim monta os grupos
    tamanho_dict = defaultdict(list)

    # Agrupa por tamanho, mas só arquivos com hash_md5 preenchido
    for caminho_pasta, arquivo in arquivos:
        if (
            arquivo.caminho_completo
            and os.path.exists(arquivo.caminho_completo)
            and arquivo.hash_md5
        ):
            tamanho_dict[arquivo.tamanho].append((caminho_pasta, arquivo))

    grupos = []
    total_duplicados = 0
    espaco_duplicado_bytes = 0
    id_grupo = 1

    for tamanho, lista in tamanho_dict.items():
        if len(lista) < 2:
            continue

        hash_dict = defaultdict(list)

        # AGORA não recalcula hash aqui – usa só o que veio do cache
        for caminho, arquivo in lista:
            if not arquivo.hash_md5:
                continue  # por segurança, ignora quem não tiver hash
            hash_dict[arquivo.hash_md5].append((caminho, arquivo))

        for hash_value, grupo in hash_dict.items():
            if len(grupo) < 2:
                continue

            num_arquivos = len(grupo)
            total_duplicados += (num_arquivos - 1)
            espaco_duplicado_bytes += (num_arquivos - 1) * tamanho

            primeira_ext = (grupo[0][1].extensao or "").lower()

            arquivos_grupo = []
            for caminho, arquivo in grupo:
                full_path = arquivo.caminho_completo or os.path.join(
                    caminho, f"{arquivo.nome}.{arquivo.extensao}"
                )

                try:
                    mtime = os.path.getmtime(full_path)
                    data_mod = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
                except OSError:
                    data_mod = "-"

                arquivos_grupo.append({
                    "nome": f"{arquivo.nome}.{arquivo.extensao}",
                    "caminho": full_path,
                    "data_mod": data_mod,
                    "origem": "Cache",  # agora tudo veio do cache
                })

            grupos.append({
                "id": id_grupo,
                "ext": primeira_ext,
                "hash": hash_value,
                "tamanho_gb": tamanho / (1024 ** 3),
                "qtd_arquivos": num_arquivos,
                "arquivos": arquivos_grupo,
            })
            id_grupo += 1

    total_grupos = len(grupos)
    espaco_duplicado_gb = espaco_duplicado_bytes / (1024 ** 3) if espaco_duplicado_bytes else 0


    contexto = {
        "total_duplicados": total_duplicados,
        "total_grupos": total_grupos,
        "espaco_duplicado_gb": espaco_duplicado_gb,
        "grupos": grupos,
        "hash_disponivel": True,
    }
    return render(request, "abas/duplicados.html", contexto)

def nova_varredura(request):
    if request.method != "POST":
        return redirect("home")

    scan_path = request.POST.get("scan_path")
    calcular_hash = bool(request.POST.get("calcular_hash"))  # checkbox

    # inicia o manipulador em modo "web" (sem input())
    m = ManipuladorPasta(scan_path, interativo=False)

    # força recriar estrutura
    m.carregar_estrutura(forcar_recriacao=True, interativo=False)

    # só calcula hash / duplicados se o usuário marcou a opção
    if calcular_hash:
        m.detectar_duplicatas()     # usa sua função atual
        # importante: salvar o cache depois que os hashes estiverem preenchidos
        m.salvar_cache(extra_meta={"hash_calculado": True})
    else:
        m.salvar_cache(extra_meta={"hash_calculado": False})

    messages.success(
        request,
        "Varredura concluída. Hash calculado." if calcular_hash
        else "Varredura concluída sem cálculo de hash."
    )
    return redirect("home")