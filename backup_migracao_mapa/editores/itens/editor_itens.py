import sys
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ_PROJETO))

import tkinter as tk
from tkinter import ttk, messagebox

from sistemas.catalogo_itens import CatalogoItens, CATEGORIAS_VALIDAS


class EditorItens:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("SimpSmith — Editor de Itens")
        self.janela.geometry("900x560")
        self.catalogo = CatalogoItens()
        self.item_selecionado = None

        self._montar_interface()
        self._atualizar_lista()

    def _montar_interface(self):
        principal = ttk.Frame(self.janela, padding=12)
        principal.pack(fill="both", expand=True)

        painel_lista = ttk.Frame(principal)
        painel_lista.pack(side="left", fill="both", expand=True, padx=(0, 12))

        ttk.Label(painel_lista, text="Itens cadastrados").pack(anchor="w")
        colunas = ("id", "nome", "categoria")
        self.tabela = ttk.Treeview(
            painel_lista, columns=colunas, show="headings", height=20
        )
        self.tabela.heading("id", text="ID")
        self.tabela.heading("nome", text="Nome")
        self.tabela.heading("categoria", text="Categoria")
        self.tabela.column("id", width=110)
        self.tabela.column("nome", width=150)
        self.tabela.column("categoria", width=100)
        self.tabela.pack(fill="both", expand=True, pady=8)
        self.tabela.bind("<<TreeviewSelect>>", self._selecionar_item)

        botoes_lista = ttk.Frame(painel_lista)
        botoes_lista.pack(fill="x")
        ttk.Button(botoes_lista, text="Novo", command=self._limpar_formulario).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(botoes_lista, text="Excluir", command=self._excluir_item).pack(
            side="left"
        )

        formulario = ttk.LabelFrame(principal, text="Dados do item", padding=12)
        formulario.pack(side="right", fill="y")

        self.campos = {}
        campos_texto = [
            ("id", "ID interno"),
            ("nome", "Nome de exibição"),
            ("peso", "Peso (kg)"),
            ("preco_base", "Preço base (R$)"),
            ("tempo_coleta", "Tempo de coleta (s)"),
            ("cor_r", "Cor vermelha (0–255)"),
            ("cor_g", "Cor verde (0–255)"),
            ("cor_b", "Cor azul (0–255)"),
        ]

        for linha, (chave, rotulo) in enumerate(campos_texto):
            ttk.Label(formulario, text=rotulo).grid(
                row=linha, column=0, sticky="w", pady=4
            )
            entrada = ttk.Entry(formulario, width=26)
            entrada.grid(row=linha, column=1, sticky="ew", pady=4)
            self.campos[chave] = entrada

        linha_categoria = len(campos_texto)
        ttk.Label(formulario, text="Categoria").grid(
            row=linha_categoria, column=0, sticky="w", pady=4
        )
        self.categoria = ttk.Combobox(
            formulario,
            values=sorted(CATEGORIAS_VALIDAS),
            state="readonly",
            width=23,
        )
        self.categoria.grid(row=linha_categoria, column=1, sticky="ew", pady=4)
        self.categoria.set("minerio")

        self.solido = tk.BooleanVar(value=True)
        self.respawn = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            formulario, text="Possui colisão sólida", variable=self.solido
        ).grid(row=linha_categoria + 1, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Checkbutton(
            formulario, text="Pode reaparecer (respawn)", variable=self.respawn
        ).grid(row=linha_categoria + 2, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Button(
            formulario, text="Salvar item", command=self._salvar_item
        ).grid(
            row=linha_categoria + 3, column=0, columnspan=2, sticky="ew", pady=(14, 4)
        )
        ttk.Label(
            formulario,
            text="Ex.: ID 'cristal_azul'\nUse o ID no código e o nome na interface.",
        ).grid(row=linha_categoria + 4, column=0, columnspan=2, sticky="w", pady=(8, 0))

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
            "tempo_coleta": item["tempo_coleta"],
            "cor_r": item["cor"][0],
            "cor_g": item["cor"][1],
            "cor_b": item["cor"][2],
        }

        for chave, valor in valores.items():
            campo = self.campos[chave]
            campo.delete(0, tk.END)
            campo.insert(0, str(valor))

        self.categoria.set(item["categoria"])
        self.solido.set(item["solido"])
        self.respawn.set(item["respawn"])

    def _limpar_formulario(self):
        self.item_selecionado = None
        self.tabela.selection_remove(self.tabela.selection())

        valores = {
            "id": "",
            "nome": "",
            "peso": "1.0",
            "preco_base": "0.0",
            "tempo_coleta": "2.0",
            "cor_r": "150",
            "cor_g": "150",
            "cor_b": "150",
        }

        for chave, valor in valores.items():
            campo = self.campos[chave]
            campo.delete(0, tk.END)
            campo.insert(0, valor)

        self.categoria.set("material")
        self.solido.set(False)
        self.respawn.set(False)

    def _dados_formulario(self):
        try:
            cor = [
                int(self.campos["cor_r"].get()),
                int(self.campos["cor_g"].get()),
                int(self.campos["cor_b"].get()),
            ]
            return {
                "id": self.campos["id"].get(),
                "nome": self.campos["nome"].get(),
                "categoria": self.categoria.get(),
                "peso": float(self.campos["peso"].get()),
                "preco_base": float(self.campos["preco_base"].get()),
                "tempo_coleta": float(self.campos["tempo_coleta"].get()),
                "cor": cor,
                "solido": self.solido.get(),
                "respawn": self.respawn.get(),
            }
        except ValueError as erro:
            raise ValueError(
                "Verifique se peso, preço, tempo e valores RGB são números válidos."
            ) from erro

    def _salvar_item(self):
        try:
            dados = self._dados_formulario()

            if self.item_selecionado is None:
                item = self.catalogo.cadastrar(dados)
            else:
                item = self.catalogo.atualizar(self.item_selecionado, dados)

            self.item_selecionado = item["id"]
            self._atualizar_lista(item["id"])
            messagebox.showinfo("Sucesso", "Item salvo com sucesso.")
        except (ValueError, OSError) as erro:
            messagebox.showerror("Não foi possível salvar", str(erro))

    def _excluir_item(self):
        selecionados = self.tabela.selection()
        if not selecionados:
            messagebox.showwarning("Atenção", "Selecione um item para excluir.")
            return

        item_id = selecionados[0]
        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja excluir '{item_id}' do catálogo?\n"
            "Isso não remove automaticamente referências em áreas do mapa ou receitas."
        )
        if not confirmar:
            return

        try:
            self.catalogo.excluir(item_id)
            self._limpar_formulario()
            self._atualizar_lista()
        except (ValueError, OSError) as erro:
            messagebox.showerror("Não foi possível excluir", str(erro))


def main():
    janela = tk.Tk()
    EditorItens(janela)
    janela.mainloop()


if __name__ == "__main__":
    main()
