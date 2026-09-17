import json
import re
from pathlib import Path


# Caminho baseado na localização deste arquivo, não no diretório do terminal.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_ITENS = RAIZ_PROJETO / "dados" / "itens.json"

CATEGORIAS_VALIDAS = {"minerio", "planta", "material", "item"}


class CatalogoItens:
    def __init__(self, caminho=CAMINHO_ITENS):
        self.caminho = Path(caminho)
        self.itens = {}
        self.carregar()

    def carregar(self):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)

        if not self.caminho.exists():
            self.itens = {}
            self.salvar()
            return

        try:
            with self.caminho.open("r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
        except json.JSONDecodeError as erro:
            raise ValueError(
                f"O arquivo {self.caminho} contém JSON inválido: {erro}"
            ) from erro

        itens = dados.get("itens", [])
        self.itens = {}

        for item in itens:
            self._validar(item)
            item_id = item["id"]
            if item_id in self.itens:
                raise ValueError(f"ID duplicado no JSON: {item_id}")
            self.itens[item_id] = item

    def salvar(self):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        dados = {"itens": list(self.itens.values())}
        temporario = self.caminho.with_suffix(".tmp")

        with temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            arquivo.write("\n")

        temporario.replace(self.caminho)

    def listar(self):
        return sorted(self.itens.values(), key=lambda item: item["nome"].lower())

    def obter(self, item_id):
        return self.itens.get(item_id)

    def listar_por_categoria(self, categoria):
        return [
            item for item in self.listar()
            if item["categoria"] == categoria
        ]

    def cadastrar(self, dados):
        item = self._normalizar(dados)
        self._validar(item)

        if item["id"] in self.itens:
            raise ValueError(f"Já existe um item com ID '{item['id']}'.")

        self.itens[item["id"]] = item
        self.salvar()
        return item

    def atualizar(self, item_id_original, dados):
        if item_id_original not in self.itens:
            raise ValueError("O item selecionado não existe.")

        item = self._normalizar(dados)
        self._validar(item)

        novo_id = item["id"]
        if novo_id != item_id_original and novo_id in self.itens:
            raise ValueError(f"Já existe um item com ID '{novo_id}'.")

        # Atualiza a chave caso o ID tenha mudado.
        itens_novos = {}
        for chave, valor in self.itens.items():
            if chave == item_id_original:
                itens_novos[novo_id] = item
            else:
                itens_novos[chave] = valor

        self.itens = itens_novos
        self.salvar()
        return item

    def excluir(self, item_id):
        if item_id not in self.itens:
            raise ValueError("O item selecionado não existe.")

        del self.itens[item_id]
        self.salvar()

    @staticmethod
    def _normalizar(dados):
        item = dict(dados)
        item["id"] = str(item.get("id", "")).strip().lower()
        item["nome"] = str(item.get("nome", "")).strip()
        item["categoria"] = str(item.get("categoria", "")).strip().lower()

        try:
            item["peso"] = float(item.get("peso", 0))
            item["preco_base"] = float(item.get("preco_base", 0))
            item["tempo_coleta"] = float(item.get("tempo_coleta", 2))
            item["cor"] = [int(c) for c in item.get("cor", [150, 150, 150])]
        except (TypeError, ValueError) as erro:
            raise ValueError("Peso, preço, tempo e cor precisam ser números.") from erro

        item["solido"] = bool(item.get("solido", True))
        item["respawn"] = bool(item.get("respawn", True))
        return item

    @staticmethod
    def _validar(item):
        if not re.fullmatch(r"[a-z0-9_-]+", item.get("id", "")):
            raise ValueError(
                "O ID deve usar apenas letras minúsculas, números, hífen ou underline."
            )

        if not item.get("nome"):
            raise ValueError("Informe o nome de exibição.")

        if item.get("categoria") not in CATEGORIAS_VALIDAS:
            raise ValueError(
                "Categoria inválida. Use: minerio, planta, material ou item."
            )

        if item.get("peso", -1) < 0:
            raise ValueError("O peso não pode ser negativo.")

        if item.get("preco_base", -1) < 0:
            raise ValueError("O preço base não pode ser negativo.")

        if item.get("tempo_coleta", 0) <= 0:
            raise ValueError("O tempo de coleta deve ser maior que zero.")

        cor = item.get("cor")
        if not isinstance(cor, list) or len(cor) != 3:
            raise ValueError("A cor precisa ter três valores RGB.")

        if any(c < 0 or c > 255 for c in cor):
            raise ValueError("Cada componente RGB deve estar entre 0 e 255.")
