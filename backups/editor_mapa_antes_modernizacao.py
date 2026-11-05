
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

        self.tela = pygame.display.set_mode(
            (self.largura_janela, self.altura_janela)
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
        pygame.draw.rect(self.tela, COR_PAINEL, painel)

        descricoes = {
            "terreno": [
                "Base visual do mapa.",
                "Grama, terra, areia e agua."
            ],
            "superior": [
                "Detalhes desenhados sobre",
                "o terreno: flores e vegetacao."
            ],
            "objetos": [
                "Tiles de estruturas e",
                "elementos visuais do cenario."
            ]
        }

        self.desenhar_texto("EDITOR DE MAPAS", self.painel_x + 20, 25)
        self.desenhar_texto(
            f"Mapa: {self.dados['nome']}", self.painel_x + 20, 65
        )
        self.desenhar_texto(
            f"Dimensoes: {self.largura} x {self.altura}",
            self.painel_x + 20, 95, self.fonte_pequena
        )

        self.desenhar_texto("CAMADA ATUAL", self.painel_x + 20, 145)
        self.desenhar_texto(
            f"< {self.camada_atual} >", self.painel_x + 20, 175
        )

        y = 205
        for linha in descricoes.get(
            self.camada_atual, ["Camada personalizada."]
        ):
            self.desenhar_texto(
                linha, self.painel_x + 20, y, self.fonte_pequena
            )
            y += 22

        titulo = (
            "SPRITES DISPONIVEIS"
            if self.camada_atual == "superior"
            else "TILES DISPONIVEIS"
        )
        self.desenhar_texto(titulo, self.painel_x + 20, 275)

        if self.camada_atual == "superior":
            sprites = list(self.sprites.items())
            inicio = self.sprite_scroll
            visiveis = sprites[inicio:inicio + 4]
            y = 310

            for identificador, informacoes in visiveis:
                imagem = informacoes["imagem"]
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
                    self.painel_x + 20, y, 280, 32
                )

                if identificador == self.sprite_selecionado:
                    pygame.draw.rect(self.tela, (85, 75, 35), rect)
                    pygame.draw.rect(
                        self.tela, COR_SELECAO, rect, 2
                    )

                self.tela.blit(
                    miniatura, (self.painel_x + 20, y + 2)
                )
                self.desenhar_texto(
                    identificador.split("/")[-1],
                    self.painel_x + 60, y + 7,
                    self.fonte_pequena
                )
                y += 42

            self.desenhar_texto(
                f"{len(sprites)} sprites | "
                f"{inicio + 1}-{min(inicio + 4, len(sprites))}",
                self.painel_x + 20, 475, self.fonte_pequena
            )

        else:
            disponiveis = self.tiles_disponiveis
            y = 310

            if not disponiveis:
                self.desenhar_texto(
                    "Nenhum tile cadastrado.",
                    self.painel_x + 20, y, self.fonte_pequena
                )
            else:
                for identificador, informacoes in disponiveis.items():
                    cor = tuple(informacoes["cor"])
                    rect = pygame.Rect(
                        self.painel_x + 20, y, 28, 28
                    )
                    pygame.draw.rect(self.tela, cor, rect)

                    if identificador == self.tile_selecionado:
                        pygame.draw.rect(
                            self.tela, COR_SELECAO, rect, 3
                        )

                    self.desenhar_texto(
                        identificador, self.painel_x + 60,
                        y + 5, self.fonte_pequena
                    )
                    y += 42

        self.desenhar_texto("FERRAMENTAS", self.painel_x + 20, 490)

        if self.modo == "spawn":
            destaque = pygame.Rect(
                self.painel_x + 12, 512, 290, 32
            )
            pygame.draw.rect(self.tela, (100, 80, 20), destaque)
            self.desenhar_texto(
                "MODO: POSICIONAR SPAWN",
                self.painel_x + 20, 520, self.fonte_pequena
            )
        else:
            modo_texto = (
                "Modo atual: sprites"
                if self.modo == "sprites"
                else "Modo atual: pintura"
            )
            self.desenhar_texto(
                modo_texto, self.painel_x + 20,
                520, self.fonte_pequena
            )

        controles = [
            "[P] Alternar modo",
            "[S] Posicionar spawn",
            "[A/D] Trocar camada",
            "[ENTER] Salvar mapa",
            "[Clique direito] Apagar",
            "[ESC] Sair do editor"
        ]

        y = 550
        for controle in controles:
            self.desenhar_texto(
                controle, self.painel_x + 20,
                y, self.fonte_pequena
            )
            y += 25

        self.desenhar_texto(
            "Spawn: circulo amarelo",
            self.painel_x + 20,
            self.altura_janela - 30,
            self.fonte_pequena
        )

        if self.salvar_mensagem:
            self.desenhar_texto(
                self.salvar_mensagem,
                self.painel_x + 20, 735,
                self.fonte_pequena
            )

    def tratar_clique(self, posicao):
        mouse_x, mouse_y = posicao

        if mouse_x >= self.painel_x:
            if self.camada_atual == "superior" and self.modo != "spawn":
                if 310 <= mouse_y < 478:
                    indice = (
                        (mouse_y - 310) // 42 + self.sprite_scroll
                    )
                    sprites = list(self.sprites.keys())

                    if 0 <= indice < len(sprites):
                        self.sprite_selecionado = sprites[indice]
                        self.modo = "sprites"
                return

            y = 310
            x = self.painel_x + 20

            for identificador in self.tiles_disponiveis:
                rect = pygame.Rect(x, y, 200, 28)

                if rect.collidepoint(posicao):
                    self.tile_selecionado = identificador
                    self.modo = "pintura"
                    return
                y += 42
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

    def tratar_eventos(self):
        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                self.executando = False

            elif evento.type == pygame.KEYDOWN:

                if evento.key == pygame.K_ESCAPE:
                    self.executando = False

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
                    if self.modo == "sprites":
                        self.sprite_scroll = max(
                            0,
                            min(
                                max(0, len(self.sprites) - 4),
                                self.sprite_scroll - evento.y
                            )
                        )

                else:
                    zoom_anterior = self.escala
                    novo_zoom = max(
                        self.zoom_minimo,
                        min(self.zoom_maximo,
                            round(self.escala * (1.15 ** evento.y)))
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

