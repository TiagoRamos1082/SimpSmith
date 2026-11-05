from sistemas.catalogo_itens import CatalogoItens


class Inventario:
    PESO_MAXIMO = 50.0
    LIMITE_PILHA = 16

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

        peso_unitario = float(item.get("peso", 0))

        if peso_unitario < 0:
            return False

        quantidade_restante = quantidade

        # Calcula quantas unidades ainda cabem pelo peso.
        if peso_unitario > 0:
            peso_disponivel = max(
                0,
                self.PESO_MAXIMO - self.peso_total
            )

            limite_peso = int(
                (peso_disponivel + 1e-9) / peso_unitario
            )

            quantidade_restante = min(
                quantidade_restante,
                limite_peso
            )

        if quantidade_restante <= 0:
            return False

        # Primeiro, completa pilhas existentes.
        for slot in self.slots:
            if (
                slot is not None
                and slot["tipo"] == tipo
                and quantidade_restante > 0
            ):
                espaco = self.LIMITE_PILHA - slot["quantidade"]
                adicionar = min(espaco, quantidade_restante)

                if adicionar > 0:
                    slot["quantidade"] += adicionar
                    quantidade_restante -= adicionar

        # Depois, ocupa slots vazios.
        for indice, slot in enumerate(self.slots):
            if slot is None and quantidade_restante > 0:
                adicionar = min(
                    self.LIMITE_PILHA,
                    quantidade_restante
                )

                self.slots[indice] = {
                    "tipo": tipo,
                    "quantidade": adicionar,
                }

                quantidade_restante -= adicionar

        return quantidade_restante < quantidade

    
    def quantidade_disponivel(self, tipo):
        quantidade_total = 0

        for slot in self.slots:
            if slot is not None and slot["tipo"] == tipo:
                quantidade_total += slot["quantidade"]

        return quantidade_total

    def remover(self, tipo, quantidade=1):
        if (
            not isinstance(quantidade, int)
            or isinstance(quantidade, bool)
            or quantidade <= 0
        ):
            return False

        if self.quantidade_disponivel(tipo) < quantidade:
            return False

        quantidade_restante = quantidade

        for indice, slot in enumerate(self.slots):
            if slot is None or slot["tipo"] != tipo:
                continue

            remover = min(
                slot["quantidade"],
                quantidade_restante
            )

            slot["quantidade"] -= remover
            quantidade_restante -= remover

            if slot["quantidade"] == 0:
                self.slots[indice] = None

            if quantidade_restante == 0:
                break

        return True



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
