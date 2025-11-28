# Script para reproduzir localmente o fluxo: Nova varredura -> apagar arquivo -> Atualizar (mesclagem)
# Execute: python reproduce_cache_flow.py

import os
import sys
import shutil
import json
import time

ROOT = os.path.dirname(__file__)
sys.path.insert(0, ROOT)

from leitor.ManipuladorPasta import ManipuladorPasta
# Configura a variável de ambiente do Django para que views.py consiga acessar settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'leitor.settings')
from django.conf import settings
from leitor import views

TMP = os.path.join(ROOT, "tmp_scan")
CACHE_DIR = os.path.join(ROOT, "Cache")
CACHE_PATH = os.path.join(CACHE_DIR, "cache.json")

# Garante que settings.CACHE_PATH aponte para o cache usado aqui
settings.CACHE_PATH = CACHE_PATH


def ler_cache(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    # limpa estado antigo
    if os.path.exists(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)

    f1 = os.path.join(TMP, 'file_a.txt')
    f2 = os.path.join(TMP, 'file_b.txt')
    with open(f1, 'w', encoding='utf-8') as fh:
        fh.write('conteudo A')
    with open(f2, 'w', encoding='utf-8') as fh:
        fh.write('conteudo B')

    print('Criados:', f1, f2)

    # Faz a primeira varredura (forca recriacao)
    m1 = ManipuladorPasta(TMP, interativo=False)
    m1.carregar_estrutura(forcar_recriacao=True, interativo=False)
    print('\nCache apos primeira varredura:')
    data = ler_cache(CACHE_PATH)
    print(json.dumps(data, ensure_ascii=False, indent=2) if data else 'nenhum cache')

    # Remove um arquivo fisicamente
    os.remove(f2)
    print('\nRemovido fisicamente:', f2)

    # Faz a varredura nova (gerando nova arvore) e aplica a rotina de mesclagem (como atualizar_cache faria)
    from leitor.Pasta import Pasta
    raiz_antiga, meta_antigo = views.carregar_raiz_do_cache()
    raiz_nova = Pasta(TMP, ler_conteudo=True)

    if raiz_antiga is None:
        print('Nao havia cache antigo. Abortando teste.')
        return

    # Mesclagem similar ao que atualizar_cache faz
    old_roots = []
    if raiz_antiga.caminho_completo != "":
        old_roots.append(raiz_antiga)
    else:
        atual = raiz_antiga.subpastas
        while atual:
            old_roots.append(atual.pasta)
            atual = atual.proximo

    final_roots = []
    raiz_nova_mesclada = False
    norm_nova_path = os.path.normpath(raiz_nova.caminho_completo).lower()

    for old_root in old_roots:
        norm_old_path = os.path.normpath(old_root.caminho_completo).lower()
        if not norm_old_path.startswith(norm_nova_path + os.sep) and norm_old_path != norm_nova_path:
            final_roots.append(old_root)

    for root in final_roots:
        norm_root_path = os.path.normpath(root.caminho_completo).lower()
        if norm_nova_path.startswith(norm_root_path + os.sep):
            views._replace_subtree(root, raiz_nova)
            raiz_nova_mesclada = True
            break

    if not raiz_nova_mesclada:
        final_roots.append(raiz_nova)

    from leitor.Pasta import Pasta
    from leitor.NoPasta import NoPasta
    raiz_final = Pasta(caminho="", ler_conteudo=False)
    if final_roots:
        head = NoPasta(final_roots[0])
        atual = head
        for i in range(1, len(final_roots)):
            novo_no = NoPasta(final_roots[i])
            atual.proximo = novo_no
            atual = novo_no
        raiz_final.subpastas = head

    # Marca arquivos removidos e salva
    views._marcar_arquivos_removidos(raiz_antiga, raiz_final)
    meta_antigo["data"] = time.strftime('%d_%m_%Y,%H:%M')
    meta_antigo["paths_varridos"] = [p.caminho_completo for p in final_roots]
    data_to_save = meta_antigo.copy()
    data_to_save["estrutura"] = raiz_final.to_dict()
    views.salvar_cache_atualizado(data_to_save)

    print('\nCache apos atualizacao/mesclagem:')
    data = ler_cache(CACHE_PATH)
    print(json.dumps(data, ensure_ascii=False, indent=2) if data else 'nenhum cache')

    # Procura por marcacao removido
    def buscar_removidos(d):
        found = []
        if isinstance(d, dict):
            if d.get('removido'):
                found.append(d)
            for v in d.values():
                if isinstance(v, (dict, list)):
                    found.extend(buscar_removidos(v))
        elif isinstance(d, list):
            for el in d:
                found.extend(buscar_removidos(el))
        return found

    removed = buscar_removidos(data)
    print('\nArquivos marcados como removidos no cache:', len(removed))
    for r in removed[:20]:
        print('-', r.get('nome'), r.get('caminho_completo'))

    # cleanup temporario (tenta com cuidado para evitar PermissionError no Windows/OneDrive)
    try:
        shutil.rmtree(TMP)
    except PermissionError:
        try:
            # tenta rmdir recursivo do Windows via cmd (menos propenso a travar com arquivos abertos)
            import subprocess
            subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", TMP], check=False)
        except Exception:
            print('Aviso: nao foi possivel remover a pasta temporaria, remova manualmente:', TMP)

if __name__ == '__main__':
    main()
