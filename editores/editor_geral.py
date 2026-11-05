import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_EDITORES = RAIZ / "editores"

EDITORES = {
    "MAPAS": [
        {
            "nome": "Editor de Mapas",
            "descricao": "Criacao e edicao dos mapas do jogo.",
            "arquivo": "mapas/editor_mapa.py",
            "icone": "MAP"
        },
        {
            "nome": "Editor de Colisoes",
            "descricao": "Colisoes do mapa, sprites e interacoes.",
            "arquivo": "mapas/editor_colisoes.py",
            "icone": "COL"
        },
        {
            "nome": "Editor de Recursos",
            "descricao": "Posicionamento e configuracao de recursos.",
            "arquivo": "mapas/editor_recursos.py",
            "icone": "REC"
        }
    ],
    "CONTEUDO": [
        {
            "nome": "Editor de Itens",
            "descricao": "Cadastro e configuracao dos itens.",
            "arquivo": "itens/editor_itens.py",
            "icone": "ITE"
        }
    ],
    "TILES E SPRITES": [
        {
            "nome": "Editor de Sprites",
            "descricao": "Organizacao e edicao dos sprites.",
            "arquivo": "tiles/editor_sprites.py",
            "icone": "SPR"
        },
        {
            "nome": "Importador de Tiles",
            "descricao": "Importacao de tiles para o projeto.",
            "arquivo": "tiles/importador.py",
            "icone": "IMP"
        }
    ]
}


class CentralEditores:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("SimpSmith | Central de Editores")
        self.janela.geometry("1050x760")
        self.janela.after(100, lambda: self.janela.state("zoomed"))
        self.janela.minsize(850, 650)
        self.processos = []
        self._scroll_resto = 0

        self.cor_fundo = "#17191F"
        self.cor_painel = "#22252D"
        self.cor_destaque = "#D99B45"
        self.cor_texto = "#F1F1F1"
        self.cor_secundaria = "#A0A5B0"

        self.janela.configure(bg=self.cor_fundo)

        self.configurar_estilo()
        self.criar_interface()

    def configurar_estilo(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure(
            "Treeview",
            background=self.cor_painel,
            foreground=self.cor_texto,
            fieldbackground=self.cor_painel,
            rowheight=27,
            borderwidth=0
        )
        estilo.configure(
            "Treeview.Heading",
            background="#30343E",
            foreground=self.cor_texto,
            font=("Segoe UI", 10, "bold")
        )

    def criar_interface(self):
        topo = tk.Frame(self.janela, bg=self.cor_fundo)
        topo.pack(fill="x", padx=30, pady=(25, 15))

        tk.Label(
            topo,
            text="SimpSmith",
            bg=self.cor_fundo,
            fg=self.cor_texto,
            font=("Segoe UI", 27, "bold")
        ).pack(anchor="w")

        tk.Label(
            topo,
            text="CENTRAL DE DESENVOLVIMENTO",
            bg=self.cor_fundo,
            fg=self.cor_secundaria,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(3, 0))

        linha = tk.Frame(self.janela, bg="#343842", height=1)
        linha.pack(fill="x", padx=30, pady=10)

        # Area rolavel da central
        container_scroll = tk.Frame(self.janela, bg=self.cor_fundo)
        container_scroll.pack(fill="both", expand=True, padx=30, pady=10)

        self.canvas = tk.Canvas(
            container_scroll,
            bg=self.cor_fundo,
            highlightthickness=0,
            borderwidth=0
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            container_scroll,
            orient="vertical",
            command=self.canvas.yview
        )
        scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.area = tk.Frame(self.canvas, bg=self.cor_fundo)

        self.janela_area = self.canvas.create_window(
            (0, 0),
            window=self.area,
            anchor="nw"
        )

        self.area.bind(
            "<Configure>",
            lambda evento: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.bind(
            "<Configure>",
            lambda evento: self.canvas.itemconfigure(
                self.janela_area,
                width=evento.width
            )
        )

        # Scroll global: a função verifica se o ponteiro está sobre a área.
        self.janela.bind_all("<MouseWheel>", self._rolar_mouse)

        for categoria, ferramentas in EDITORES.items():
            self.criar_categoria(categoria, ferramentas)

        rodape = tk.Frame(self.janela, bg=self.cor_fundo)
        rodape.pack(fill="x", padx=30, pady=(10, 22))

        self.status = tk.Label(
            rodape,
            text="Central pronta.",
            bg=self.cor_fundo,
            fg=self.cor_secundaria,
            font=("Segoe UI", 9)
        )
        self.status.pack(side="left")

        tk.Button(
            rodape,
            text="INVENTARIO DO PROJETO",
            command=self.abrir_inventario,
            bg="#343842",
            fg=self.cor_texto,
            activebackground="#454B59",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=9,
            cursor="hand2"
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            rodape,
            text="ABRIR PASTA",
            command=lambda: os.startfile(str(PASTA_EDITORES)),
            bg="#343842",
            fg=self.cor_texto,
            activebackground="#454B59",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=9,
            cursor="hand2"
        ).pack(side="right")

    def _rolar_mouse(self, evento):
        # Ignora a rolagem quando o mouse está fora da área de conteúdo.
        mouse_x, mouse_y = self.janela.winfo_pointerxy()

        esquerda = self.canvas.winfo_rootx()
        topo = self.canvas.winfo_rooty()
        direita = esquerda + self.canvas.winfo_width()
        base = topo + self.canvas.winfo_height()

        if not (esquerda <= mouse_x <= direita and topo <= mouse_y <= base):
            return

        self._scroll_resto += evento.delta
        passos = int(self._scroll_resto / 120)

        if passos:
            self.canvas.yview_scroll(-passos, "units")
            self._scroll_resto -= passos * 120

    def criar_categoria(self, categoria, ferramentas):
        tk.Label(
            self.area,
            text=categoria,
            bg=self.cor_fundo,
            fg=self.cor_destaque,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(12, 7))

        grade = tk.Frame(self.area, bg=self.cor_fundo)
        grade.pack(fill="x")

        for indice, ferramenta in enumerate(ferramentas):
            linha = indice // 2
            coluna = indice % 2

            grade.grid_columnconfigure(coluna, weight=1)

            self.criar_cartao(
                grade,
                ferramenta,
                linha,
                coluna
            )

    def criar_cartao(self, pai, ferramenta, linha, coluna):
        caminho = PASTA_EDITORES / ferramenta["arquivo"]
        existe = caminho.is_file()

        cartao = tk.Frame(
            pai,
            bg=self.cor_painel,
            padx=15,
            pady=13,
            highlightthickness=1,
            highlightbackground="#343842"
        )
        cartao.grid(
            row=linha,
            column=coluna,
            sticky="nsew",
            padx=(0, 10) if coluna == 0 else (5, 0),
            pady=5
        )

        cabecalho = tk.Frame(cartao, bg=self.cor_painel)
        cabecalho.pack(fill="x")

        tk.Label(
            cabecalho,
            text=ferramenta["icone"],
            bg="#343842",
            fg=self.cor_destaque,
            font=("Segoe UI", 10, "bold"),
            width=5,
            pady=5
        ).pack(side="left")

        tk.Label(
            cabecalho,
            text="DISPONIVEL" if existe else "NAO ENCONTRADO",
            bg=self.cor_painel,
            fg="#75C995" if existe else "#E77D7D",
            font=("Segoe UI", 8, "bold")
        ).pack(side="right")

        tk.Label(
            cartao,
            text=ferramenta["nome"],
            bg=self.cor_painel,
            fg=self.cor_texto,
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(10, 3))

        tk.Label(
            cartao,
            text=ferramenta["descricao"],
            bg=self.cor_painel,
            fg=self.cor_secundaria,
            font=("Segoe UI", 9),
            wraplength=390,
            justify="left"
        ).pack(anchor="w", pady=(0, 10))

        tk.Button(
            cartao,
            text="ABRIR FERRAMENTA" if existe else "ARQUIVO AUSENTE",
            command=lambda p=caminho, n=ferramenta["nome"]: self.abrir_editor(p, n),
            state="normal" if existe else "disabled",
            bg=self.cor_destaque if existe else "#454545",
            fg="#17191F",
            activebackground="#EAB66F",
            activeforeground="#17191F",
            disabledforeground="#999999",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=7,
            cursor="hand2" if existe else "arrow"
        ).pack(anchor="e")

    def abrir_editor(self, caminho, nome):
        try:
            processo = subprocess.Popen(
                [sys.executable, str(caminho)],
                cwd=str(RAIZ)
            )

            self.processos.append((processo, nome))
            self.status.config(text=f"{nome} iniciado.")

        except Exception as erro:
            messagebox.showerror(
                "Erro ao abrir editor",
                f"Nao foi possivel abrir {nome}.\n\n{erro}"
            )

    def abrir_inventario(self):
        janela = tk.Toplevel(self.janela)
        janela.title("SimpSmith | Inventario")
        janela.geometry("750x600")
        janela.configure(bg=self.cor_fundo)

        tk.Label(
            janela,
            text="Inventario de Editores",
            bg=self.cor_fundo,
            fg=self.cor_texto,
            font=("Segoe UI", 19, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))

        tk.Label(
            janela,
            text="Arquivos encontrados dentro de editores/",
            bg=self.cor_fundo,
            fg=self.cor_secundaria,
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=20, pady=(0, 15))

        container = tk.Frame(janela, bg=self.cor_fundo)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        arvore = ttk.Treeview(
            container,
            columns=("tipo",),
            show="tree headings"
        )

        arvore.heading("#0", text="Nome")
        arvore.heading("tipo", text="Tipo")
        arvore.column("#0", width=480)
        arvore.column("tipo", width=130, anchor="center")

        barra = ttk.Scrollbar(
            container,
            orient="vertical",
            command=arvore.yview
        )
        arvore.configure(yscrollcommand=barra.set)

        arvore.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        raiz_id = arvore.insert(
            "",
            "end",
            text="editores/",
            values=("Diretorio",),
            open=True
        )

        contagem = {"arquivos": 0, "pastas": 0}

        def percorrer(pasta, pai):
            try:
                itens = sorted(
                    pasta.iterdir(),
                    key=lambda p: (p.is_file(), p.name.lower())
                )
            except PermissionError:
                return

            for item in itens:
                if item.name == "__pycache__":
                    continue

                if item.is_dir():
                    contagem["pastas"] += 1
                    novo = arvore.insert(
                        pai,
                        "end",
                        text=item.name + "/",
                        values=("Diretorio",)
                    )
                    percorrer(item, novo)
                else:
                    contagem["arquivos"] += 1
                    arvore.insert(
                        pai,
                        "end",
                        text=item.name,
                        values=(item.suffix or "Arquivo",)
                    )

        percorrer(PASTA_EDITORES, raiz_id)

        tk.Label(
            janela,
            text=f"{contagem['pastas']} pastas | "
                 f"{contagem['arquivos']} arquivos",
            bg=self.cor_fundo,
            fg=self.cor_secundaria,
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=20, pady=(5, 15))


if __name__ == "__main__":
    janela = tk.Tk()
    app = CentralEditores(janela)
    janela.mainloop()

