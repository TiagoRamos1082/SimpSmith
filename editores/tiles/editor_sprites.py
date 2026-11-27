import pygame
import ctypes
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]

ORIGEM = RAIZ / "assets" / "tiles" / "spritesheet_original.png"
DESTINO = RAIZ / "assets" / "tiles"

TAMANHO_CELULA = 12

CATEGORIAS = {
    pygame.K_1: "terreno",
    pygame.K_2: "superior",
    pygame.K_3: "objetos"
}


class EditorSprites:
    def __init__(self):
        pygame.init()

        info = pygame.display.Info()
        self.largura_janela = min(1200, info.current_w)
        self.altura_janela = min(760, info.current_h)
        self.tela_cheia = False

        self.tela = pygame.display.set_mode(
            (self.largura_janela, self.altura_janela),
            pygame.RESIZABLE
        )
        self.largura, self.altura = self.tela.get_size()
        pygame.display.set_caption("SimpSmith - Editor de Sprites")

        # Maximiza a janela mantendo bordas e barra de tarefas.
        try:
            pygame.display.flip()
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 3)
        except (AttributeError, OSError):
            pass


        self.fonte = pygame.font.Font(None, 25)
        self.fonte_pequena = pygame.font.Font(None, 18)

        self.relogio = pygame.time.Clock()
        self.executando = True

        self.imagem = pygame.image.load(str(ORIGEM)).convert_alpha()

        self.imagem_largura, self.imagem_altura = self.imagem.get_size()

        self.colunas = self.imagem_largura // TAMANHO_CELULA
        self.linhas = self.imagem_altura // TAMANHO_CELULA

        self.escala = min(
            1.5,
            (self.altura - 100) / self.imagem_altura
        )

        self.visual_largura = int(self.imagem_largura * self.escala)
        self.visual_altura = int(self.imagem_altura * self.escala)

        self.origem_x = 20
        self.origem_y = 65

        self.zoom_minimo = 0.25
        self.zoom_maximo = 5.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.arrastando_camera = False
        self.ultima_posicao_camera = None

        self.largura_painel = 300
        self.scroll_painel = 0
        self.max_scroll_painel = 0
        self.limite_visual = self.largura - self.largura_painel - 35

        self.imagem_visual = pygame.transform.scale(
            self.imagem,
            (self.visual_largura, self.visual_altura)
        )

        self.selecao_inicio = None
        self.selecao_fim = None
        self.selecionando = False

        self.categoria = "terreno"
        self.nome = "novo_sprite"
        self.editando_nome = False

        self.mensagem = "Arraste o mouse para selecionar uma regiao."

    def alternar_tela_cheia(self):
        if self.tela_cheia:
            self.tela = pygame.display.set_mode(
                (self.largura_janela, self.altura_janela),
                pygame.RESIZABLE
            )
            self.tela_cheia = False
        else:
            self.largura_janela = self.largura
            self.altura_janela = self.altura
            self.tela = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN
            )
            self.tela_cheia = True

        self.largura, self.altura = self.tela.get_size()
        self.limite_visual = self.largura - self.largura_painel - 35

    def voltar_central(self):
        # A Central permanece aberta em segundo plano.
        self.executando = False

    def desenhar_texto(self, texto, x, y, fonte=None, cor=(240, 240, 240)):
        fonte = fonte or self.fonte
        imagem = fonte.render(texto, True, cor)
        self.tela.blit(imagem, (x, y))

    def obter_celula(self, posicao):
        mx, my = posicao

        if mx >= self.largura - self.largura_painel:
            return None

        x = (
            mx - self.origem_x - self.pan_x
        ) / (TAMANHO_CELULA * self.escala)

        y = (
            my - self.origem_y - self.pan_y
        ) / (TAMANHO_CELULA * self.escala)

        if not (0 <= x < self.colunas and 0 <= y < self.linhas):
            return None

        return int(x), int(y)

    def obter_selecao(self):
        if self.selecao_inicio is None or self.selecao_fim is None:
            return None

        x1, y1 = self.selecao_inicio
        x2, y2 = self.selecao_fim

        esquerda = min(x1, x2)
        topo = min(y1, y2)

        direita = max(x1, x2) + 1
        baixo = max(y1, y2) + 1

        return esquerda, topo, direita, baixo

    def desenhar_grade(self):
        tamanho = TAMANHO_CELULA * self.escala

        for x in range(self.colunas + 1):
            px = self.origem_x + round(self.pan_x) + int(x * tamanho)
            pygame.draw.line(
                self.tela, (70, 70, 70),
                (px, self.origem_y + round(self.pan_y)),
                (px, self.origem_y + round(self.pan_y) + self.visual_altura)
            )

        for y in range(self.linhas + 1):
            py = self.origem_y + round(self.pan_y) + int(y * tamanho)
            pygame.draw.line(
                self.tela, (70, 70, 70),
                (self.origem_x + round(self.pan_x), py),
                (self.origem_x + round(self.pan_x) + self.visual_largura, py)
            )

    def desenhar_selecao(self):
        selecao = self.obter_selecao()

        if selecao is None:
            return

        x1, y1, x2, y2 = selecao
        tamanho = TAMANHO_CELULA * self.escala

        rect = pygame.Rect(
            self.origem_x + round(self.pan_x) + int(x1 * tamanho),
            self.origem_y + round(self.pan_y) + int(y1 * tamanho),
            int((x2 - x1) * tamanho),
            int((y2 - y1) * tamanho)
        )

        pygame.draw.rect(self.tela, (255, 210, 50), rect, 3)

    def desenhar_painel(self):
        fundo = (32, 35, 43)
        painel = (41, 45, 54)
        cartao = (48, 53, 64)
        borda = (58, 64, 77)
        texto = (240, 240, 240)
        secundario = (165, 170, 181)
        azul = (122, 162, 247)
        destaque = (217, 170, 91)

        painel_x = self.largura - self.largura_painel
        margem = 18
        x = painel_x + margem
        largura = self.largura_painel - margem * 2

        # Cabecalho.
        pygame.draw.rect(self.tela, fundo, (0, 0, self.largura, 70))
        pygame.draw.line(
            self.tela, borda, (0, 69), (self.largura, 69), 1
        )

        self.desenhar_texto("SimpSmith", 24, 10, self.fonte, texto)
        self.desenhar_texto(
            "EDITOR DE SPRITES", 25, 40,
            self.fonte_pequena, secundario
        )

        botao_voltar = pygame.Rect(self.largura - 190, 16, 166, 38)
        pygame.draw.rect(
            self.tela, (52, 56, 66), botao_voltar, border_radius=6
        )
        pygame.draw.rect(
            self.tela, borda, botao_voltar, 1, border_radius=6
        )
        label = self.fonte_pequena.render(
            "VOLTAR À CENTRAL", True, texto
        )
        self.tela.blit(label, label.get_rect(center=botao_voltar.center))

        # Fundo do painel.
        pygame.draw.rect(
            self.tela, painel,
            (painel_x, 70, self.largura_painel, self.altura - 70)
        )
        pygame.draw.line(
            self.tela, borda,
            (painel_x, 70), (painel_x, self.altura), 2
        )

        area_topo = 82
        area_base = self.altura - 18
        altura_area = max(1, area_base - area_topo)

        # Todo o conteudo abaixo respeita a area de recorte.
        clip_anterior = self.tela.get_clip()
        self.tela.set_clip(
            pygame.Rect(painel_x, area_topo,
                        self.largura_painel, altura_area)
        )

        def titulo(rotulo, y):
            self.desenhar_texto(
                rotulo, x, y - self.scroll_painel,
                self.fonte_pequena, azul
            )

        def linha(rotulo, y, cor=texto):
            self.desenhar_texto(
                rotulo, x, y - self.scroll_painel,
                self.fonte_pequena, cor
            )

        y = 95

        titulo("SPRITESHEET", y)
        y += 30
        linha(f"{self.imagem_largura} x {self.imagem_altura} px", y)
        y += 25
        linha(f"Grade: {self.colunas} x {self.linhas}", y)
        y += 25
        linha(f"Celula: {TAMANHO_CELULA} x {TAMANHO_CELULA}", y)
        y += 34

        pygame.draw.line(
            self.tela, borda,
            (x, y - self.scroll_painel),
            (x + largura, y - self.scroll_painel), 1
        )

        y += 18
        titulo("SELECAO ATUAL", y)
        y += 30

        selecao = self.obter_selecao()
        if selecao:
            x1, y1, x2, y2 = selecao
            colunas = x2 - x1
            linhas = y2 - y1
            linha(f"Colunas: {colunas}", y)
            y += 25
            linha(f"Linhas: {linhas}", y)
            y += 25
            linha(
                f"Pixels: {colunas * TAMANHO_CELULA} x "
                f"{linhas * TAMANHO_CELULA}", y
            )
        else:
            linha("Nenhuma regiao selecionada.", y, secundario)

        y += 42
        pygame.draw.line(
            self.tela, borda,
            (x, y - self.scroll_painel),
            (x + largura, y - self.scroll_painel), 1
        )

        y += 18
        titulo("CATEGORIA", y)
        y += 32

        categorias = [
            ("[1] Terreno", "terreno"),
            ("[2] Superior", "superior"),
            ("[3] Objetos", "objetos"),
        ]

        for nome, valor in categorias:
            cor = azul if self.categoria == valor else secundario
            prefixo = "> " if self.categoria == valor else "  "
            linha(prefixo + nome, y, cor)
            y += 29

        y += 12
        pygame.draw.line(
            self.tela, borda,
            (x, y - self.scroll_painel),
            (x + largura, y - self.scroll_painel), 1
        )

        y += 18
        titulo("NOME DO SPRITE", y)
        y += 32

        nome = self.nome
        if len(nome) > 27:
            nome = nome[:24] + "..."

        linha(
            nome, y,
            destaque if self.editando_nome else texto
        )
        y += 42

        pygame.draw.line(
            self.tela, borda,
            (x, y - self.scroll_painel),
            (x + largura, y - self.scroll_painel), 1
        )

        y += 18
        titulo("ATALHOS", y)
        y += 32

        atalhos = [
            "[F2] Editar nome",
            "[ENTER] Exportar",
            "[R] Limpar selecao",
            "[F11] Tela cheia",
            "[ESC] Fechar editor",
        ]

        for atalho in atalhos:
            linha(atalho, y, secundario)
            y += 27

        y += 15
        pygame.draw.line(
            self.tela, borda,
            (x, y - self.scroll_painel),
            (x + largura, y - self.scroll_painel), 1
        )
        y += 18
        titulo("STATUS", y)
        y += 30

        mensagem = self.mensagem
        if len(mensagem) > 35:
            mensagem = mensagem[:32] + "..."
        linha(mensagem, y, destaque)

        # Limite de rolagem.
        conteudo_altura = y + 45 - 95
        self.max_scroll_painel = max(
            0, conteudo_altura - altura_area
        )
        self.scroll_painel = max(
            0, min(self.scroll_painel, self.max_scroll_painel)
        )

        # Barra de rolagem.
        if self.max_scroll_painel > 0:
            trilho_x = self.largura - 9
            trilho = pygame.Rect(trilho_x, area_topo, 4, altura_area)
            pygame.draw.rect(self.tela, borda, trilho, border_radius=3)

            proporcao = altura_area / conteudo_altura
            altura_barra = max(28, int(altura_area * proporcao))
            deslocamento = int(
                (altura_area - altura_barra)
                * self.scroll_painel / self.max_scroll_painel
            )
            barra = pygame.Rect(
                trilho_x, area_topo + deslocamento,
                4, altura_barra
            )
            pygame.draw.rect(
                self.tela, azul, barra, border_radius=3
            )

        self.tela.set_clip(clip_anterior)

    def exportar(self):
        selecao = self.obter_selecao()

        if selecao is None:
            self.mensagem = "Selecione uma regiao primeiro."
            return

        nome = self.nome.strip()

        if not nome or nome in (".", ".."):
            self.mensagem = "Digite um nome valido."
            return

        if any(caractere in nome for caractere in '\\/:*?"<>|'):
            self.mensagem = "Nome contem caracteres invalidos."
            return

        x1, y1, x2, y2 = selecao

        area = pygame.Rect(
            x1 * TAMANHO_CELULA,
            y1 * TAMANHO_CELULA,
            (x2 - x1) * TAMANHO_CELULA,
            (y2 - y1) * TAMANHO_CELULA
        )

        recorte = self.imagem.subsurface(area).copy()

        pasta = DESTINO / self.categoria
        pasta.mkdir(parents=True, exist_ok=True)

        caminho = pasta / f"{nome}.png"

        if caminho.exists():
            self.mensagem = "Ja existe um sprite com esse nome."
            return

        pygame.image.save(recorte, str(caminho))

        self.mensagem = (
            f"Exportado: {self.categoria}/{nome}.png"
        )

    def tratar_eventos(self):
        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                self.executando = False

            elif evento.type == pygame.KEYDOWN:

                if self.editando_nome:
                    if evento.key == pygame.K_RETURN:
                        self.editando_nome = False
                    elif evento.key == pygame.K_BACKSPACE:
                        self.nome = self.nome[:-1]
                    elif evento.key == pygame.K_ESCAPE:
                        self.editando_nome = False
                    continue

                if evento.key == pygame.K_F11:
                    self.alternar_tela_cheia()

                elif evento.key == pygame.K_ESCAPE:
                    self.executando = False

                elif evento.key == pygame.K_r:
                    self.selecao_inicio = None
                    self.selecao_fim = None
                    self.mensagem = "Selecao limpa."

                elif evento.key == pygame.K_F2:
                    self.editando_nome = True
                    self.mensagem = "Digite o nome e pressione Enter."

                elif evento.key == pygame.K_RETURN:
                    self.exportar()

                elif evento.key in CATEGORIAS:
                    self.categoria = CATEGORIAS[evento.key]

            elif evento.type == pygame.TEXTINPUT:
                if self.editando_nome:
                    self.nome += evento.text

            elif evento.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                if mouse_x >= self.largura - self.largura_painel:
                    self.scroll_painel -= evento.y * 35
                    self.scroll_painel = max(
                        0,
                        min(self.scroll_painel, self.max_scroll_painel)
                    )
                else:
                    zoom_anterior = self.escala
                    novo_zoom = max(
                        self.zoom_minimo,
                        min(self.zoom_maximo,
                            self.escala * (1.15 ** evento.y))
                    )

                    mundo_x = (
                        mouse_x - self.origem_x - self.pan_x
                    ) / zoom_anterior
                    mundo_y = (
                        mouse_y - self.origem_y - self.pan_y
                    ) / zoom_anterior

                    self.pan_x = (
                        mouse_x - self.origem_x - mundo_x * novo_zoom
                    )
                    self.pan_y = (
                        mouse_y - self.origem_y - mundo_y * novo_zoom
                    )

                    self.escala = novo_zoom
                    self.visual_largura = round(
                        self.imagem_largura * self.escala
                    )
                    self.visual_altura = round(
                        self.imagem_altura * self.escala
                    )
                    self.imagem_visual = pygame.transform.scale(
                        self.imagem,
                        (self.visual_largura, self.visual_altura)
                    )

            elif evento.type == pygame.VIDEORESIZE:
                if not self.tela_cheia:
                    self.largura, self.altura = evento.size
                    self.tela = pygame.display.set_mode(
                        evento.size, pygame.RESIZABLE
                    )
                    self.limite_visual = (
                        self.largura - self.largura_painel - 35
                    )

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if (
                    evento.button == 1
                    and pygame.Rect(
                        self.largura - 190, 16, 166, 38
                    ).collidepoint(evento.pos)
                ):
                    self.voltar_central()

                elif evento.button == 2:
                    self.arrastando_camera = True
                    self.ultima_posicao_camera = evento.pos

                elif evento.button == 1:
                    celula = self.obter_celula(evento.pos)

                    if celula is not None:
                        self.selecao_inicio = celula
                        self.selecao_fim = celula
                        self.selecionando = True

            elif evento.type == pygame.MOUSEMOTION:
                if self.arrastando_camera:
                    dx = evento.pos[0] - self.ultima_posicao_camera[0]
                    dy = evento.pos[1] - self.ultima_posicao_camera[1]
                    self.pan_x += dx
                    self.pan_y += dy
                    self.ultima_posicao_camera = evento.pos

                elif self.selecionando:
                    celula = self.obter_celula(evento.pos)

                    if celula is not None:
                        self.selecao_fim = celula

            elif evento.type == pygame.MOUSEBUTTONUP:
                if evento.button == 2:
                    self.arrastando_camera = False
                    self.ultima_posicao_camera = None

                elif evento.button == 1:
                    self.selecionando = False

    def executar(self):
        while self.executando:
            self.relogio.tick(60)
            self.tratar_eventos()

            self.tela.fill((35, 35, 40))

            self.tela.blit(
                self.imagem_visual,
                (
                    self.origem_x + round(self.pan_x),
                    self.origem_y + round(self.pan_y)
                )
            )

            self.desenhar_grade()
            self.desenhar_selecao()
            self.desenhar_painel()

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    EditorSprites().executar()

