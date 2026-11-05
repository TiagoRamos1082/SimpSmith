
import pygame


class Tile:
    def __init__(self, identificador, cor, solido=False):
        self.identificador = identificador
        self.cor = tuple(cor)
        self.solido = solido

    def desenhar(self, tela, x, y, tamanho):
        pygame.draw.rect(
            tela,
            self.cor,
            (x, y, tamanho, tamanho)
        )
