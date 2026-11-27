
import pygame

from sistemas.catalogo_receitas import CatalogoReceitas


class Crafting:
    def __init__(self, mapa, inventario=None, catalogo=None):
        self.mapa = mapa
        self.inventario = inventario
        self.catalogo = catalogo or CatalogoReceitas()

        self.area_atual = None
        self.aberto = False

    def atualizar(self, jogador):
        hitbox = getattr(
            jogador, "rect_colisao", jogador.rect
        )

        self.area_atual = self.mapa.obter_area_interacao(
            hitbox
        )

    def tratar_evento(self, evento, interface):
        if evento.type != pygame.KEYDOWN:
            return

        # Enquanto a interface estiver aberta,
        # os eventos são encaminhados para ela.
        if self.aberto:
            interface.tratar_evento(evento, self)
            self.aberto = interface.aberto
            return

        # Abre a fornalha ao pressionar E.
        if (
            evento.key == pygame.K_e
            and self.area_atual is not None
            and self.area_atual["tipo"] == "bigorna"
        ):
            receitas = self.catalogo.listar_por_estacao(
                "bigorna"
            )

            interface.configurar_receitas(
                receitas,
                estacao="bigorna",
                inventario=self.inventario
            )
            interface.alternar()
            self.aberto = interface.aberto

    def fabricar(self, receita_id, quantidade=1):
        if self.inventario is None:
            return False

        if (
            not isinstance(quantidade, int)
            or isinstance(quantidade, bool)
            or quantidade <= 0
        ):
            return False

        receita = self.catalogo.obter(receita_id)

        if receita is None:
            return False

        ingredientes = receita["ingredientes"]
        resultado = receita["resultado"]

        # Confere todos os ingredientes antes de alterar o inventário.
        for item_id, quantidade_item in ingredientes.items():
            necessario = quantidade_item * quantidade

            if self.inventario.quantidade_disponivel(item_id) < necessario:
                return False

        # Snapshot para reverter qualquer falha, inclusive adição parcial.
        slots_originais = [
            slot.copy() if slot is not None else None
            for slot in self.inventario.slots
        ]

        for item_id, quantidade_item in ingredientes.items():
            sucesso = self.inventario.remover(
                item_id,
                quantidade_item * quantidade
            )

            if not sucesso:
                self.inventario.slots = slots_originais
                return False

        for item_id, quantidade_item in resultado.items():
            quantidade_adicionar = quantidade_item * quantidade
            quantidade_antes = (
                self.inventario.quantidade_disponivel(item_id)
            )

            self.inventario.adicionar(
                item_id,
                quantidade_adicionar
            )

            quantidade_depois = (
                self.inventario.quantidade_disponivel(item_id)
            )

            adicionada = quantidade_depois - quantidade_antes

            if adicionada != quantidade_adicionar:
                self.inventario.slots = slots_originais
                return False

        return True
