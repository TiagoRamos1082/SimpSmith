
import json
import os
import pygame


class Mapa:
    MOSTRAR_BORDAS = True

    COR_OBSTACULO = (255, 40, 40)
    ESPESSURA_BORDA = 2

    def __init__(self):
        raiz = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        caminho_imagem = os.path.join(
            raiz, "assets", "mapa", "mapaPrincipal.png"
        )

        caminho_colisoes = os.path.join(
            raiz, "mapa", "colisoes.json"
        )

        self.imagem_original = pygame.image.load(
            caminho_imagem
        ).convert()

        self.largura_referencia = self.imagem_original.get_width()
        self.altura_referencia = self.imagem_original.get_height()

        self.obstaculos = []
        self.areas_interacao = []

        if os.path.isfile(caminho_colisoes):
            with open(caminho_colisoes, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)

            self.obstaculos = [
                pygame.Rect(
                    item["x"],
                    item["y"],
                    item["largura"],
                    item["altura"]
                )
                for item in dados.get("obstaculos", [])
            ]

            self.areas_interacao = [
                {
                    "id": item["id"],
                    "tipo": item["tipo"],
                    "rect": pygame.Rect(
                        item["x"],
                        item["y"],
                        item["largura"],
                        item["altura"]
                    )
                }
                for item in dados.get("areas_interacao", [])
            ]

    def obter_area_interacao(self, rect):
        tela = pygame.display.get_surface()

        if tela is None:
            return None

        sx, sy = self._escala(tela)

        for area in self.areas_interacao:
            area_tela = self._escalar_rect(
                area["rect"], sx, sy
            )

            if rect.colliderect(area_tela):
                return area

        return None

    def _escala(self, tela):
        largura, altura = tela.get_size()

        return (
            largura / self.largura_referencia,
            altura / self.altura_referencia
        )

    def _escalar_rect(self, rect, sx, sy):
        return pygame.Rect(
            round(rect.x * sx),
            round(rect.y * sy),
            round(rect.width * sx),
            round(rect.height * sy)
        )

    def desenhar(self, tela):
        largura, altura = tela.get_size()

        imagem = pygame.transform.scale(
            self.imagem_original,
            (largura, altura)
        )

        tela.blit(imagem, (0, 0))

    def colide_com_obstaculo(self, rect):
        tela = pygame.display.get_surface()

        if tela is None:
            return True

        largura, altura = tela.get_size()

        if (
            rect.left < 0
            or rect.top < 0
            or rect.right > largura
            or rect.bottom > altura
        ):
            return True

        sx, sy = self._escala(tela)

        for obstaculo in self.obstaculos:
            obstaculo_tela = self._escalar_rect(obstaculo, sx, sy)

            if rect.colliderect(obstaculo_tela):
                return True

        return False
