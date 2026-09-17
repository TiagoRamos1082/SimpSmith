import pygame


class Mineracao:
    TECLA = pygame.K_e
    TEMPO_MINERACAO = 2.0
    DISTANCIA_MAXIMA = 70

    LARGURA_BARRA = 300
    ALTURA_BARRA = 18
    MARGEM_INFERIOR = 55

    COR_FUNDO = (35, 35, 35)
    COR_BARRA = (245, 190, 55)
    COR_BORDA = (240, 240, 240)

    def __init__(self, inventario):
        self.inventario = inventario
        self.alvo = None
        self.progresso = 0.0
        self._aguardando_soltar = False
        self.mensagem = ""
        self.coleta_concluida = False

    def atualizar(self, dt, jogador, spawn):
        teclas = pygame.key.get_pressed()

        # Depois de uma falha, exige soltar E antes de tentar novamente.
        if not teclas[self.TECLA]:
            self._aguardando_soltar = False
            self.mensagem = ""
            self._cancelar()
            return

        if self._aguardando_soltar:
            return

        minerio = self._encontrar_alvo(jogador, spawn)
        if minerio is None:
            self._cancelar()
            return

        if minerio is not self.alvo:
            self.alvo = minerio
            self.progresso = 0.0

        dados_item = self.inventario.catalogo.obter(self.alvo.tipo)
        if dados_item is None:
            self.mensagem = f"Item '{self.alvo.tipo}' não existe no catálogo."
            self._aguardando_soltar = True
            self._cancelar()
            return

        tempo = float(dados_item.get("tempo_coleta", self.TEMPO_MINERACAO))
        self.progresso += dt

        if self.progresso >= tempo:
            tipo_minerio = self.alvo.tipo
            if self.inventario.adicionar(tipo_minerio):
                spawn.minerar(self.alvo)
                self.coleta_concluida = True
                self.mensagem = ""
                self._cancelar()
            else:
                self.mensagem = "Inventário cheio. Solte E para tentar novamente."
                self._aguardando_soltar = True
                self._cancelar()

    def _encontrar_alvo(self, jogador, spawn):
        for minerio in spawn.minerios:
            if self._esta_na_frente_e_encostando(jogador, minerio):
                return minerio
        return None

    def _esta_na_frente_e_encostando(self, jogador, minerio):
        jogador_rect = pygame.Rect(
            round(jogador.x) + 7,
            round(jogador.y) + 5,
            jogador.largura - 14,
            jogador.altura - 7
        )
        minerio_rect = minerio.rect
        tolerancia = 4

        if jogador.direcao == "up":
            alinhado = (
                jogador_rect.left < minerio_rect.right
                and jogador_rect.right > minerio_rect.left
            )
            encostando = abs(jogador_rect.top - minerio_rect.bottom) <= tolerancia
        elif jogador.direcao == "down":
            alinhado = (
                jogador_rect.left < minerio_rect.right
                and jogador_rect.right > minerio_rect.left
            )
            encostando = abs(jogador_rect.bottom - minerio_rect.top) <= tolerancia
        elif jogador.direcao == "left":
            alinhado = (
                jogador_rect.top < minerio_rect.bottom
                and jogador_rect.bottom > minerio_rect.top
            )
            encostando = abs(jogador_rect.left - minerio_rect.right) <= tolerancia
        elif jogador.direcao == "right":
            alinhado = (
                jogador_rect.top < minerio_rect.bottom
                and jogador_rect.bottom > minerio_rect.top
            )
            encostando = abs(jogador_rect.right - minerio_rect.left) <= tolerancia
        else:
            return False

        return alinhado and encostando

    def _cancelar(self):
        self.alvo = None
        self.progresso = 0.0

    def desenhar(self, tela):
        if self.alvo is None and not self.mensagem:
            return

        largura = self.LARGURA_BARRA
        altura = self.ALTURA_BARRA
        x = (tela.get_width() - largura) // 2
        y = tela.get_height() - self.MARGEM_INFERIOR - altura
        fundo = pygame.Rect(x, y, largura, altura)

        pygame.draw.rect(tela, self.COR_FUNDO, fundo, border_radius=8)

        if self.alvo is not None:
            dados_item = self.inventario.catalogo.obter(self.alvo.tipo)
            tempo = float(dados_item.get("tempo_coleta", self.TEMPO_MINERACAO)) if dados_item else self.TEMPO_MINERACAO
            percentual = min(self.progresso / tempo, 1.0)
            largura_preenchida = round(largura * percentual)
            x_preenchimento = (tela.get_width() - largura_preenchida) // 2
            preenchimento = pygame.Rect(x_preenchimento, y, largura_preenchida, altura)
            if largura_preenchida > 0:
                pygame.draw.rect(tela, self.COR_BARRA, preenchimento, border_radius=8)

            texto = pygame.font.Font(None, 24).render(
                "Minerando...", True, (255, 255, 255)
            )
            tela.blit(texto, texto.get_rect(center=(tela.get_width() // 2, y - 18)))

        pygame.draw.rect(tela, self.COR_BORDA, fundo, width=2, border_radius=8)

        if self.mensagem:
            texto = pygame.font.Font(None, 22).render(
                self.mensagem, True, (255, 220, 120)
            )
            tela.blit(texto, texto.get_rect(center=(tela.get_width() // 2, y - 22)))
