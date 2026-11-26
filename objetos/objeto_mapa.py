import pygame

from sistemas.catalogo_itens import CatalogoItens
from sistemas.carregador_imagens import obter_imagem


CATEGORIAS_POSICIONAVEIS = {"item", "construcao"}


class ObjetoMapa:
    def __init__(self, x, y, tipo, catalogo=None):
        self.catalogo = catalogo or CatalogoItens()
        item = self.catalogo.obter(tipo)

        if item is None or item["categoria"] not in CATEGORIAS_POSICIONAVEIS:
            raise ValueError(f"Objeto de mapa inválido: {tipo}")

        if not item.get("imagem"):
            raise ValueError(f"O objeto '{tipo}' não possui imagem.")

        self.x = int(x)
        self.y = int(y)
        self.tipo = tipo
        self.nome = item["nome"]
        self.imagem = item["imagem"]
        self.cor = tuple(item["cor"])

        self.largura_visual = item["largura_visual"]
        self.altura_visual = item["altura_visual"]
        self.solido = bool(item.get("solido", True))

        # x e y representam o canto superior esquerdo da imagem.
        self.area_visual = pygame.Rect(
            self.x, self.y,
            self.largura_visual, self.altura_visual
        )
        self.rect = self.area_visual.copy()

        self.colisoes = []
        self.areas_interacao = []

        for dados in item.get("colisao", []):
            area = pygame.Rect(
                self.area_visual.x + dados["x"],
                self.area_visual.y + dados["y"],
                dados["largura"],
                dados["altura"],
            )

            if self.solido and dados.get("ativa", True):
                self.colisoes.append(area.copy())

        for dados in item.get("interacao", []):
            self.areas_interacao.append(
                pygame.Rect(
                    self.area_visual.x + dados["x"],
                    self.area_visual.y + dados["y"],
                    dados["largura"],
                    dados["altura"],
                )
            )

    def desenhar(self, tela, camera=None):
        area = self.area_visual

        if camera is not None:
            area = camera.aplicar_rect(area)

        imagem = obter_imagem(
            self.imagem,
            (self.largura_visual, self.altura_visual),
        )

        if imagem is not None:
            tela.blit(imagem, area)
        else:
            pygame.draw.rect(tela, self.cor, area)
