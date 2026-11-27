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
        self.solido = bool(
            item.get("colisao_ativa", item.get("solido", True))
        )
        self.interacao_ativa = bool(item.get("interacao_ativa", True))

        # x e y representam o canto superior esquerdo da imagem.
        self.area_visual = pygame.Rect(
            self.x, self.y,
            self.largura_visual, self.altura_visual
        )
        self.rect = self.area_visual.copy()

        # Uma única geometria atende colisão física e interação.
        # Se houver configuração antiga sem "colisao", usa "interacao"
        # como compatibilidade para não perder áreas já cadastradas.
        geometria = item.get("colisao") or item.get("interacao", [])

        # Cada retângulo pertence à mesma geometria lógica.
        # Os estados são globais: não há ativação por retângulo.
        self.geometria = []

        for dados in geometria:
            area = pygame.Rect(
                self.area_visual.x + dados["x"],
                self.area_visual.y + dados["y"],
                dados["largura"],
                dados["altura"],
            )
            self.geometria.append(area)

        self.colisoes = (
            [area.copy() for area in self.geometria]
            if self.solido else []
        )

        self.areas_interacao = (
            [area.copy() for area in self.geometria]
            if self.interacao_ativa else []
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
