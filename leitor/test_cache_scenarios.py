# leitor/leitor/test_cache_scenarios.py
import os
import json
import shutil
import tempfile
from django.test import TestCase, Client
from django.conf import settings
from django.urls import reverse

class CacheScenariosTestCase(TestCase):
    def setUp(self):
        """
        Configura um ambiente de teste limpo antes de cada teste.
        - Cria um diretório de teste temporário.
        - Cria um arquivo de cache temporário e sobrescreve a configuração.
        - Inicializa um cliente de teste do Django.
        """
        # Cria um diretório temporário para os arquivos de teste
        self.test_dir = tempfile.mkdtemp()
        
        # Cria um arquivo de cache temporário
        self.temp_cache_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_cache_dir, 'cache.json')

        # Sobrescreve a configuração CACHE_PATH para usar o arquivo temporário
        settings.CACHE_PATH = self.cache_file

        # Cliente de teste do Django
        self.client = Client()

    def tearDown(self):
        """
        Limpa o ambiente de teste depois de cada teste.
        - Remove o diretório de teste temporário e seu conteúdo.
        - Remove o diretório de cache temporário.
        """
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.temp_cache_dir)

    def _create_file(self, path, content=""):
        """Cria um arquivo com conteúdo no caminho especificado."""
        with open(path, "w") as f:
            f.write(content)

    def _get_cache_content(self):
        """Lê e retorna o conteúdo do arquivo de cache JSON."""
        if not os.path.exists(self.cache_file):
            return None
        with open(self.cache_file, "r") as f:
            return json.load(f)
            
    def _get_all_files_from_cache(self, cache_data):
        """Extrai todos os arquivos da estrutura de cache, retornando um dicionário."""
        files = {}
        if not cache_data or "estrutura" not in cache_data:
            return files

        def recurse(pasta_dict):
            """Função recursiva que navega na estrutura de dicionários do cache."""
            # Adiciona arquivos da pasta atual
            for arquivo in pasta_dict.get('arquivos', []):
                # O caminho completo do arquivo é relativo ao caminho da pasta que o contém
                nome_arquivo_completo = f"{arquivo['nome']}.{arquivo['extensao']}" if arquivo.get('extensao') else arquivo['nome']
                full_path = os.path.join(pasta_dict['caminho_completo'], nome_arquivo_completo)
                files[full_path.lower()] = arquivo
            
            # Recurso para cada subpasta
            for subpasta_dict in pasta_dict.get('subpastas', []):
                recurse(subpasta_dict)

        # Inicia a recursão pela estrutura raiz
        recurse(cache_data["estrutura"])
        return files

    def test_1_add_new_files(self):
        """
        Testa o cenário 1: Adicionar novos arquivos.
        - Cria um cache inicial.
        - Adiciona dois novos arquivos.
        - Roda "Atualizar cache".
        - Verifica se os novos arquivos aparecem no cache.json.
        """
        # 1. Setup inicial e primeira varredura
        initial_file = os.path.join(self.test_dir, "initial.txt")
        self._create_file(initial_file, "initial content")
        
        self.client.post(reverse("nova_varredura"), {"scan_path": self.test_dir})
        
        # 2. Adiciona novos arquivos
        new_file1 = os.path.join(self.test_dir, "new_file1.txt")
        new_file2 = os.path.join(self.test_dir, "new_file2.log")
        self._create_file(new_file1, "content1")
        self._create_file(new_file2, "content2")

        # 3. Roda "Atualizar cache"
        self.client.post(reverse("atualizar_cache"), {"scan_path": self.test_dir})
        
        # 4. Verificação
        cache_content = self._get_cache_content()
        cache_files = self._get_all_files_from_cache(cache_content)
        
        self.assertIn(new_file1.lower(), cache_files)
        self.assertIn(new_file2.lower(), cache_files)
        self.assertFalse(cache_files[new_file1.lower()].get("removido", False))
        self.assertFalse(cache_files[new_file2.lower()].get("removido", False))

    def test_2_remove_multiple_files(self):
        """
        Testa o cenário 2: Remover múltiplos arquivos.
        - Cria um cache com 3 arquivos (um em subpasta).
        - Remove 2 arquivos.
        - Roda "Atualizar cache".
        - Verifica se os arquivos removidos são marcados como "removido: true".
        """
        # 1. Setup inicial
        sub_dir = os.path.join(self.test_dir, "subdir")
        os.makedirs(sub_dir)
        
        file1 = os.path.join(self.test_dir, "file1.txt")
        file2 = os.path.join(self.test_dir, "file2.txt")
        file3 = os.path.join(sub_dir, "file3.txt")
        
        self._create_file(file1, "1")
        self._create_file(file2, "2")
        self._create_file(file3, "3")

        self.client.post(reverse("nova_varredura"), {"scan_path": self.test_dir})
        
        # 2. Remove arquivos
        os.remove(file1)
        os.remove(file3)
        
        # 3. Roda "Atualizar cache"
        self.client.post(reverse("atualizar_cache"), {"scan_path": self.test_dir})

        # 4. Verificação
        cache_content = self._get_cache_content()
        cache_files = self._get_all_files_from_cache(cache_content)
        
        self.assertIn(file1.lower(), cache_files)
        self.assertTrue(cache_files[file1.lower()]["removido"])
        
        self.assertIn(file3.lower(), cache_files)
        self.assertTrue(cache_files[file3.lower()]["removido"])

        self.assertIn(file2.lower(), cache_files)
        self.assertFalse(cache_files[file2.lower()].get("removido", False))

    def test_3_move_rename_file(self):
        """
        Testa o cenário 3: Mover/renomear arquivo.
        - Cria um cache com um arquivo.
        - Renomeia o arquivo.
        - Roda "Atualizar cache".
        - Verifica se o nome antigo é marcado como removido e o novo existe.
        """
        # 1. Setup inicial
        old_path = os.path.join(self.test_dir, "original.txt")
        new_path = os.path.join(self.test_dir, "renamed.txt")
        self._create_file(old_path, "some content")
        
        self.client.post(reverse("nova_varredura"), {"scan_path": self.test_dir})

        # 2. Renomeia
        os.rename(old_path, new_path)
        
        # 3. Roda "Atualizar cache"
        self.client.post(reverse("atualizar_cache"), {"scan_path": self.test_dir})
        
        # 4. Verificação
        cache_content = self._get_cache_content()
        cache_files = self._get_all_files_from_cache(cache_content)
        
        self.assertIn(old_path.lower(), cache_files)
        self.assertTrue(cache_files[old_path.lower()]["removido"])
        
        self.assertIn(new_path.lower(), cache_files)
        self.assertFalse(cache_files[new_path.lower()].get("removido", False))

    def test_4_nested_scan(self):
        """
        Testa o cenário 4: Varredura aninhada.
        - Faz varredura de uma subpasta.
        - Adiciona arquivos na pasta pai.
        - Roda "Atualizar cache" na pasta pai.
        - Verifica se a hierarquia está correta e completa no cache.
        """
        # 1. Setup inicial
        parent_dir = self.test_dir
        child_dir = os.path.join(parent_dir, "child")
        os.makedirs(child_dir)
        
        child_file = os.path.join(child_dir, "child_file.txt")
        self._create_file(child_file, "child")
        
        # 2. Varredura inicial (apenas da subpasta)
        self.client.post(reverse("nova_varredura"), {"scan_path": child_dir})
        
        # 3. Adiciona arquivo na pasta pai e atualiza o cache a partir do pai
        parent_file = os.path.join(parent_dir, "parent_file.txt")
        self._create_file(parent_file, "parent")
        
        self.client.post(reverse("atualizar_cache"), {"scan_path": parent_dir})
        
        # 4. Verificação
        cache_content = self._get_cache_content()
        estrutura = cache_content['estrutura']

        # A estrutura deve ter uma raiz virtual com UMA subpasta (o parent_dir)
        self.assertEqual(estrutura['caminho_completo'], "")
        self.assertEqual(len(estrutura['subpastas']), 1, "A raiz virtual deve conter apenas a pasta pai")
        
        parent_in_cache = estrutura['subpastas'][0]
        self.assertEqual(os.path.normpath(parent_in_cache['caminho_completo']), os.path.normpath(parent_dir))
        
        # O parent deve conter o child
        self.assertEqual(len(parent_in_cache['subpastas']), 1, "A pasta pai deve ter uma subpasta (a filha)")
        child_in_cache = parent_in_cache['subpastas'][0]
        self.assertEqual(os.path.normpath(child_in_cache['caminho_completo']), os.path.normpath(child_dir))

        # Verifica se todos os arquivos estão lá
        cache_files = self._get_all_files_from_cache(cache_content)
        self.assertIn(child_file.lower(), cache_files)
        self.assertIn(parent_file.lower(), cache_files)

    def test_5_hash_duplicates(self):
        """
        Testa o cenário 5: Cálculo de hash e duplicados.
        - Cria 3 arquivos, sendo 2 com conteúdo idêntico.
        - Roda varredura inicial com "calcular_hash".
        - Verifica se os hashes foram calculados e se os arquivos idênticos têm o mesmo hash.
        """
        # 1. Setup
        file1 = os.path.join(self.test_dir, "file1.txt")
        file2_duplicate = os.path.join(self.test_dir, "file2_duplicate.txt")
        file3_unique = os.path.join(self.test_dir, "file3_unique.txt")
        
        self._create_file(file1, "identical content")
        self._create_file(file2_duplicate, "identical content")
        self._create_file(file3_unique, "unique content")

        # 2. Roda nova varredura com cálculo de hash
        self.client.post(reverse("nova_varredura"), {
            "scan_path": self.test_dir,
            "calcular_hash": "True"
        })
        
        # 3. Verificação
        cache_content = self._get_cache_content()
        self.assertTrue(cache_content["hash_calculado"])
        
        cache_files = self._get_all_files_from_cache(cache_content)
        
        hash1 = cache_files[file1.lower()]["hash_md5"]
        hash2 = cache_files[file2_duplicate.lower()]["hash_md5"]
        hash3 = cache_files[file3_unique.lower()]["hash_md5"]
        
        self.assertIsNotNone(hash1)
        self.assertIsNotNone(hash2)
        self.assertIsNotNone(hash3)
        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)
