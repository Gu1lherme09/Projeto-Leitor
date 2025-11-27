import os
import json
import tempfile
import shutil
from django.test import TestCase, override_settings
from django.urls import reverse

# Assume que as classes Pasta, NoPasta estão em leitor/Pasta.py e leitor/NoPasta.py
# e que a view as importa corretamente.
from .Pasta import Pasta
from .NoPasta import NoPasta

class CacheUpdateTests(TestCase):
    """
    Testes para a funcionalidade de Nova Varredura e Atualizar Cache.
    """

    def setUp(self):
        """
        Configura um ambiente de teste limpo antes de cada teste.
        """
        # Cria um diretório temporário para os arquivos de teste (ex: C:/Users/user/AppData/Local/Temp/tmpXXXXX)
        self.test_root_dir = tempfile.mkdtemp()

        # Cria um diretório temporário para o arquivo de cache de teste
        self.cache_dir = tempfile.mkdtemp()
        self.temp_cache_path = os.path.join(self.cache_dir, "test_cache.json")

        # Sobrescreve a configuração CACHE_PATH para usar o nosso arquivo de cache temporário
        # para que os testes não afetem o cache real do projeto.
        self.override = override_settings(
            CACHE_PATH=self.temp_cache_path
        )
        self.override.enable()

    def tearDown(self):
        """
        Limpa o ambiente de teste depois de cada teste.
        """
        # Remove os diretórios temporários e seus conteúdos
        shutil.rmtree(self.test_root_dir)
        shutil.rmtree(self.cache_dir)
        # Desativa a sobrescrita de configuração
        self.override.disable()

    def _create_dummy_file(self, path, content=""):
        """Cria um arquivo de teste com conteúdo."""
        with open(path, "w") as f:
            f.write(content)

    def _get_cache_structure(self):
        """Lê e retorna a estrutura do cache de teste."""
        if not os.path.exists(self.temp_cache_path):
            return None
        with open(self.temp_cache_path, "r") as f:
            return json.load(f).get("estrutura")

    def test_nova_varredura_cria_cache(self):
        """Verifica se a nova varredura cria um cache com uma única raiz."""
        dir_a = os.path.join(self.test_root_dir, "DirA")
        os.makedirs(dir_a)
        self._create_dummy_file(os.path.join(dir_a, "file.txt"))

        # Simula o POST para /nova_varredura
        self.client.post(reverse("nova_varredura"), {"scan_path": dir_a})

        estrutura = self._get_cache_structure()
        self.assertIsNotNone(estrutura)
        self.assertEqual(estrutura["caminho_completo"], dir_a)
        self.assertEqual(len(estrutura["arquivos"]), 1)

    def test_cenario_pastas_independentes(self):
        """
        Testa o Cenário 1: Escaneia C:\\A, depois D:\\B.
        O resultado deve ser uma raiz virtual com duas subpastas.
        """
        # 1. Escaneia a primeira pasta
        dir_a = os.path.join(self.test_root_dir, "DirA")
        os.makedirs(dir_a)
        self._create_dummy_file(os.path.join(dir_a, "file_a.txt"))
        self.client.post(reverse("nova_varredura"), {"scan_path": dir_a})
        
        # 2. Escaneia a segunda pasta (independente)
        dir_b = os.path.join(self.test_root_dir, "DirB")
        os.makedirs(dir_b)
        self._create_dummy_file(os.path.join(dir_b, "file_b.txt"))
        self.client.post(reverse("atualizar_cache"), {"scan_path": dir_b})

        # 3. Verifica a estrutura final
        estrutura = self._get_cache_structure()
        self.assertEqual(estrutura["caminho_completo"], "", "A raiz deveria ser virtual (caminho vazio)")
        self.assertEqual(len(estrutura["subpastas"]), 2, "A raiz virtual deveria ter 2 subpastas")
        
        # Obter os caminhos das pastas dentro da raiz virtual para verificar
        caminhos_encontrados = {p["caminho_completo"] for p in estrutura["subpastas"]}
        self.assertIn(dir_a, caminhos_encontrados)
        self.assertIn(dir_b, caminhos_encontrados)

        # Verificação mais detalhada para dir_a e dir_b
        for p in estrutura["subpastas"]:
            if p["caminho_completo"] == dir_a:
                self.assertEqual(len(p["arquivos"]), 1, f"Pasta {dir_a} deveria ter 1 arquivo")
            elif p["caminho_completo"] == dir_b:
                self.assertEqual(len(p["arquivos"]), 1, f"Pasta {dir_b} deveria ter 1 arquivo")

    def test_cenario_pai_depois_do_filho(self):
        """
        Testa o Cenário 3: Escaneia C:\\Pai\\Filho, depois C:\\Pai.
        O resultado deve ser uma única raiz para C:\\Pai, absorvendo o filho.
        """
        # 1. Cria a estrutura e escaneia o filho
        dir_pai = os.path.join(self.test_root_dir, "Pai")
        dir_filho = os.path.join(dir_pai, "Filho")
        os.makedirs(dir_filho)
        self._create_dummy_file(os.path.join(dir_filho, "file_filho.txt"))
        self.client.post(reverse("nova_varredura"), {"scan_path": dir_filho})

        # 2. Escaneia o pai (que inclui o filho)
        self._create_dummy_file(os.path.join(dir_pai, "file_pai.txt"))
        self.client.post(reverse("atualizar_cache"), {"scan_path": dir_pai})

        # 3. Verifica a estrutura final
        estrutura = self._get_cache_structure()
        self.assertEqual(estrutura["caminho_completo"], "", "A raiz deveria ser virtual")
        self.assertEqual(len(estrutura["subpastas"]), 1, "Deveria haver apenas uma raiz (Pai) na raiz virtual")
        
        raiz_pai_no_cache = estrutura["subpastas"][0]
        self.assertEqual(raiz_pai_no_cache["caminho_completo"], dir_pai)
        self.assertEqual(len(raiz_pai_no_cache["arquivos"]), 1, "A pasta Pai deveria ter 1 arquivo")
        
        # Verifica se o filho está dentro do pai
        self.assertIsNotNone(raiz_pai_no_cache["subpastas"], "A pasta Pai deve ter subpastas")
        self.assertEqual(len(raiz_pai_no_cache["subpastas"]), 1, "A pasta Pai deve ter 1 subpasta (Filho)")
        self.assertEqual(raiz_pai_no_cache["subpastas"][0]["caminho_completo"], dir_filho)
        self.assertEqual(len(raiz_pai_no_cache["subpastas"][0]["arquivos"]), 1, "A subpasta Filho deveria ter 1 arquivo")


    def test_cenario_filho_depois_do_pai(self):
        """
        Testa o Cenário 2: Escaneia C:\\Pai, depois C:\\Pai\\Filho.
        O resultado deve ser uma única raiz C:\\Pai, com o filho atualizado dentro dela.
        """
        # 1. Cria a estrutura e escaneia o pai
        dir_pai = os.path.join(self.test_root_dir, "Pai")
        dir_filho = os.path.join(dir_pai, "Filho")
        os.makedirs(dir_filho)
        self._create_dummy_file(os.path.join(dir_pai, "file_pai.txt"))
        self.client.post(reverse("nova_varredura"), {"scan_path": dir_pai})

        # 2. Modifica o filho (adiciona um arquivo) e o escaneia
        self._create_dummy_file(os.path.join(dir_filho, "file_filho_novo.txt"))
        self.client.post(reverse("atualizar_cache"), {"scan_path": dir_filho})

        # 3. Verifica a estrutura final
        estrutura = self._get_cache_structure()
        self.assertEqual(estrutura["caminho_completo"], "", "A raiz deveria ser virtual")
        self.assertEqual(len(estrutura["subpastas"]), 1, "A raiz virtual deveria ter apenas uma raiz (Pai)")
        
        raiz_pai_no_cache = estrutura["subpastas"][0]
        self.assertEqual(raiz_pai_no_cache["caminho_completo"], dir_pai)
        self.assertEqual(len(raiz_pai_no_cache["arquivos"]), 1, "A pasta Pai deveria ter 1 arquivo próprio")
        
        # Verifica se o filho está dentro do pai e se foi atualizado
        self.assertIsNotNone(raiz_pai_no_cache["subpastas"], "A pasta Pai deve ter subpastas")
        self.assertEqual(len(raiz_pai_no_cache["subpastas"]), 1, "A pasta Pai deve ter 1 subpasta (Filho)")
        self.assertEqual(raiz_pai_no_cache["subpastas"][0]["caminho_completo"], dir_filho)
        self.assertEqual(len(raiz_pai_no_cache["subpastas"][0]["arquivos"]), 1, "A subpasta Filho deveria ter sido atualizada com 1 arquivo")
        self.assertEqual(raiz_pai_no_cache["subpastas"][0]["arquivos"][0]["nome"], "file_filho_novo")
