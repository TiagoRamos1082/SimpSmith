
import pygame


class Objeto:
    def __init__(self, x, y, tamanho=32, solido=True):
        self.x = x
        self.y = y
        self.tamanho = tamanho
        self.solido = solido

        self.rect = pygame.Rect(
            x, y, tamanho, tamanho
        )

    def desenhar(self, tela):
        """Implementado pelas subclasses."""
        pass
