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

        self.solido = bool(item.get("solido", True))
        self.rect = pygame.Rect(x, y, tamanho, tamanho)

        # Origem da imagem, centralizada no retângulo de posicionamento.
        area_visual = pygame.Rect(
            0, 0, self.largura_visual, self.altura_visual
        )
        area_visual.center = self.rect.center

        # A geometria de colisao tambem define a area de interacao.
        # Retangulos inativos continuam interativos, mas nao bloqueiam
        # fisicamente o jogador.
        self.colisoes = []
        self.areas_interacao = []

        for dados_retangulo in item.get("colisao", []):
            retangulo = pygame.Rect(
                area_visual.left + dados_retangulo["x"],
                area_visual.top + dados_retangulo["y"],
                dados_retangulo["largura"],
                dados_retangulo["altura"]
            )

            self.areas_interacao.append(retangulo)

            if self.solido and dados_retangulo.get("ativa", True):
                self.colisoes.append(retangulo.copy())

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
