
import pygame


class Crafting:
    def __init__(self, mapa):
        self.mapa = mapa
        self.area_atual = None
        self.aberto = False

    def atualizar(self, jogador):
        self.area_atual = self.mapa.obter_area_interacao(
            jogador.rect
        )

    def tratar_evento(self, evento, interface):
        if evento.type != pygame.KEYDOWN:
            return

        if (
            evento.key == pygame.K_e
            and self.area_atual is not None
            and self.area_atual["tipo"] == "crafting"
        ):
            interface.alternar()
            self.aberto = interface.aberto

        elif evento.key == pygame.K_ESCAPE and self.aberto:
            interface.aberto = False
            self.aberto = False
