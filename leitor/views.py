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

from .Pasta import Pasta
from .NoPasta import NoPasta
from .ManipuladorPasta import ManipuladorPasta


def carregar_raiz_do_cache():
    if not os.path.exists(settings.CACHE_PATH):
        return None, None
    
    try:
        with open(settings.CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        estrutura = data.get("estrutura")
        if not estrutura:
            return None, data

        raiz = Pasta.from_dict(estrutura)
        return raiz, data
    except (json.JSONDecodeError, OSError, KeyError, TypeError):
        return None, None


def salvar_cache_atualizado(data_to_save):
    """
    Salva o dicionário de dados completo no arquivo de cache.
    """
    # Garante que a pasta Cache exista
    cache_dir = os.path.dirname(settings.CACHE_PATH)
    os.makedirs(cache_dir, exist_ok=True)
    
    with open(settings.CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)


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
                arq._calcular_hash()  # Atualiza arq.hash_md5

        hash_disponivel = True
        # Atualiza o meta_antigo para ter o hash_calculado como True
        meta["hash_calculado"] = True
        # Salva de volta no cache, usando a função atualizada
        data_to_save = meta.copy()
        data_to_save["estrutura"] = raiz.to_dict()
        salvar_cache_atualizado(data_to_save)


    # Se depois disso ainda não tiver hash, NÃO faz busca por duplicados
    if not hash_disponivel:
        contexto = {
            "total_duplicados": 0,
            "total_grupos": 0,
            "espaco_duplicado_gb": 0,
            "grupos": [],
            "hash_disponivel": False,
            "sem_cache": True,
        }
        return render(request, "abas/duplicados.html", contexto)

    # A partir daqui: já TEM hash no cache → agora sim monta os grupos
    tamanho_dict = defaultdict(list)
    
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
    calcular_hash = bool(request.POST.get("calcular_hash"))

    if not os.path.isdir(scan_path):
        messages.error(request, f"O caminho '{scan_path}' não existe ou não é uma pasta.")
        return redirect("home")

    m = ManipuladorPasta(scan_path, interativo=False)
    m.carregar_estrutura(forcar_recriacao=True, interativo=False)

    data_to_save = {
        "estrutura": m.raiz.to_dict(),
        "data": datetime.now().strftime('%d_%m_%Y,%H:%M'),
        "paths_varridos": [scan_path],
    }

    if calcular_hash:
        m.detectar_duplicatas()
        data_to_save["hash_calculado"] = True
    else:
        data_to_save["hash_calculado"] = False
    
    salvar_cache_atualizado(data_to_save)

    messages.success(
        request,
        "Varredura concluída. Hash calculado." if calcular_hash
        else "Varredura concluída sem cálculo de hash."
    )
    return redirect("home")


def _replace_subtree(raiz, sub_arvore_nova):
    """
    Função auxiliar recursiva para encontrar e substituir uma sub-árvore de pastas 
    dentro da estrutura de cache principal, usado na lógica de mesclagem.
    """
    if not raiz.caminho_completo or not sub_arvore_nova.caminho_completo.startswith(raiz.caminho_completo + os.sep):
        return False

    # Navega na lista encadeada de subpastas
    atual = raiz.subpastas
    while atual:
        pasta_atual = atual.pasta
        
        # Se encontramos a subpasta exata para substituir
        if pasta_atual.caminho_completo == sub_arvore_nova.caminho_completo:
            atual.pasta = sub_arvore_nova
            return True

        # Se a subpasta que procuramos está DENTRO da pasta_atual, faz a recursão
        if sub_arvore_nova.caminho_completo.startswith(pasta_atual.caminho_completo + os.sep):
            if _replace_subtree(pasta_atual, sub_arvore_nova):
                return True
        
        atual = atual.proximo
        
    return False


def atualizar_cache(request):
    if request.method != "POST":
        return redirect("home")

    scan_path = request.POST.get("scan_path")
    calcular_hash = bool(request.POST.get("calcular_hash"))

    if not os.path.isdir(scan_path):
        messages.error(request, f"O caminho '{scan_path}' não existe ou não é uma pasta.")
        return redirect("home")

    # Carrega o cache antigo e faz a varredura do novo caminho solicitado.
    raiz_antiga, meta_antigo = carregar_raiz_do_cache()
    if raiz_antiga is None:
        messages.error(request, "Nenhum cache encontrado para atualizar. Execute uma 'Nova varredura' primeiro.")
        return redirect("home")

    m_novo = ManipuladorPasta(scan_path, interativo=False)
    m_novo.carregar_estrutura(forcar_recriacao=True, interativo=False)
    raiz_nova = m_novo.raiz

    if not raiz_nova or (not raiz_nova.arquivos and not raiz_nova.subpastas):
        messages.info(request, f"Nenhum arquivo ou pasta encontrado em '{scan_path}'. O cache não foi alterado.")
        return redirect("home")

    # Coleta as raízes de varredura existentes a partir da raiz virtual do cache.
    old_roots = []
    if raiz_antiga.caminho_completo != "": # Não é virtual
        old_roots.append(raiz_antiga)
    else: # É virtual, coleta filhos
        atual = raiz_antiga.subpastas
        while atual:
            old_roots.append(atual.pasta)
            atual = atual.proximo

    final_roots = []
    raiz_nova_mesclada = False
    norm_nova_path = os.path.normpath(raiz_nova.caminho_completo).lower()

    # Lógica de mesclagem: remove raízes antigas que são filhas da nova varredura.
    for old_root in old_roots:
        norm_old_path = os.path.normpath(old_root.caminho_completo).lower()
        if not norm_old_path.startswith(norm_nova_path + os.sep) and norm_old_path != norm_nova_path:
            final_roots.append(old_root)

    # Lógica de mesclagem: tenta encaixar a nova varredura como subpasta de uma raiz existente.
    for root in final_roots:
        norm_root_path = os.path.normpath(root.caminho_completo).lower()
        if norm_nova_path.startswith(norm_root_path + os.sep):
            _replace_subtree(root, raiz_nova)
            raiz_nova_mesclada = True
            break
    
    # Se a nova varredura não foi mesclada, ela se torna uma nova raiz.
    if not raiz_nova_mesclada:
        final_roots.append(raiz_nova)

    # Reconstrói a raiz virtual do cache com a lista final de diretórios.
    raiz_final = Pasta(caminho="", ler_conteudo=False)
    if final_roots:
        # Cria a lista encadeada a partir da `final_roots`
        head = NoPasta(final_roots[0])
        atual = head
        for i in range(1, len(final_roots)):
            novo_no = NoPasta(final_roots[i])
            atual.proximo = novo_no
            atual = novo_no
        raiz_final.subpastas = head

    # Se solicitado, calcula o hash dos arquivos que ainda não o possuem no cache final.
    if calcular_hash:
        todos_arquivos = raiz_final.coletar_arquivos()
        for _, arq in todos_arquivos:
            if arq.hash_md5 is None and arq.caminho_completo and os.path.exists(arq.caminho_completo):
                arq._calcular_hash()
        meta_antigo["hash_calculado"] = True

    # Atualiza os metadados e salva a nova estrutura completa no arquivo cache.json.
    meta_antigo["data"] = datetime.now().strftime('%d_%m_%Y,%H:%M')
    meta_antigo["paths_varridos"] = [p.caminho_completo for p in final_roots]
    data_to_save = meta_antigo.copy()
    data_to_save["estrutura"] = raiz_final.to_dict()
    salvar_cache_atualizado(data_to_save)

    messages.success(request, f"Cache hierarquicamente atualizado com os dados de '{scan_path}'.")
    return redirect("home")