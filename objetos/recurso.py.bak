import pygame
from sistemas.catalogo_itens import CatalogoItens


CATEGORIAS_RECURSOS = {"minerio", "planta"}


class Recurso:
    def __init__(self, x, y, tipo, tamanho=32, catalogo=None):
        self.catalogo = catalogo or CatalogoItens()
        item = self.catalogo.obter(tipo)

        if item is None or item["categoria"] not in CATEGORIAS_RECURSOS:
            raise ValueError(
                f"Recurso inválido ou não cadastrado: {tipo}"
            )

        self.x = x
        self.y = y
        self.tipo = tipo
        self.categoria = item["categoria"]
        self.nome = item["nome"]
        self.cor = tuple(item["cor"])
        self.tamanho = tamanho
        self.solido = bool(item.get("solido", True))
        self.rect = pygame.Rect(x, y, tamanho, tamanho)

    def desenhar(self, tela):
        pygame.draw.rect(tela, self.cor, self.rect)
        pygame.draw.rect(tela, (30, 30, 30), self.rect, 2)
