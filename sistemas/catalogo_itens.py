import json
import re
from pathlib import Path


# Caminho baseado na localização deste arquivo, não no diretório do terminal.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_ITENS = RAIZ_PROJETO / "dados" / "itens" / "itens.json"

CATEGORIAS_VALIDAS = {"minerio", "material", "item", "construcao"}


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

        for dados_item in itens:
            item = self._normalizar(dados_item)
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

        # Mescla os novos dados com o registro existente.
        # Campos que o editor não controla permanecem preservados.
        dados_completos = dict(self.itens[item_id_original])
        dados_completos.update(dados)

        item = self._normalizar(dados_completos)
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
    def _normalizar_retangulo(dados, padrao, permitir_ativa=False):
        if dados is None:
            dados = {}

        if not isinstance(dados, dict):
            raise ValueError("A configuração do retângulo precisa ser um objeto.")

        resultado = {}

        for campo in ("x", "y", "largura", "altura"):
            valor = dados.get(campo, padrao[campo])

            try:
                numero = float(valor)
                if not numero.is_integer():
                    raise ValueError
                resultado[campo] = int(numero)
            except (TypeError, ValueError):
                raise ValueError(
                    f"O campo '{campo}' do retângulo precisa ser inteiro."
                )

        if permitir_ativa:
            ativa = dados.get("ativa", padrao["ativa"])

            if not isinstance(ativa, bool):
                raise ValueError(
                    "O campo 'ativa' da colisão precisa ser booleano."
                )

            resultado["ativa"] = ativa

        return resultado

    @staticmethod
    def _normalizar_lista_retangulos(dados, padrao, permitir_ativa=False):
        """
        Aceita o formato antigo (um dicionario) e o novo (lista).
        O formato antigo e convertido em uma lista com um elemento.
        """

        if dados is None:
            dados = [dict(padrao)]

        elif isinstance(dados, dict):
            dados = [dados]

        if not isinstance(dados, list):
            raise ValueError(
                "A configuracao precisa ser uma lista de retangulos."
            )

        return [
            CatalogoItens._normalizar_retangulo(
                retangulo,
                padrao,
                permitir_ativa=permitir_ativa
            )
            for retangulo in dados
        ]

    @staticmethod
    def _normalizar(dados):
        item = dict(dados)
        item["id"] = str(item.get("id", "")).strip().lower()
        item["nome"] = str(item.get("nome", "")).strip()
        item["categoria"] = str(item.get("categoria", "")).strip().lower()

        # Compatibilidade com categorias antigas.
        if item["categoria"] in {"recurso", "planta"}:
            item["categoria"] = "minerio"

        if item.get("subtipo") == "planta":
            item.pop("subtipo", None)

        try:
            item["peso"] = float(item.get("peso", 0))
            item["preco_base"] = float(item.get("preco_base", 0))
            item["tempo_coleta"] = float(item.get("tempo_coleta", 2))
            item["cor"] = [int(c) for c in item.get("cor", [150, 150, 150])]

            for campo in ("largura_visual", "altura_visual"):
                valor = float(item.get(campo, 32))

                if not valor.is_integer():
                    raise ValueError

                item[campo] = int(valor)
        except (TypeError, ValueError) as erro:
            raise ValueError("Peso, preço, tempo e cor precisam ser números.") from erro

        item["solido"] = bool(item.get("solido", True))
        item["colisao_ativa"] = bool(
            item.get("colisao_ativa", item["solido"])
        )
        item["interacao_ativa"] = bool(
            item.get("interacao_ativa", True)
        )
        item["solido"] = item["colisao_ativa"]
        item["respawn"] = bool(item.get("respawn", True))

        # Interação e colisão compartilham a mesma geometria.
        # Migra dados antigos de interação quando não há colisões.
        geometria_antiga = (
            item["colisao"]
            if "colisao" in item
            else item.get("interacao")
        )

        item.pop("interagivel", None)
        item.pop("tipo_interacao", None)

        imagem = item.get("imagem")
        item["imagem"] = str(imagem).strip() if imagem else None

        item["colisao"] = CatalogoItens._normalizar_lista_retangulos(
            geometria_antiga,
            {
                "x": 0,
                "y": 0,
                "largura": 32,
                "altura": 32,
                "ativa": item["colisao_ativa"],
            },
            permitir_ativa=True,
        )

        # Mantém compatibilidade com código/editor legado,
        # mas sem permitir uma segunda geometria independente.
        item["interacao"] = [
            dict(retangulo)
            for retangulo in item["colisao"]
        ]

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
                "Categoria inválida. Use: minerio, material, item ou construcao."
            )

        if item.get("peso", -1) < 0:
            raise ValueError("O peso não pode ser negativo.")

        if item.get("preco_base", -1) < 0:
            raise ValueError("O preço base não pode ser negativo.")

        for campo, rotulo in (
            ("largura_visual", "largura visual"),
            ("altura_visual", "altura visual"),
        ):
            valor = item.get(campo)

            if not isinstance(valor, int) or valor <= 0:
                raise ValueError(
                    f"A {rotulo} precisa ser um número inteiro maior que zero."
                )

        if item.get("tempo_coleta", 0) <= 0:
            raise ValueError("O tempo de coleta deve ser maior que zero.")

        cor = item.get("cor")
        if not isinstance(cor, list) or len(cor) != 3:
            raise ValueError("A cor precisa ter três valores RGB.")

        if any(c < 0 or c > 255 for c in cor):
            raise ValueError("Cada componente RGB deve estar entre 0 e 255.")

        for nome, retangulos in (
            ("colisao", item.get("colisao")),
            ("interacao", item.get("interacao")),
        ):
            if not isinstance(retangulos, list):
                raise ValueError(f"A configuracao de {nome} precisa ser uma lista.")

            for indice, retangulo in enumerate(retangulos):
                if not isinstance(retangulo, dict):
                    raise ValueError(
                        f"O retangulo {indice + 1} de {nome} e invalido."
                    )

                for campo in ("x", "y", "largura", "altura"):
                    valor = retangulo.get(campo)

                    if not isinstance(valor, int):
                        raise ValueError(
                            f"O campo '{campo}' de {nome} precisa ser inteiro."
                        )

                if retangulo["largura"] <= 0 or retangulo["altura"] <= 0:
                    raise ValueError(
                        f"Largura e altura de {nome} precisam ser maiores que zero."
                    )

                if nome == "colisao" and not isinstance(
                    retangulo.get("ativa"), bool
                ):
                    raise ValueError(
                        "O campo 'ativa' da colisao precisa ser booleano."
                    )

        imagem = item.get("imagem")
        if imagem is not None:
            if not isinstance(imagem, str) or not imagem.strip():
                raise ValueError("O caminho da imagem precisa ser um texto válido.")

            caminho_imagem = Path(imagem)
            if caminho_imagem.is_absolute() or ".." in caminho_imagem.parts:
                raise ValueError("A imagem deve usar um caminho relativo dentro do projeto.")
