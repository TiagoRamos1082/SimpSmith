import pygame

from sistemas.catalogo_itens import CatalogoItens
from sistemas.carregador_imagens import obter_imagem


CATEGORIAS_RECURSOS = {"minerio"}


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
        self.imagem = item.get("imagem")
        self.tamanho = tamanho

        self.largura_visual = item["largura_visual"]
        self.altura_visual = item["altura_visual"]

        self.colisao_ativa = bool(
            item.get("colisao_ativa", item.get("solido", True))
        )
        self.interacao_ativa = bool(
            item.get("interacao_ativa", True)
        )

        # Compatibilidade com o sistema de colisão existente.
        self.solido = self.colisao_ativa

        self.rect = pygame.Rect(x, y, tamanho, tamanho)

        # A origem visual é centralizada no ponto de posicionamento.
        self.area_visual = pygame.Rect(
            0, 0, self.largura_visual, self.altura_visual
        )
        self.area_visual.center = self.rect.center

        # Todos os retângulos pertencem à mesma geometria.
        # O campo legado "ativa" não controla mais cada retângulo.
        self.geometria = []

        for dados in item.get("colisao", []):
            self.geometria.append(
                pygame.Rect(
                    self.area_visual.left + dados["x"],
                    self.area_visual.top + dados["y"],
                    dados["largura"],
                    dados["altura"],
                )
            )

        self.colisoes = (
            [area.copy() for area in self.geometria]
            if self.colisao_ativa else []
        )

        self.areas_interacao = (
            [area.copy() for area in self.geometria]
            if self.interacao_ativa else []
        )

    def desenhar(self, tela, camera=None):
        if camera is None:
            rect_tela = self.rect
        else:
            rect_tela = camera.aplicar_rect(self.rect)

        area_visual = pygame.Rect(
            0,
            0,
            self.largura_visual,
            self.altura_visual
        )
        area_visual.center = rect_tela.center

        imagem = obter_imagem(
            self.imagem,
            (self.largura_visual, self.altura_visual)
        )

        if imagem is not None:
            area_imagem = imagem.get_rect(center=area_visual.center)
            tela.blit(imagem, area_imagem)
            return

        pygame.draw.rect(tela, self.cor, area_visual)
        pygame.draw.rect(
            tela,
            (30, 30, 30),
            area_visual,
            2
        )
