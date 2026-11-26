from pathlib import Path

import pygame


class RenderizadorMapa:
    CATEGORIAS_AMPLIADAS = (
        "arvores/",
        "casas/",
        "cercas/",
        "outras_estruturas/",
    )

    def __init__(self, raiz, dados):
        self.raiz = Path(raiz)
        self.dados = dados

        self.camadas = list(dados["camadas"].keys())
        self.tiles = dados["tiles"]
        self.tile_size = dados["tile_size"]

        sprites_json = dados.get("sprites_por_camada", {})
        sprites_legados = dados.get("sprites_superiores", [])

        self.sprites_por_camada = {}

        for camada in self.camadas:
            sprites = sprites_json.get(camada)

            if sprites is None:
                sprites = (
                    sprites_legados
                    if camada == "superior"
                    else []
                )

            self.sprites_por_camada[camada] = sprites

        self.imagens_por_camada = {}
        self.imagens_redimensionadas = {}
        self.tamanhos_sprites = dados.get("tamanhos_sprites", {})

        self.carregar_sprites()

    def carregar_sprites(self):
        pasta_base = self.raiz / "assets" / "tiles"

        for camada in self.camadas:
            pasta = pasta_base / camada
            biblioteca = {}

            if pasta.is_dir():
                for caminho in pasta.rglob("*.png"):
                    identificador = (
                        caminho.relative_to(pasta)
                        .with_suffix("")
                        .as_posix()
                    )

                    imagem = pygame.image.load(
                        str(caminho)
                    ).convert_alpha()

                    biblioteca[identificador] = imagem

            self.imagens_por_camada[camada] = biblioteca

    def obter_sprites_camada(self, camada):
        return self.sprites_por_camada.get(camada, [])

    def desenhar_tiles_camada(self, tela, camada, camera=None):
        matriz = self.dados["camadas"][camada]

        for y, linha in enumerate(matriz):
            for x, identificador in enumerate(linha):
                if identificador is None:
                    continue

                informacoes = self.tiles.get(identificador)

                if informacoes is None:
                    continue

                rect = pygame.Rect(
                    x * self.tile_size,
                    y * self.tile_size,
                    self.tile_size,
                    self.tile_size,
                )

                if camera is not None:
                    rect = camera.aplicar_rect(rect)

                if tela.get_rect().colliderect(rect):
                    pygame.draw.rect(
                        tela,
                        tuple(informacoes["cor"]),
                        rect,
                    )

    def desenhar_chao_base(self, tela, camera=None):
        identificador = self.dados.get("chao_base")

        if not identificador:
            return

        biblioteca = self.imagens_por_camada.get("terreno", {})
        imagem = biblioteca.get(identificador)

        if imagem is None:
            return

        escala = 2.0
        chave = ("chao_base", identificador, escala)

        imagem_tela = self.imagens_redimensionadas.get(chave)

        if imagem_tela is None:
            tamanho = (
                round(imagem.get_width() * escala),
                round(imagem.get_height() * escala),
            )
            imagem_tela = pygame.transform.scale(imagem, tamanho)
            self.imagens_redimensionadas[chave] = imagem_tela

        rect_mapa = pygame.Rect(
            0, 0,
            self.dados["largura"] * self.tile_size,
            self.dados["altura"] * self.tile_size,
        )

        if camera is not None:
            rect_mapa = camera.aplicar_rect(rect_mapa)

        area_visivel = rect_mapa.clip(tela.get_rect())

        if area_visivel.width <= 0 or area_visivel.height <= 0:
            return

        clip_anterior = tela.get_clip()
        tela.set_clip(area_visivel)

        largura, altura = imagem_tela.get_size()

        for y in range(rect_mapa.top, rect_mapa.bottom, altura):
            for x in range(rect_mapa.left, rect_mapa.right, largura):
                tela.blit(imagem_tela, (x, y))

        tela.set_clip(clip_anterior)

    def desenhar_tiles(self, tela, camera=None):
        self.desenhar_chao_base(tela, camera)
        for camada in self.camadas:
            self.desenhar_tiles_camada(
                tela, camada, camera
            )

    def desenhar_sprites_camada(self, tela, camada, camera=None):
        biblioteca = self.imagens_por_camada.get(camada, {})

        for sprite in self.obter_sprites_camada(camada):
            identificador = sprite.get("id")

            if not identificador:
                continue

            imagem = biblioteca.get(identificador)
            if imagem is None:
                continue

            escala = 2.0
            configuracao = self.tamanhos_sprites.get(
                camada, {}
            ).get(identificador, {})

            largura_base = max(
                1, int(configuracao.get("largura", imagem.get_width()))
            )
            altura_base = max(
                1, int(configuracao.get("altura", imagem.get_height()))
            )

            tamanho = (
                max(1, round(largura_base * escala)),
                max(1, round(altura_base * escala)),
            )

            if tamanho == imagem.get_size():
                imagem_tela = imagem
            else:
                chave = (
                    camada, identificador,
                    largura_base, altura_base, escala
                )
                imagem_tela = self.imagens_redimensionadas.get(chave)

                if imagem_tela is None:
                    imagem_tela = pygame.transform.scale(
                        imagem, tamanho
                    )
                    self.imagens_redimensionadas[chave] = imagem_tela

            posicao = (sprite["x"], sprite["y"])

            if camera is not None:
                posicao = camera.aplicar(posicao)

            rect = imagem_tela.get_rect(topleft=posicao)

            if tela.get_rect().colliderect(rect):
                tela.blit(imagem_tela, posicao)


    def desenhar(self, tela, camera=None):
        self.desenhar_chao_base(tela, camera)

        for camada in self.camadas:
            self.desenhar_tiles_camada(
                tela, camada, camera
            )

            self.desenhar_sprites_camada(
                tela, camada, camera
            )
