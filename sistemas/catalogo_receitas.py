
import json
from pathlib import Path


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_RECEITAS = (
    RAIZ_PROJETO / "dados" / "receitas" / "processamento.json"
)


class CatalogoReceitas:
    def __init__(self, caminho=CAMINHO_RECEITAS):
        self.caminho = Path(caminho)
        self.receitas = {}
        self.carregar()

    def carregar(self):
        if not self.caminho.exists():
            self.receitas = {}
            return

        try:
            with self.caminho.open("r", encoding="utf-8-sig") as arquivo:
                dados = json.load(arquivo)
        except json.JSONDecodeError as erro:
            raise ValueError(
                f"Arquivo de receitas contém JSON inválido: {erro}"
            ) from erro

        receitas = {}

        for receita in dados.get("receitas", []):
            self._validar(receita)

            receita_id = receita["id"]

            if receita_id in receitas:
                raise ValueError(
                    f"ID de receita duplicado: {receita_id}"
                )

            receitas[receita_id] = receita

        self.receitas = receitas

    def obter(self, receita_id):
        return self.receitas.get(receita_id)

    def listar(self):
        return list(self.receitas.values())

    def listar_por_estacao(self, estacao):
        return [
            receita
            for receita in self.receitas.values()
            if receita["estacao"] == estacao
        ]

    @staticmethod
    def _validar(receita):
        campos = {
            "id", "nome", "tipo",
            "estacao", "ingredientes", "resultado"
        }

        if not isinstance(receita, dict):
            raise ValueError("Cada receita precisa ser um objeto.")

        if not campos.issubset(receita):
            raise ValueError("Receita possui campos obrigatórios ausentes.")

        if not all(
            isinstance(receita[campo], str) and receita[campo].strip()
            for campo in ("id", "nome", "tipo", "estacao")
        ):
            raise ValueError("Identificação da receita inválida.")

        for campo in ("ingredientes", "resultado"):
            itens = receita[campo]

            if not isinstance(itens, dict) or not itens:
                raise ValueError(f"{campo} precisa conter itens.")

            if any(
                not isinstance(item_id, str)
                or not item_id.strip()
                or isinstance(quantidade, bool)
                or not isinstance(quantidade, int)
                or quantidade <= 0
                for item_id, quantidade in itens.items()
            ):
                raise ValueError(f"Dados inválidos em {campo}.")
