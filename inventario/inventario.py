from sistemas.catalogo_itens import CatalogoItens


class Inventario:
    PESO_MAXIMO = 50.0

    def __init__(self, quantidade_slots, catalogo=None):
        self.catalogo = catalogo or CatalogoItens()
        self.slots = [None] * quantidade_slots

    def _dados_item(self, tipo):
        return self.catalogo.obter(tipo)

    @property
    def peso_total(self):   
        peso = 0.0
        for slot in self.slots:
            if slot is not None:
                item = self._dados_item(slot["tipo"])
                if item is not None:
                    peso += float(item.get("peso", 0)) * slot["quantidade"]
        return peso

    @property
    def sobrecarregado(self):
        return self.peso_total > self.PESO_MAXIMO

    def adicionar(self, tipo, quantidade=1):
        item = self._dados_item(tipo)
        if item is None or quantidade <= 0:
            return False

        # Primeiro, tenta acumular em uma pilha existente.
        for slot in self.slots:
            if slot is not None and slot["tipo"] == tipo:
                slot["quantidade"] += quantidade
                return True

        # Se não existir pilha, procura um slot vazio.
        for indice, slot in enumerate(self.slots):
            if slot is None:
                self.slots[indice] = {
                    "tipo": tipo,
                    "quantidade": quantidade,
                }
                return True

        return False

    def mover(self, origem, destino):
        if origem == destino:
            return
        if not (0 <= origem < len(self.slots)):
            return
        if not (0 <= destino < len(self.slots)):
            return

        item_origem = self.slots[origem]
        item_destino = self.slots[destino]
        if item_origem is None:
            return

        if item_destino is not None and item_origem["tipo"] == item_destino["tipo"]:
            item_destino["quantidade"] += item_origem["quantidade"]
            self.slots[origem] = None
            return

        self.slots[origem], self.slots[destino] = (
            self.slots[destino],
            self.slots[origem],
        )

    def descartar(self, indice, quantidade=None):
        if not (0 <= indice < len(self.slots)):
            return False

        item = self.slots[indice]

        if item is None:
            return False

        if quantidade is None:
            quantidade = item["quantidade"]

        if quantidade <= 0 or quantidade > item["quantidade"]:
            return False

        item["quantidade"] -= quantidade

        if item["quantidade"] == 0:
            self.slots[indice] = None

        return True
