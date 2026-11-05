
import json
from pathlib import Path

import pygame


class Mapa:
    MOSTRAR_BORDAS = True

    COR_OBSTACULO = (255, 40, 40)
    ESPESSURA_BORDA = 2
    COR_FUNDO = (35, 35, 40)

    def __init__(self):
        self.raiz = Path(__file__).resolve().parents[1]

        self.caminho_mapa = (
            self.raiz / "dados" / "mapas" / "mapa_principal.json"
        )

        self.caminho_sprites = (
            self.raiz / "assets" / "tiles" / "superior"
        )

        self.caminho_colisoes = (
            self.raiz / "mapa" / "colisoes.json"
        )

        self.carregar_mapa()
        self.carregar_sprites()
        self.carregar_colisoes()

    def carregar_mapa(self):
        with self.caminho_mapa.open(
            "r", encoding="utf-8-sig"
        ) as arquivo:
            self.dados = json.load(arquivo)

        self.largura = self.dados["largura"]
        self.altura = self.dados["altura"]
        self.tile_size = self.dados["tile_size"]

        self.largura_referencia = self.largura * self.tile_size
        self.altura_referencia = self.altura * self.tile_size

        self.camadas = list(self.dados["camadas"].keys())
        self.tiles = self.dados["tiles"]

        self.spawn_jogador = self.dados.get(
            "spawn_jogador",
            {"x": 550, "y": 500, "direcao": "down"}
        )

        self.sprites_superiores = self.dados.get(
            "sprites_superiores", []
        )

    def carregar_sprites(self):
        self.sprites = {}

        for caminho in self.caminho_sprites.rglob("*.png"):
            identificador = (
                caminho.relative_to(self.caminho_sprites)
                .with_suffix("")
                .as_posix()
            )

            imagem = pygame.image.load(
                str(caminho)
            ).convert_alpha()

            self.sprites[identificador] = imagem

    def carregar_colisoes(self):
        self.obstaculos = []
        self.areas_interacao = []

        if not self.caminho_colisoes.is_file():
            return

        with self.caminho_colisoes.open(
            "r", encoding="utf-8"
        ) as arquivo:
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

    def desenhar_camadas(self, tela):
        sx, sy = self._escala(tela)

        tamanho_x = round(self.tile_size * sx)
        tamanho_y = round(self.tile_size * sy)

        for nome_camada in self.camadas:
            camada = self.dados["camadas"][nome_camada]

            for y in range(self.altura):
                for x in range(self.largura):
                    identificador = camada[y][x]

                    if identificador is None:
                        continue

                    informacoes = self.tiles.get(identificador)

                    if informacoes is None:
                        continue

                    rect = pygame.Rect(
                        round(x * self.tile_size * sx),
                        round(y * self.tile_size * sy),
                        tamanho_x,
                        tamanho_y
                    )

                    pygame.draw.rect(
                        tela,
                        tuple(informacoes["cor"]),
                        rect
                    )

    def desenhar_sprites_superiores(self, tela):
        sx, sy = self._escala(tela)

        for sprite in self.sprites_superiores:
            identificador = sprite["id"]

            imagem = self.sprites.get(identificador)

            if imagem is None:
                continue

            largura = max(
                1, round(imagem.get_width() * sx)
            )

            altura = max(
                1, round(imagem.get_height() * sy)
            )

            imagem_redimensionada = pygame.transform.scale(
                imagem,
                (largura, altura)
            )

            x = round(sprite["x"] * sx)
            y = round(sprite["y"] * sy)

            tela.blit(imagem_redimensionada, (x, y))

    def desenhar(self, tela):
        tela.fill(self.COR_FUNDO)

        self.desenhar_camadas(tela)
        self.desenhar_sprites_superiores(tela)

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
            obstaculo_tela = self._escalar_rect(
                obstaculo, sx, sy
            )

            if rect.colliderect(obstaculo_tela):
                return True

        return False
