
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
from collections import defaultdict

# Adicionando o caminho do projeto ao sys.path para garantir que as importações funcionem
import sys
sys.path.append(os.path.dirname(__file__))

from Manipulador.ManipuladorPasta import ManipuladorPasta
from Classe.Pasta import Pasta
from Classe.Arquivo import Arquivo

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Analisador de Arquivos")
        self.root.geometry("800x600")

        self.manipulador = None

        self.create_widgets()

    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Botão e Status
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)

        self.analysis_button = ttk.Button(top_frame, text="Iniciar Análise da Pasta './Arq'", command=self.start_analysis_thread)
        self.analysis_button.pack(side=tk.LEFT, padx=(0, 10))

        self.status_label = ttk.Label(top_frame, text="Pronto para iniciar.")
        self.status_label.pack(side=tk.LEFT)

        # Abas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)

        # Aba de Estrutura de Arquivos
        self.tree_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tree_frame, text="Estrutura de Pastas")
        self.create_file_tree_view()

        # Aba de Duplicatas
        self.duplicates_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.duplicates_frame, text="Arquivos Duplicados")
        self.create_duplicates_view()

        # Aba de Gráficos
        self.graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_frame, text="Gráficos")
        self.canvas_grafico = tk.Canvas(self.graph_frame, bg="white")
        self.canvas_grafico.pack(fill=tk.BOTH, expand=True)


    def create_file_tree_view(self):
        self.file_tree = ttk.Treeview(self.tree_frame, columns=("size", "hash"), selectmode="browse")
        self.file_tree.heading("#0", text="Nome")
        self.file_tree.heading("size", text="Tamanho (bytes)")
        self.file_tree.heading("hash", text="Hash MD5 (início)")
        self.file_tree.pack(fill=tk.BOTH, expand=True)

    def create_duplicates_view(self):
        self.duplicates_tree = ttk.Treeview(self.duplicates_frame, columns=("path", "size", "hash"), selectmode="browse")
        self.duplicates_tree.heading("#0", text="Arquivo")
        self.duplicates_tree.heading("path", text="Caminho")
        self.duplicates_tree.heading("size", text="Tamanho (bytes)")
        self.duplicates_tree.heading("hash", text="Hash MD5")
        self.duplicates_tree.pack(fill=tk.BOTH, expand=True)

    def start_analysis_thread(self):
        self.analysis_button.config(state=tk.DISABLED)
        self.status_label.config(text="Analisando... Isso pode levar um tempo.")
        
        # Limpa as visualizações antigas
        for i in self.file_tree.get_children():
            self.file_tree.delete(i)
        for i in self.duplicates_tree.get_children():
            self.duplicates_tree.delete(i)

        # Inicia a análise em uma nova thread para não congelar a UI
        thread = threading.Thread(target=self.run_analysis)
        thread.daemon = True
        thread.start()

    def run_analysis(self):
        try:
            # A lógica principal do seu projeto é chamada aqui
            self.manipulador = ManipuladorPasta("./Arq")
            duplicatas = self.manipulador.detectar_duplicatas() # Modificado para retornar as duplicatas

            # Após a conclusão, agenda a atualização da UI na thread principal
            self.root.after(0, self.update_ui, self.manipulador.raiz, duplicatas)
        except Exception as e:
            self.root.after(0, self.show_error, str(e))

    def update_ui(self, raiz, duplicatas):
        # Preenche a árvore de estrutura de arquivos
        self.populate_file_tree(raiz)
        
        # Preenche a tabela de duplicatas
        if duplicatas:
            self.populate_duplicates_view(duplicatas)
        
        # Gera os gráficos
        self.generate_graphs(raiz)

        self.status_label.config(text="Análise concluída.")
        self.analysis_button.config(state=tk.NORMAL)

    def populate_file_tree(self, pasta, parent_id=""):
        # Insere a pasta atual na árvore
        folder_id = self.file_tree.insert(parent_id, "end", text=f"📁 {pasta.nome}", open=True)
        
        # Adiciona os arquivos da pasta
        for arq in pasta.arquivos:
            hash_display = arq.hash_md5[:12] if arq.hash_md5 else "N/A"
            self.file_tree.insert(folder_id, "end", text=f"  - {arq.nome}.{arq.extensao}", values=(arq.tamanho, hash_display))
            
        # Chama recursivamente para as subpastas
        subpasta_no = pasta.subpastas
        while subpasta_no:
            self.populate_file_tree(subpasta_no.pasta, parent_id=folder_id)
            subpasta_no = subpasta_no.proximo

    def populate_duplicates_view(self, duplicatas):
        for tamanho, hash_value, grupo in duplicatas:
            # Adiciona um nó pai para o grupo de duplicatas
            parent_id = self.duplicates_tree.insert("", "end", text=f"Grupo (Hash: {hash_value[:12]}...)", open=True)
            for _, arquivo in grupo:
                self.duplicates_tree.insert(parent_id, "end", text=arquivo.nome, values=(arquivo.caminho_completo, arquivo.tamanho, hash_value))

    def generate_graphs(self, raiz):
        # 1. Coletar dados para o gráfico
        ext_data = defaultdict(int)
        todos_arquivos = raiz.coletar_arquivos()
        for _, arquivo in todos_arquivos:
            ext_data[arquivo.extensao] += arquivo.tamanho
            
        # Limpa o gráfico anterior
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        # 2. Criar a figura com Matplotlib
        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        if not ext_data:
            ax.text(0.5, 0.5, "Nenhum dado para exibir.", horizontalalignment='center', verticalalignment='center')
        else:
            labels = ext_data.keys()
            sizes = ext_data.values()
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')  # Assegura que a pizza seja um círculo
            ax.set_title("Distribuição de Espaço por Tipo de Arquivo")

        # 3. Embutir o gráfico no Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def show_error(self, error_message):
        messagebox.showerror("Erro na Análise", error_message)
        self.status_label.config(text="Ocorreu um erro.")
        self.analysis_button.config(state=tk.NORMAL)


if __name__ == "__main__":
    # Modificação para que o script encontre a pasta Arq corretamente
    # Assumindo que o script está na raiz do projeto
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    root = tk.Tk()
    app = App(root)
    root.mainloop()
