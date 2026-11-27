
import json
from pathlib import Path

import pygame

from mapa.renderizador_mapa import RenderizadorMapa
from objetos.objeto_mapa import ObjetoMapa
from sistemas.catalogo_itens import CatalogoItens


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

        self.caminho_colisoes_sprites = (
            self.raiz / "mapa" / "colisoes_sprites.json"
        )

        self.carregar_mapa()
        self.carregar_sprites()
        self.carregar_objetos()
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
        self.renderizador = RenderizadorMapa(
            self.raiz, self.dados
        )

        self.sprites_por_camada = (
            self.renderizador.sprites_por_camada
        )

        self.sprites = (
            self.renderizador.imagens_por_camada.get(
                "superior", {}
            )
        )

        self.sprites_superiores = (
            self.sprites_por_camada.get("superior", [])
        )

    def carregar_objetos(self):
        caminho = self.raiz / "mapa" / "objetos_mapa.json"
        self.objetos = []
        self.areas_interacao_objetos = []

        if not caminho.is_file():
            return

        with caminho.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        catalogo = CatalogoItens()

        for registro in dados.get("objetos", []):
            objeto = ObjetoMapa(
                registro["x"],
                registro["y"],
                registro["id"],
                catalogo,
            )
            self.objetos.append(objeto)

            for area in objeto.areas_interacao:
                self.areas_interacao_objetos.append({
                    "id": objeto.tipo,
                    "tipo": objeto.tipo,
                    "rect": area.copy(),
                })

    def desenhar_objetos(self, tela, camera=None):
        for objeto in self.objetos:
            objeto.desenhar(tela, camera)

    def carregar_colisoes(self):
        self.obstaculos = []
        self.areas_interacao = []
        self.obstaculos_sprites = []

        # Colisoes convencionais do mapa.
        if self.caminho_colisoes.is_file():
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

        # Colisoes definidas pelo editor de sprites.
        if not self.caminho_colisoes_sprites.is_file():
            return

        with self.caminho_colisoes_sprites.open(
            "r", encoding="utf-8"
        ) as arquivo:
            dados_sprites = json.load(arquivo)

        if dados_sprites.get("mapa") != self.caminho_mapa.stem:
            print("Aviso: colisoes de sprites pertencem a outro mapa.")
            return

        colisoes_por_id = dados_sprites.get("sprites", {})
        escala = 2.0

        for camada, instancias in self.sprites_por_camada.items():
            for instancia in instancias:
                identificador = instancia.get("id")

                if not identificador:
                    continue

                colisoes = colisoes_por_id.get(identificador, [])

                for item in colisoes:
                    self.obstaculos_sprites.append(
                        pygame.Rect(
                            instancia["x"] + item["x"] * escala,
                            instancia["y"] + item["y"] * escala,
                            item["largura"] * escala,
                            item["altura"] * escala
                        )
                    )

        print(
            f"Colisoes de sprites carregadas: "
            f"{len(self.obstaculos_sprites)}"
        )

    def obter_area_interacao(self, rect):
        # Áreas tradicionais configuradas no mapa.
        for area in self.areas_interacao:
            if rect.colliderect(area["rect"]):
                return area

        # Áreas das construções cadastradas no NGC.
        for area in self.areas_interacao_objetos:
            if rect.colliderect(area["rect"]):
                return area

        return None

    def desenhar_camadas(self, tela, camera=None):
        self.renderizador.desenhar_tiles(tela, camera)

    def desenhar_sprites_superiores(self, tela, camera=None):
        self.renderizador.desenhar_sprites_camada(
            tela, "superior", camera
        )

    def desenhar(self, tela, camera=None):
        tela.fill(self.COR_FUNDO)
        self.renderizador.desenhar(tela, camera)
        self.desenhar_objetos(tela, camera)

    def colide_com_obstaculo(self, rect):
        if (
            rect.left < 0
            or rect.top < 0
            or rect.right > self.largura_referencia
            or rect.bottom > self.altura_referencia
        ):
            return True

        for obstaculo in self.obstaculos:
            if rect.colliderect(obstaculo):
                return True

        for obstaculo in self.obstaculos_sprites:
            if rect.colliderect(obstaculo):
                return True

        for objeto in self.objetos:
            if not objeto.solido:
                continue

            if any(
                rect.colliderect(colisao)
                for colisao in objeto.colisoes
            ):
                return True

        return False
