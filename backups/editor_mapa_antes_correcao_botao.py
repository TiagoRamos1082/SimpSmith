
import json
import pygame
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]
CAMINHO_MAPA = RAIZ / "dados" / "mapas" / "mapa_principal.json"

TAMANHO_TILE = 32

COR_FUNDO = (35, 35, 40)
COR_PAINEL = (48, 48, 55)
COR_GRADE = (20, 20, 20)
COR_TEXTO = (240, 240, 240)
COR_SELECAO = (255, 210, 50)


class EditorMapa:
    def __init__(self):
        pygame.init()

        info = pygame.display.Info()

        self.largura_janela = min(1200, info.current_w)
        self.altura_janela = min(760, info.current_h)

        self.painel_largura = 320
        self.posicao_mapa_x = 20
        self.posicao_mapa_y = 60

        self.tela_cheia = False
        self.tela = pygame.display.set_mode(
            (self.largura_janela, self.altura_janela),
            pygame.RESIZABLE
        )
        pygame.display.set_caption("SimpSmith - Editor de Mapas")

        self.fonte = pygame.font.Font(None, 25)
        self.fonte_pequena = pygame.font.Font(None, 20)

        self.relogio = pygame.time.Clock()
        self.executando = True

        self.carregar_mapa()
        self.dados.setdefault("sprites_superiores", [])
        self.sprites = {}
        self.carregar_sprites()

        self.escala = max(1, min(
            20,
            (self.largura_janela - self.painel_largura - 50) // self.largura,
            (self.altura_janela - 90) // self.altura
        ))

        self.painel_x = self.largura_janela - self.painel_largura

        self.zoom_minimo = 1
        self.zoom_maximo = 40
        self.arrastando_camera = False
        self.ultima_posicao_camera = None

        self.camadas = list(self.dados["camadas"].keys())
        self.indice_camada = 0

        self.tiles = self.dados["tiles"]
        self.tile_selecionado = next(iter(self.tiles_disponiveis), None)

        self.sprite_selecionado = next(iter(self.sprites), None)
        self.sprite_scroll = 0
        self.painel_scroll = 0
        self.painel_conteudo_altura = 0

        self.modo = "pintura"

        self.salvar_mensagem = ""

    @property
    def camada_atual(self):
        return self.camadas[self.indice_camada]

    @property
    def tiles_disponiveis(self):
        return {
            identificador: informacoes
            for identificador, informacoes in self.tiles.items()
            if informacoes.get("categoria") == self.camada_atual
        }

    def atualizar_camada(self, deslocamento):
        self.indice_camada = (
            self.indice_camada + deslocamento
        ) % len(self.camadas)

        disponiveis = self.tiles_disponiveis

        if self.tile_selecionado not in disponiveis:
            self.tile_selecionado = next(iter(disponiveis), None)

        self.modo = (
            "sprites"
            if self.camada_atual == "superior"
            else "pintura"
        )

    def carregar_mapa(self):
        with CAMINHO_MAPA.open("r", encoding="utf-8-sig") as arquivo:
            self.dados = json.load(arquivo)

        self.largura = self.dados["largura"]
        self.altura = self.dados["altura"]
        self.tile_size = self.dados["tile_size"]

    def carregar_sprites(self):
        pasta = RAIZ / "assets" / "tiles" / "superior"

        for caminho in pasta.rglob("*.png"):
            identificador = caminho.relative_to(pasta).with_suffix("").as_posix()

            imagem = pygame.image.load(str(caminho)).convert_alpha()

            self.sprites[identificador] = {
                "imagem": imagem,
                "caminho": caminho.relative_to(RAIZ).as_posix()
            }

    def salvar_mapa(self):
        try:
            with CAMINHO_MAPA.open("w", encoding="utf-8") as arquivo:
                json.dump(
                    self.dados,
                    arquivo,
                    indent=4,
                    ensure_ascii=False
                )

            self.salvar_mensagem = "Mapa salvo com sucesso!"

        except OSError as erro:
            self.salvar_mensagem = f"Erro ao salvar: {erro}"

    def obter_posicao_tile(self, posicao_mouse):
        mouse_x, mouse_y = posicao_mouse

        x = (mouse_x - self.posicao_mapa_x) // self.escala
        y = (mouse_y - self.posicao_mapa_y) // self.escala

        if 0 <= x < self.largura and 0 <= y < self.altura:
            return int(x), int(y)

        return None

    def obter_posicao_mundo(self, posicao_mouse):
        mouse_x, mouse_y = posicao_mouse
        fator = self.escala / self.tile_size

        mundo_x = (mouse_x - self.posicao_mapa_x) / fator
        mundo_y = (mouse_y - self.posicao_mapa_y) / fator

        largura_mapa = self.largura * self.tile_size
        altura_mapa = self.altura * self.tile_size

        if not (0 <= mundo_x < largura_mapa):
            return None

        if not (0 <= mundo_y < altura_mapa):
            return None

        x = int(mundo_x // 12) * 12
        y = int(mundo_y // 12) * 12

        return x, y

    def pintar_tile(self, x, y):
        if self.tile_selecionado not in self.tiles_disponiveis:
            return

        self.dados["camadas"][self.camada_atual][y][x] = (
            self.tile_selecionado
        )

    def posicionar_spawn(self, x, y):
        self.dados["spawn_jogador"] = {
            "x": x * self.tile_size,
            "y": y * self.tile_size,
            "direcao": "down"
        }

        self.salvar_mensagem = "Spawn atualizado!"

    def desenhar_texto(self, texto, x, y, fonte=None):
        fonte = fonte or self.fonte

        imagem = fonte.render(
            texto,
            True,
            COR_TEXTO
        )

        self.tela.blit(imagem, (x, y))

    def desenhar_sprites_superiores(self):
        fator = self.escala / self.tile_size

        for sprite in self.dados["sprites_superiores"]:
            identificador = sprite["id"]

            if identificador not in self.sprites:
                continue

            imagem = self.sprites[identificador]["imagem"]
            largura = max(1, round(imagem.get_width() * fator))
            altura = max(1, round(imagem.get_height() * fator))

            imagem_redimensionada = pygame.transform.scale(
                imagem, (largura, altura)
            )

            x = self.posicao_mapa_x + round(sprite["x"] * fator)
            y = self.posicao_mapa_y + round(sprite["y"] * fator)

            self.tela.blit(imagem_redimensionada, (x, y))

    def desenhar_mapa(self):
        tamanho = self.escala

        for y in range(self.altura):
            for x in range(self.largura):
                cor = None

                # Desenha as camadas na ordem definida no JSON.
                for nome_camada in self.camadas:
                    identificador = (
                        self.dados["camadas"][nome_camada][y][x]
                    )

                    if identificador is not None:
                        cor = self.tiles[identificador]["cor"]

                if cor is None:
                    cor = COR_FUNDO

                rect = pygame.Rect(
                    self.posicao_mapa_x + x * tamanho,
                    self.posicao_mapa_y + y * tamanho,
                    tamanho,
                    tamanho
                )

                pygame.draw.rect(self.tela, cor, rect)
                pygame.draw.rect(
                    self.tela,
                    COR_GRADE,
                    rect,
                    1
                )

        self.desenhar_sprites_superiores()

        if self.camada_atual == "superior":
            self.desenhar_grade_auxiliar()

        self.desenhar_spawn()

        self.desenhar_preview_spawn()

    def desenhar_grade_auxiliar(self):
        fator = self.escala / self.tile_size
        largura = self.largura * self.tile_size
        altura = self.altura * self.tile_size

        largura_tela = round(largura * fator)
        altura_tela = round(altura * fator)

        superficie = pygame.Surface(
            (largura_tela, altura_tela),
            pygame.SRCALPHA
        )

        cor = (255, 255, 255, 55)

        for x in range(0, largura + 1, 12):
            posicao = round(x * fator)
            pygame.draw.line(
                superficie, cor,
                (posicao, 0), (posicao, altura_tela)
            )

        for y in range(0, altura + 1, 12):
            posicao = round(y * fator)
            pygame.draw.line(
                superficie, cor,
                (0, posicao), (largura_tela, posicao)
            )

        self.tela.blit(
            superficie,
            (self.posicao_mapa_x, self.posicao_mapa_y)
        )

    def desenhar_preview_spawn(self):
        if self.modo != "spawn":
            return

        posicao = self.obter_posicao_tile(pygame.mouse.get_pos())

        if posicao is None:
            return

        x, y = posicao
        tamanho = self.escala

        rect = pygame.Rect(
            self.posicao_mapa_x + x * tamanho,
            self.posicao_mapa_y + y * tamanho,
            tamanho,
            tamanho
        )

        superficie = pygame.Surface(
            (tamanho, tamanho),
            pygame.SRCALPHA
        )
        superficie.fill((255, 210, 50, 90))

        self.tela.blit(superficie, rect.topleft)

        pygame.draw.rect(
            self.tela, COR_SELECAO, rect, max(2, tamanho // 10)
        )

        pygame.draw.circle(
            self.tela, (255, 255, 255), rect.center,
            max(3, tamanho // 5)
        )
    def desenhar_spawn(self):
        spawn = self.dados.get("spawn_jogador")

        if spawn is None:
            return

        x = spawn["x"] // self.tile_size
        y = spawn["y"] // self.tile_size

        centro_x = self.posicao_mapa_x + x * self.escala + self.escala // 2
        centro_y = self.posicao_mapa_y + y * self.escala + self.escala // 2

        pygame.draw.circle(
            self.tela,
            (255, 220, 40),
            (centro_x, centro_y),
            8
        )

        pygame.draw.circle(
            self.tela,
            (30, 30, 30),
            (centro_x, centro_y),
            8,
            2
        )

    def desenhar_biblioteca_sprites(self):
        self.desenhar_texto(
            "BIBLIOTECA DE SPRITES",
            self.painel_x + 20, 145
        )

        sprites = list(self.sprites.keys())
        inicio = self.sprite_scroll
        visiveis = sprites[inicio:inicio + 12]

        y = 185

        for identificador in visiveis:
            dados = self.sprites[identificador]
            imagem = dados["imagem"]

            largura, altura = imagem.get_size()
            fator = min(28 / largura, 28 / altura)

            miniatura = pygame.transform.scale(
                imagem,
                (
                    max(1, int(largura * fator)),
                    max(1, int(altura * fator))
                )
            )

            rect = pygame.Rect(
                self.painel_x + 15, y, 285, 36
            )

            if identificador == self.sprite_selecionado:
                pygame.draw.rect(self.tela, (85, 75, 35), rect)
                pygame.draw.rect(self.tela, COR_SELECAO, rect, 2)

            self.tela.blit(
                miniatura,
                (self.painel_x + 20, y + 4)
            )

            nome = identificador.split("/")[-1]

            self.desenhar_texto(
                nome,
                self.painel_x + 60,
                y + 9,
                self.fonte_pequena
            )

            y += 40

        self.desenhar_texto(
            f"{len(sprites)} sprites | "
            f"{inicio + 1}-{min(inicio + 12, len(sprites))}",
            self.painel_x + 20, 685, self.fonte_pequena
        )

        self.desenhar_texto(
            "[O] Voltar para pintura",
            self.painel_x + 20, 715, self.fonte_pequena
        )

    def desenhar_painel(self):
        painel = pygame.Rect(
            self.painel_x, 0,
            self.painel_largura, self.altura_janela
        )
        pygame.draw.rect(self.tela, (32, 35, 43), painel)

        # Cabeçalho fixo.
        self.desenhar_texto(
            "SimpSmith", self.painel_x + 20, 16
        )
        self.desenhar_texto(
            "EDITOR DE MAPAS", self.painel_x + 20, 43,
            self.fonte_pequena
        )

        self.desenhar_botao_central()

        self.desenhar_texto(
            f"Mapa: {self.dados['nome']}",
            self.painel_x + 20, 78, self.fonte_pequena
        )
        self.desenhar_texto(
            f"{self.largura} x {self.altura} tiles",
            self.painel_x + 20, 101, self.fonte_pequena
        )

        pygame.draw.line(
            self.tela, (65, 70, 82),
            (self.painel_x + 15, 140),
            (self.painel_x + self.painel_largura - 15, 140), 1
        )

        # Área rolável.
        topo = 151
        rodape = self.altura_janela - 18
        altura_area = max(50, rodape - topo)

        area = pygame.Rect(
            self.painel_x + 8, topo,
            self.painel_largura - 16, altura_area
        )

        superficie = pygame.Surface(
            (area.width, area.height)
        )
        superficie.fill((32, 35, 43))

        tela_original = self.tela
        deslocamento_x = self.painel_x + 8
        deslocamento_y = topo

        class SuperficiePainel:
            def __init__(self, destino, x, y):
                self.destino = destino
                self.x = x
                self.y = y

            def blit(self, imagem, posicao, *args, **kwargs):
                self.destino.blit(
                    imagem,
                    (posicao[0] - self.x, posicao[1] - self.y),
                    *args, **kwargs
                )

        # Desenha os elementos usando coordenadas do painel.
        y = 0

        def texto(texto, posicao_y, fonte=None, cor=COR_TEXTO):
            fonte_usada = fonte or self.fonte
            imagem = fonte_usada.render(texto, True, cor)
            superficie.blit(imagem, (12, posicao_y - self.painel_scroll))

        def secao(titulo, posicao_y):
            texto(titulo, posicao_y)
            pygame.draw.line(
                superficie, (65, 70, 82),
                (12, posicao_y + 27 - self.painel_scroll),
                (area.width - 12, posicao_y + 27 - self.painel_scroll), 1
            )

        # Camada.
        secao("CAMADA ATUAL", y)
        y += 42

        texto(f"<  {self.camada_atual.upper()}  >", y)
        y += 34

        descricoes = {
            "terreno": [
                "Base visual do mapa.",
                "Grama, terra, areia e agua."
            ],
            "superior": [
                "Detalhes sobre o terreno:",
                "flores e vegetacao."
            ],
            "objetos": [
                "Estruturas e elementos",
                "visuais do cenario."
            ]
        }

        for linha in descricoes.get(
            self.camada_atual, ["Camada personalizada."]
        ):
            texto(linha, y, self.fonte_pequena, (170, 176, 188))
            y += 22

        y += 18

        # Biblioteca.
        if self.camada_atual == "superior":
            secao("SPRITES DISPONIVEIS", y)
            y += 38

            sprites = list(self.sprites.items())
            inicio = self.sprite_scroll
            altura_item = 54

            for identificador, informacoes in sprites[inicio:]:
                rect = pygame.Rect(
                    10, y - self.painel_scroll,
                    area.width - 28, 46
                )

                selecionado = identificador == self.sprite_selecionado

                if selecionado:
                    pygame.draw.rect(
                        superficie, (66, 62, 43), rect,
                        border_radius=5
                    )
                    pygame.draw.rect(
                        superficie, COR_SELECAO, rect, 1,
                        border_radius=5
                    )
                else:
                    pygame.draw.rect(
                        superficie, (43, 47, 57), rect,
                        border_radius=5
                    )

                imagem = informacoes["imagem"]
                largura, altura = imagem.get_size()
                fator = min(34 / largura, 34 / altura)

                miniatura = pygame.transform.scale(
                    imagem,
                    (
                        max(1, int(largura * fator)),
                        max(1, int(altura * fator))
                    )
                )

                superficie.blit(
                    miniatura,
                    (17, y + 6 - self.painel_scroll)
                )

                nome = identificador.split("/")[-1]
                fonte_item = self.fonte_pequena
                imagem_nome = fonte_item.render(
                    nome[:25], True, COR_TEXTO
                )
                superficie.blit(
                    imagem_nome,
                    (60, y + 14 - self.painel_scroll)
                )

                y += altura_item

            texto(
                f"{len(sprites)} sprites disponíveis",
                y + 2, self.fonte_pequena,
                (170, 176, 188)
            )
            y += 32

            texto(
                "Use O para voltar à pintura.",
                y, self.fonte_pequena,
                (170, 176, 188)
            )
            y += 38

        else:
            secao("TILES DISPONIVEIS", y)
            y += 38

            disponiveis = list(self.tiles_disponiveis.items())

            if not disponiveis:
                texto(
                    "Nenhum tile cadastrado.",
                    y, self.fonte_pequena
                )
                y += 42
            else:
                for identificador, informacoes in disponiveis:
                    rect = pygame.Rect(
                        10, y - self.painel_scroll,
                        area.width - 28, 44
                    )

                    selecionado = identificador == self.tile_selecionado

                    pygame.draw.rect(
                        superficie,
                        (66, 62, 43) if selecionado else (43, 47, 57),
                        rect, border_radius=5
                    )

                    if selecionado:
                        pygame.draw.rect(
                            superficie, COR_SELECAO,
                            rect, 1, border_radius=5
                        )

                    cor = tuple(informacoes["cor"])
                    pygame.draw.rect(
                        superficie, cor,
                        (18, y + 8 - self.painel_scroll, 28, 28),
                        border_radius=3
                    )

                    nome = identificador[:25]
                    imagem_nome = self.fonte_pequena.render(
                        nome, True, COR_TEXTO
                    )
                    superficie.blit(
                        imagem_nome,
                        (58, y + 13 - self.painel_scroll)
                    )

                    y += 52

            y += 20

        # Ferramentas.
        secao("FERRAMENTAS", y)
        y += 40

        if self.modo == "spawn":
            modo_texto = "Modo: posicionar spawn"
        elif self.modo == "sprites":
            modo_texto = "Modo: posicionar sprites"
        else:
            modo_texto = "Modo: pintura"

        texto(modo_texto, y, self.fonte_pequena)
        y += 34

        controles = [
            ("P", "Alternar modo"),
            ("S", "Posicionar spawn"),
            ("A / D", "Trocar camada"),
            ("ENTER", "Salvar mapa"),
            ("Clique direito", "Apagar elemento"),
            ("F11", "Tela cheia"),
            ("ESC", "Sair do editor")
        ]

        for tecla, descricao in controles:
            pygame.draw.rect(
                superficie, (43, 47, 57),
                (10, y - self.painel_scroll, area.width - 28, 36),
                border_radius=4
            )

            imagem_tecla = self.fonte_pequena.render(
                tecla, True, (150, 180, 235)
            )
            imagem_descricao = self.fonte_pequena.render(
                descricao, True, COR_TEXTO
            )

            superficie.blit(
                imagem_tecla,
                (17, y + 9 - self.painel_scroll)
            )
            superficie.blit(
                imagem_descricao,
                (105, y + 9 - self.painel_scroll)
            )

            y += 43

        y += 12
        texto(
            "Spawn: circulo amarelo",
            y, self.fonte_pequena,
            (220, 195, 90)
        )
        y += 32

        if self.salvar_mensagem:
            texto(
                self.salvar_mensagem,
                y, self.fonte_pequena,
                (130, 205, 150)
            )
            y += 30

        self.painel_conteudo_altura = y
        max_scroll = max(0, y - altura_area)
        self.painel_scroll = max(
            0, min(self.painel_scroll, max_scroll)
        )

        # Recorta o conteúdo dentro da área rolável.
        tela_original.blit(superficie, area.topleft)

        # Barra de rolagem.
        if max_scroll > 0:
            trilho = pygame.Rect(
                self.painel_x + self.painel_largura - 9,
                topo, 4, altura_area
            )
            pygame.draw.rect(
                tela_original, (55, 60, 72), trilho,
                border_radius=3
            )

            altura_barra = max(
                28,
                int(altura_area * altura_area / y)
            )
            deslocamento = int(
                (altura_area - altura_barra)
                * self.painel_scroll / max_scroll
            )

            barra = pygame.Rect(
                trilho.x, trilho.y + deslocamento,
                trilho.width, altura_barra
            )
            pygame.draw.rect(
                tela_original, (130, 145, 170), barra,
                border_radius=3
            )


    def tratar_clique(self, posicao):
        mouse_x, mouse_y = posicao

        if mouse_x >= self.painel_x:
            if mouse_y < 151:
                return

            y_conteudo = mouse_y - 151 + self.painel_scroll

            y = 42
            descricoes = self.camada_atual

            if y_conteudo < 76:
                self.atualizar_camada(
                    -1 if y_conteudo < 59 else 1
                )
                self.painel_scroll = 0
                return

            # A biblioteca começa depois da descrição da camada.
            y_biblioteca = 42 + 34 + 34 + 44

            if self.camada_atual == "superior" and self.modo != "spawn":
                inicio_lista = y_biblioteca + 38
                altura_item = 54

                if y_conteudo >= inicio_lista:
                    indice = (
                        (y_conteudo - inicio_lista) // altura_item
                        + self.sprite_scroll
                    )
                    sprites = list(self.sprites.keys())

                    if 0 <= indice < len(sprites):
                        self.sprite_selecionado = sprites[indice]
                        self.modo = "sprites"
                return

            disponiveis = list(self.tiles_disponiveis.keys())
            inicio_lista = y_biblioteca + 38

            if y_conteudo >= inicio_lista:
                indice = (y_conteudo - inicio_lista) // 52

                if 0 <= indice < len(disponiveis):
                    self.tile_selecionado = disponiveis[indice]
                    self.modo = "pintura"
            return

        if self.modo == "sprites":
            posicao_mundo = self.obter_posicao_mundo(posicao)
            if posicao_mundo is None:
                return
            x, y = posicao_mundo
        else:
            posicao_tile = self.obter_posicao_tile(posicao)
            if posicao_tile is None:
                return
            x, y = posicao_tile

        if self.modo == "pintura":
            self.pintar_tile(x, y)

        elif self.modo == "sprites":
            if self.sprite_selecionado is not None:
                self.dados["sprites_superiores"].append({
                    "id": self.sprite_selecionado,
                    "x": x,
                    "y": y
                })
                self.salvar_mensagem = "Sprite posicionado!"

        elif self.modo == "spawn":
            self.posicionar_spawn(x, y)


    def alternar_tela_cheia(self):
        if self.tela_cheia:
            self.tela_cheia = False
            self.tela = pygame.display.set_mode(
                (self.largura_janela, self.altura_janela),
                pygame.RESIZABLE
            )
        else:
            self.largura_janela = self.tela.get_width()
            self.altura_janela = self.tela.get_height()

            self.tela_cheia = True
            self.tela = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN
            )

        self.largura_janela, self.altura_janela = self.tela.get_size()
        self.painel_x = self.largura_janela - self.painel_largura

    def voltar_central(self):
        self.executando = False

    def desenhar_botao_central(self):
        rect = pygame.Rect(
            self.painel_x + 20, 108, 280, 28
        )

        pygame.draw.rect(self.tela, (52, 61, 76), rect, border_radius=5)
        pygame.draw.rect(self.tela, (100, 130, 175), rect, 1, border_radius=5)

        texto = self.fonte_pequena.render(
            "VOLTAR À CENTRAL", True, (241, 241, 241)
        )
        self.tela.blit(
            texto,
            texto.get_rect(center=rect.center)
        )

    def tratar_eventos(self):
        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                self.executando = False

            elif evento.type == pygame.KEYDOWN:

                if evento.key == pygame.K_ESCAPE:
                    self.executando = False

                elif evento.key == pygame.K_F11:
                    self.alternar_tela_cheia()

                elif evento.key == pygame.K_RETURN:
                    self.salvar_mapa()

                elif evento.key == pygame.K_a:
                    self.atualizar_camada(-1)

                elif evento.key == pygame.K_d:
                    self.atualizar_camada(1)

                elif evento.key == pygame.K_p:
                    self.modo = (
                        "sprites"
                        if self.camada_atual == "superior"
                        else "pintura"
                    )

                elif evento.key == pygame.K_s:
                    self.modo = "spawn"


            elif evento.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                if mouse_x >= self.painel_x:
                    topo = 151
                    rodape = self.altura_janela - 18
                    altura_area = max(50, rodape - topo)
                    max_scroll = max(
                        0, self.painel_conteudo_altura - altura_area
                    )

                    self.painel_scroll = max(
                        0,
                        min(
                            max_scroll,
                            self.painel_scroll - evento.y * 45
                        )
                    )

                    if self.camada_atual == "superior":
                        self.sprite_scroll = max(
                            0,
                            min(
                                max(0, len(self.sprites) - 1),
                                self.sprite_scroll - evento.y
                            )
                        )

                else:
                    zoom_anterior = self.escala
                    novo_zoom = max(
                        self.zoom_minimo,
                        min(
                            self.zoom_maximo,
                            round(self.escala * (1.15 ** evento.y))
                        )
                    )

                    if novo_zoom != zoom_anterior:
                        fator = novo_zoom / zoom_anterior

                        self.posicao_mapa_x = round(
                            mouse_x - (mouse_x - self.posicao_mapa_x) * fator
                        )
                        self.posicao_mapa_y = round(
                            mouse_y - (mouse_y - self.posicao_mapa_y) * fator
                        )
                        self.escala = novo_zoom

            elif evento.type == pygame.MOUSEBUTTONDOWN:

                if evento.button == 2:
                    self.arrastando_camera = True
                    self.ultima_posicao_camera = evento.pos

                elif evento.button == 1:
                    botao_central = pygame.Rect(
                        self.painel_x + 20, 108, 280, 28
                    )

                    if botao_central.collidepoint(evento.pos):
                        self.voltar_central()
                    else:
                        self.tratar_clique(evento.pos)

                elif evento.button == 3:
                    if self.modo == "sprites":
                        mouse_x, mouse_y = evento.pos

                        fator = self.escala / self.tile_size

                        mundo_x = (
                            mouse_x - self.posicao_mapa_x
                        ) / fator

                        mundo_y = (
                            mouse_y - self.posicao_mapa_y
                        ) / fator

                        for sprite in reversed(
                            self.dados["sprites_superiores"]
                        ):
                            imagem = self.sprites.get(
                                sprite["id"], {}
                            ).get("imagem")

                            if imagem is None:
                                continue

                            rect = pygame.Rect(
                                sprite["x"],
                                sprite["y"],
                                imagem.get_width(),
                                imagem.get_height()
                            )

                            if rect.collidepoint(mundo_x, mundo_y):
                                self.dados[
                                    "sprites_superiores"
                                ].remove(sprite)

                                self.salvar_mensagem = "Sprite removido!"
                                break

                    else:
                        posicao = self.obter_posicao_tile(evento.pos)

                        if posicao is not None:
                            x, y = posicao

                            self.dados["camadas"][
                                self.camada_atual
                            ][y][x] = None

            elif evento.type == pygame.VIDEORESIZE:
                if not self.tela_cheia:
                    self.largura_janela = max(800, evento.w)
                    self.altura_janela = max(600, evento.h)

                    self.tela = pygame.display.set_mode(
                        (self.largura_janela, self.altura_janela),
                        pygame.RESIZABLE
                    )

                    self.largura_janela, self.altura_janela = (
                        self.tela.get_size()
                    )
                    self.painel_x = (
                        self.largura_janela - self.painel_largura
                    )

            elif evento.type == pygame.MOUSEBUTTONUP:
                if evento.button == 2:
                    self.arrastando_camera = False
                    self.ultima_posicao_camera = None

            elif evento.type == pygame.MOUSEMOTION:

                if self.arrastando_camera:
                    dx = evento.pos[0] - self.ultima_posicao_camera[0]
                    dy = evento.pos[1] - self.ultima_posicao_camera[1]

                    self.posicao_mapa_x += dx
                    self.posicao_mapa_y += dy
                    self.ultima_posicao_camera = evento.pos

                elif pygame.mouse.get_pressed()[0]:
                    posicao = self.obter_posicao_tile(evento.pos)

                    if posicao is not None and self.modo == "pintura":
                        x, y = posicao
                        self.pintar_tile(x, y)

    def executar(self):
        while self.executando:
            self.relogio.tick(60)

            self.tratar_eventos()

            self.tela.fill(COR_FUNDO)

            self.desenhar_mapa()
            self.desenhar_painel()

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    editor = EditorMapa()
    editor.executar()

