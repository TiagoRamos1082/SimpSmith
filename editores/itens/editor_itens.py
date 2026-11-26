import sys
import shutil
import re
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ_PROJETO))

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from sistemas.catalogo_itens import CatalogoItens, CATEGORIAS_VALIDAS


def maximizar_janela(janela):
    """Maximiza uma janela Tkinter com fallback para ambientes Linux."""

    try:
        janela.state("zoomed")
        return
    except tk.TclError:
        pass

    try:
        janela.attributes("-zoomed", True)
        return
    except tk.TclError:
        pass

    try:
        janela.update_idletasks()
        largura = janela.winfo_screenwidth()
        altura = janela.winfo_screenheight()
        janela.geometry(f"{largura}x{altura}+0+0")
    except tk.TclError:
        pass


class EditorItens:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("SimpSmith â€” Editor de Itens")
        self.janela.geometry("900x560")
        self.janela.after(
            100, lambda: maximizar_janela(self.janela)
        )
        self.catalogo = CatalogoItens()
        self.item_selecionado = None
        self.imagem_item = None
        self.imagem_preview = None
        self.imagem_origem = None
        self.imagem_alterada = False
        self._configurar_estilo()
        self._montar_interface()
        self._atualizar_lista()

    def _configurar_estilo(self):
        self.cor_fundo = "#20232B"
        self.cor_painel = "#292D36"
        self.cor_campo = "#343842"
        self.cor_texto = "#F0F0F0"
        self.cor_secundaria = "#A5AAB5"
        self.cor_destaque = "#7AA2F7"

        self.janela.configure(bg=self.cor_fundo)
        self.janela.geometry("1100x720")
        self.janela.minsize(850, 600)

        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure(
            "Simp.Treeview",
            background=self.cor_painel,
            foreground=self.cor_texto,
            fieldbackground=self.cor_painel,
            rowheight=32,
            borderwidth=0,
            font=("Segoe UI", 10)
        )

        estilo.configure(
            "Simp.Treeview.Heading",
            background="#343842",
            foreground=self.cor_texto,
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )

        estilo.map(
            "Simp.Treeview",
            background=[("selected", "#405477")],
            foreground=[("selected", "#FFFFFF")]
        )

        estilo.configure(
            "Simp.TCombobox",
            fieldbackground=self.cor_campo,
            background=self.cor_campo,
            foreground=self.cor_texto,
            arrowcolor=self.cor_texto
        )

        estilo.map(
            "Simp.TCombobox",
            fieldbackground=[("readonly", self.cor_campo)],
            foreground=[("readonly", self.cor_texto)]
        )

        estilo.configure(
            "Simp.TCheckbutton",
            background=self.cor_painel,
            foreground=self.cor_texto,
            font=("Segoe UI", 9)
        )

        estilo.map(
            "Simp.TCheckbutton",
            background=[("active", self.cor_painel)]
        )

    def _voltar_central(self):
        # A Central original permanece aberta em segundo plano.
        self.janela.destroy()

    def _montar_interface(self):
        topo = tk.Frame(self.janela, bg=self.cor_fundo)
        topo.pack(fill="x", padx=25, pady=(20, 12))

        tk.Label(
            topo,
            text="Editor de Itens",
            bg=self.cor_fundo,
            fg=self.cor_texto,
            font=("Segoe UI", 23, "bold")
        ).pack(side="left")

        tk.Button(
            topo,
            text="← VOLTAR À CENTRAL",
            command=self._voltar_central,
            bg=self.cor_painel,
            fg=self.cor_texto,
            activebackground="#454B59",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=9,
            cursor="hand2",
            font=("Segoe UI", 9, "bold")
        ).pack(side="right")

        tk.Label(
            self.janela,
            text="GERENCIAMENTO DO CATÁLOGO DE ITENS",
            bg=self.cor_fundo,
            fg=self.cor_secundaria,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=27, pady=(0, 12))

        tk.Frame(
            self.janela,
            bg="#414652",
            height=1
        ).pack(fill="x", padx=25)

        principal = tk.Frame(self.janela, bg=self.cor_fundo)
        principal.pack(fill="both", expand=True, padx=25, pady=18)

        painel_lista = tk.Frame(
            principal,
            bg=self.cor_painel
        )
        painel_lista.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 14)
        )

        tk.Label(
            painel_lista,
            text="ITENS CADASTRADOS",
            bg=self.cor_painel,
            fg=self.cor_destaque,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=16, pady=(16, 10))

        tabela_container = tk.Frame(
            painel_lista,
            bg=self.cor_painel
        )
        tabela_container.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=(0, 10)
        )

        colunas = ("id", "nome", "categoria")

        self.tabela = ttk.Treeview(
            tabela_container,
            columns=colunas,
            show="headings",
            style="Simp.Treeview"
        )

        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Nome")
        self.tabela.heading("categoria", text="Categoria")

        self.tabela.column("id", width=150, minwidth=100)
        self.tabela.column("nome", width=180, minwidth=120)
        self.tabela.column("categoria", width=120, minwidth=90)

        barra = ttk.Scrollbar(
            tabela_container,
            orient="vertical",
            command=self.tabela.yview
        )

        self.tabela.configure(yscrollcommand=barra.set)

        self.tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        self.tabela.bind(
            "<<TreeviewSelect>>",
            self._selecionar_item
        )

        botoes_lista = tk.Frame(
            painel_lista,
            bg=self.cor_painel
        )
        botoes_lista.pack(fill="x", padx=14, pady=(0, 14))

        tk.Button(
            botoes_lista,
            text="+ NOVO ITEM",
            command=self._limpar_formulario,
            bg=self.cor_destaque,
            fg="#17191F",
            activebackground="#91B4FF",
            relief="flat",
            padx=15,
            pady=9,
            cursor="hand2",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        tk.Button(
            botoes_lista,
            text="EXCLUIR",
            command=self._excluir_item,
            bg=self.cor_campo,
            fg=self.cor_texto,
            activebackground="#454B59",
            relief="flat",
            padx=15,
            pady=9,
            cursor="hand2",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=8)

        # Painel de formulario com rolagem vertical
        painel_formulario = tk.Frame(
            principal,
            bg=self.cor_painel,
            width=410
        )
        painel_formulario.pack(side="right", fill="y")
        painel_formulario.pack_propagate(False)

        canvas_formulario = tk.Canvas(
            painel_formulario,
            bg=self.cor_painel,
            highlightthickness=0,
            width=390
        )
        canvas_formulario.pack(side="left", fill="both", expand=True)

        barra_formulario = ttk.Scrollbar(
            painel_formulario,
            orient="vertical",
            command=canvas_formulario.yview
        )
        barra_formulario.pack(side="right", fill="y")

        canvas_formulario.configure(
            yscrollcommand=barra_formulario.set
        )

        formulario = tk.Frame(
            canvas_formulario,
            bg=self.cor_painel
        )

        janela_formulario = canvas_formulario.create_window(
            (0, 0),
            window=formulario,
            anchor="nw"
        )

        def atualizar_regiao_scroll(event=None):
            canvas_formulario.configure(
                scrollregion=canvas_formulario.bbox("all")
            )

        def ajustar_largura_formulario(event):
            canvas_formulario.itemconfigure(
                janela_formulario,
                width=event.width
            )

        formulario.bind(
            "<Configure>",
            atualizar_regiao_scroll
        )

        canvas_formulario.bind(
            "<Configure>",
            ajustar_largura_formulario
        )

        def rolar_formulario(event):
            widget = self.janela.winfo_containing(
                event.x_root,
                event.y_root
            )

            if widget is None:
                return

            if widget == canvas_formulario or str(widget).startswith(str(formulario)):
                canvas_formulario.yview_scroll(
                    int(-event.delta / 120),
                    "units"
                )

        canvas_formulario.bind_all(
            "<MouseWheel>",
            rolar_formulario
        )

        self.janela.protocol(
            "WM_DELETE_WINDOW",
            lambda: (
                canvas_formulario.unbind_all("<MouseWheel>"),
                self.janela.destroy()
            )
        )

        tk.Label(
            formulario,
            text="DADOS DO ITEM",
            bg=self.cor_painel,
            fg=self.cor_destaque,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=18, pady=(17, 14))

        campos_texto = [
            ("id", "ID interno"),
            ("nome", "Nome de exibição"),
            ("peso", "Peso (kg)"),
            ("preco_base", "Preço base (R$)"),
            ("cor_r", "Cor vermelha (0–255)"),
            ("cor_g", "Cor verde (0–255)"),
            ("cor_b", "Cor azul (0–255)"),
        ]

        self.campos = {}

        for chave, rotulo in campos_texto:
            linha = tk.Frame(formulario, bg=self.cor_painel)
            linha.pack(fill="x", padx=18, pady=4)

            tk.Label(
                linha,
                text=rotulo,
                bg=self.cor_painel,
                fg=self.cor_secundaria,
                font=("Segoe UI", 9)
            ).pack(anchor="w")

            entrada = tk.Entry(
                linha,
                bg=self.cor_campo,
                fg=self.cor_texto,
                insertbackground=self.cor_texto,
                relief="flat",
                font=("Segoe UI", 10)
            )
            entrada.pack(fill="x", ipady=6, pady=(3, 0))

            self.campos[chave] = entrada

        tk.Label(
            formulario,
            text="Categoria",
            bg=self.cor_painel,
            fg=self.cor_secundaria,
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=18, pady=(9, 3))

        self.categoria = ttk.Combobox(
            formulario,
            values=sorted(CATEGORIAS_VALIDAS),
            state="readonly",
            style="Simp.TCombobox"
        )
        self.categoria.pack(fill="x", padx=18, ipady=4)
        self.categoria.set("minerio")

        # Imagem do item.
        tk.Label(
            formulario,
            text="IMAGEM DO ITEM",
            bg=self.cor_painel,
            fg=self.cor_destaque,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=18, pady=(18, 8))

        self.previa_imagem = tk.Label(
            formulario,
            text="Nenhuma imagem selecionada",
            bg=self.cor_campo,
            fg=self.cor_secundaria,
            width=24,
            height=7
        )
        self.previa_imagem.pack(padx=18, pady=5)

        tk.Button(
            formulario,
            text="SELECIONAR IMAGEM",
            command=self._selecionar_imagem,
            bg=self.cor_campo,
            fg=self.cor_texto,
            activebackground="#454B59",
            relief="flat",
            padx=12,
            pady=9,
            cursor="hand2"
        ).pack(fill="x", padx=18, pady=(8, 4))

        tk.Button(
            formulario,
            text="REMOVER IMAGEM",
            command=self._remover_imagem,
            bg=self.cor_campo,
            fg=self.cor_secundaria,
            activebackground="#454B59",
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2"
        ).pack(fill="x", padx=18, pady=(0, 12))

        tk.Button(
            formulario,
            text="SALVAR ITEM",
            command=self._salvar_item,
            bg=self.cor_destaque,
            fg="#17191F",
            activebackground="#91B4FF",
            relief="flat",
            padx=12,
            pady=11,
            cursor="hand2",
            font=("Segoe UI", 9, "bold")
        ).pack(fill="x", padx=18, pady=(18, 8))

        tk.Label(
            formulario,
            text="Use o ID no código e o nome na interface.",
            bg=self.cor_painel,
            fg=self.cor_secundaria,
            font=("Segoe UI", 8),
            wraplength=330
        ).pack(anchor="w", padx=18, pady=(4, 12))

        rodape = tk.Frame(self.janela, bg=self.cor_fundo)
        rodape.pack(fill="x", padx=25, pady=(0, 16))

        self.status = tk.Label(
            rodape,
            text="Editor de Itens pronto.",
            bg=self.cor_fundo,
            fg=self.cor_secundaria,
            font=("Segoe UI", 9)
        )
        self.status.pack(side="left")

        tk.Label(
            rodape,
            text="SimpSmith Tools",
            bg=self.cor_fundo,
            fg=self.cor_secundaria,
            font=("Segoe UI", 9)
        ).pack(side="right")
    def _atualizar_lista(self, selecionar_id=None):
        for linha in self.tabela.get_children():
            self.tabela.delete(linha)

        for item in self.catalogo.listar():
            self.tabela.insert(
                "", "end", iid=item["id"],
                values=(item["id"], item["nome"], item["categoria"])
            )

        if selecionar_id and self.tabela.exists(selecionar_id):
            self.tabela.selection_set(selecionar_id)
            self.tabela.focus(selecionar_id)

    def _selecionar_item(self, _evento=None):
        selecionados = self.tabela.selection()
        if not selecionados:
            return

        item_id = selecionados[0]
        item = self.catalogo.obter(item_id)
        if item is None:
            return

        self.item_selecionado = item_id
        valores = {
            "id": item["id"],
            "nome": item["nome"],
            "peso": item["peso"],
            "preco_base": item["preco_base"],
            "cor_r": item["cor"][0],
            "cor_g": item["cor"][1],
            "cor_b": item["cor"][2],
        }

        for chave, valor in valores.items():
            campo = self.campos[chave]
            campo.delete(0, tk.END)
            campo.insert(0, str(valor))


        self.categoria.set(item["categoria"])
        self._definir_imagem(item.get("imagem"))

    def _limpar_formulario(self):
        self.item_selecionado = None
        self.tabela.selection_remove(self.tabela.selection())

        valores = {
            "id": "",
            "nome": "",
            "peso": "1.0",
            "preco_base": "0.0",
            "cor_r": "150",
            "cor_g": "150",
            "cor_b": "150",
        }

        for chave, valor in valores.items():
            campo = self.campos[chave]
            campo.delete(0, tk.END)
            campo.insert(0, valor)


        self.categoria.set("material")
        self._definir_imagem(None)

    def _selecionar_imagem(self):
        caminho = filedialog.askopenfilename(
            parent=self.janela,
            title="Selecionar imagem do item",
            initialdir=str(RAIZ_PROJETO / "assets" / "itens"),
            filetypes=[("Imagens PNG", "*.png")]
        )

        if not caminho:
            return

        origem = Path(caminho).resolve()

        if not origem.is_file() or origem.suffix.lower() != ".png":
            messagebox.showerror(
                "Imagem inválida",
                "Selecione um arquivo PNG válido."
            )
            return

        self.imagem_origem = origem
        self.imagem_alterada = True
        self._mostrar_previa(origem)

    def _mostrar_previa(self, arquivo_imagem):
        try:
            imagem = tk.PhotoImage(file=str(arquivo_imagem))

            largura_original = imagem.width()
            altura_original = imagem.height()

            largura_maxima = 180
            altura_maxima = 140

            fator = max(
                1,
                (largura_original + largura_maxima - 1) // largura_maxima,
                (altura_original + altura_maxima - 1) // altura_maxima
            )

            if fator > 1:
                imagem = imagem.subsample(fator, fator)

            self.imagem_preview = imagem

            self.previa_imagem.configure(
                image=self.imagem_preview,
                text="",
                width=largura_maxima,
                height=altura_maxima,
                anchor="center"
            )

        except (OSError, tk.TclError):
            self.imagem_preview = None
            self.previa_imagem.configure(
                image="",
                text="Imagem não encontrada ou inválida"
            )

    def _definir_imagem(self, caminho):
        self.imagem_item = caminho
        self.imagem_origem = None
        self.imagem_alterada = False
        self.imagem_preview = None

        if not caminho:
            self.previa_imagem.configure(
                image="",
                text="Nenhuma imagem selecionada"
            )
            return

        arquivo_imagem = (RAIZ_PROJETO / caminho).resolve()

        try:
            arquivo_imagem.relative_to(RAIZ_PROJETO.resolve())
            self._mostrar_previa(arquivo_imagem)

        except ValueError:
            self.previa_imagem.configure(
                image="",
                text="Caminho de imagem inválido"
            )

    def _remover_imagem(self):
        self.imagem_item = None
        self.imagem_origem = None
        self.imagem_alterada = True
        self.imagem_preview = None

        self.previa_imagem.configure(
            image="",
            text="Nenhuma imagem selecionada"
        )

    def _preparar_imagem_para_salvar(self, dados):
        categoria_pastas = {
            "minerio": "minerios",
            "material": "materiais",
            "item": "itens",
            "construcao": "construcoes",
        }

        item_id = str(dados["id"]).strip().lower()
        categoria = dados["categoria"]

        if not re.fullmatch(r"[a-z0-9_-]+", item_id):
            raise ValueError("O ID do item não pode conter caracteres inválidos.")

        if categoria not in categoria_pastas:
            raise ValueError("Categoria inválida para armazenamento da imagem.")

        if not self.imagem_alterada:
            dados["imagem"] = self.imagem_item
            return None

        if self.imagem_origem is None:
            dados["imagem"] = None
            return None

        origem = self.imagem_origem.resolve()

        if not origem.is_file() or origem.suffix.lower() != ".png":
            raise ValueError("A imagem selecionada não está mais disponível.")

        pasta = (
            RAIZ_PROJETO
            / "assets"
            / "itens"
            / categoria_pastas[categoria]
            / item_id
        )

        destino = pasta / f"{item_id}.png"
        temporario = pasta / f".{item_id}.tmp.png"

        pasta.mkdir(parents=True, exist_ok=True)

        try:
            if origem != destino.resolve():
                shutil.copy2(origem, temporario)
            else:
                return destino.relative_to(RAIZ_PROJETO).as_posix(), None

        except OSError:
            temporario.unlink(missing_ok=True)
            raise

        dados["imagem"] = destino.relative_to(RAIZ_PROJETO).as_posix()

        return destino, temporario

    def _limpar_imagem_antiga(self, caminho_antigo, caminho_novo):
        if not caminho_antigo or caminho_antigo == caminho_novo:
            return

        raiz_itens = (RAIZ_PROJETO / "assets" / "itens").resolve()
        arquivo_antigo = (RAIZ_PROJETO / caminho_antigo).resolve()

        try:
            relativo = arquivo_antigo.relative_to(raiz_itens)
        except ValueError:
            return

        if len(relativo.parts) != 3 or not arquivo_antigo.is_file():
            return

        arquivo_antigo.unlink()

        try:
            arquivo_antigo.parent.rmdir()
        except OSError:
            pass

    def _dados_formulario(self):
        try:
            cor = [
                int(self.campos["cor_r"].get()),
                int(self.campos["cor_g"].get()),
                int(self.campos["cor_b"].get()),
            ]

            item_atual = (
                self.catalogo.obter(self.item_selecionado)
                if self.item_selecionado is not None
                else None
            )

            return {
                "id": self.campos["id"].get(),
                "nome": self.campos["nome"].get(),
                "categoria": self.categoria.get(),
                "peso": float(self.campos["peso"].get()),
                "preco_base": float(self.campos["preco_base"].get()),
                "cor": cor,
                "imagem": self.imagem_item,
                "largura_visual": item_atual["largura_visual"] if item_atual else 32,
                "altura_visual": item_atual["altura_visual"] if item_atual else 32,
            }
        except ValueError as erro:
            raise ValueError(
                "Verifique se peso, preço, tempo e valores RGB são números válidos."
            ) from erro

    def _salvar_item(self):
        temporario = None

        try:
            dados = self._dados_formulario()

            item_antigo = (
                self.catalogo.obter(self.item_selecionado)
                if self.item_selecionado is not None
                else None
            )

            imagem_antiga = (
                item_antigo.get("imagem")
                if item_antigo
                else None
            )

            resultado = self._preparar_imagem_para_salvar(dados)

            if resultado is not None:
                if isinstance(resultado, tuple):
                    _, temporario = resultado
                else:
                    dados["imagem"] = resultado[0]

            if self.item_selecionado is None:
                item = self.catalogo.cadastrar(dados)
            else:
                item = self.catalogo.atualizar(
                    self.item_selecionado,
                    dados
                )

            if temporario is not None:
                temporario.replace(dados["imagem"] and (
                    RAIZ_PROJETO / dados["imagem"]
                ))
                temporario = None

            self._limpar_imagem_antiga(
                imagem_antiga,
                item.get("imagem")
            )

            self.item_selecionado = item["id"]
            self.imagem_item = item.get("imagem")
            self.imagem_origem = None
            self.imagem_alterada = False

            self._atualizar_lista(item["id"])
            self._definir_imagem(item.get("imagem"))

            messagebox.showinfo("Sucesso", "Item salvo com sucesso.")

        except (ValueError, OSError, shutil.Error) as erro:
            if temporario is not None:
                temporario.unlink(missing_ok=True)

            messagebox.showerror(
                "Não foi possível salvar",
                str(erro)
            )

    def _excluir_item(self):
        selecionados = self.tabela.selection()
        if not selecionados:
            messagebox.showwarning("AtenÃ§Ã£o", "Selecione um item para excluir.")
            return

        item_id = selecionados[0]
        confirmar = messagebox.askyesno(
            "Confirmar exclusÃ£o",
            f"Deseja excluir '{item_id}' do catÃ¡logo?\n"
            "Isso nÃ£o remove automaticamente referÃªncias em Ã¡reas do mapa ou receitas."
        )
        if not confirmar:
            return

        try:
            self.catalogo.excluir(item_id)
            self._limpar_formulario()
            self._atualizar_lista()
        except (ValueError, OSError) as erro:
            messagebox.showerror("NÃ£o foi possÃ­vel excluir", str(erro))


def main():
    janela = tk.Tk()
    EditorItens(janela)
    janela.mainloop()


if __name__ == "__main__":
    main()


