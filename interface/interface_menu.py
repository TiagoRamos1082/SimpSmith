import pygame


class InterfaceMenu:
    def __init__(self):
        self.fonte_titulo = pygame.font.Font(None, 64)
        self.fonte_botao = pygame.font.Font(None, 34)
        self.botoes = []
        self.selecionado = 0

    def tratar_evento(self, evento, opcoes):
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_UP:
                self.selecionado = (
                    self.selecionado - 1
                ) % len(opcoes)

            elif evento.key == pygame.K_DOWN:
                self.selecionado = (
                    self.selecionado + 1
                ) % len(opcoes)

            elif evento.key == pygame.K_RETURN:
                return opcoes[self.selecionado]

        elif evento.type == pygame.MOUSEMOTION:
            for indice, rect in enumerate(self.botoes):
                if rect.collidepoint(evento.pos):
                    self.selecionado = indice

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:
                for indice, rect in enumerate(self.botoes):
                    if rect.collidepoint(evento.pos):
                        self.selecionado = indice
                        return opcoes[indice]

        return None

    def desenhar(self, tela, titulo, opcoes, sobreposicao=False):
        largura, altura = tela.get_size()

        if sobreposicao:
            fundo = pygame.Surface(
                (largura, altura),
                pygame.SRCALPHA
            )
            fundo.fill((0, 0, 0, 190))
            tela.blit(fundo, (0, 0))
        else:
            tela.fill((22, 24, 32))

        texto_titulo = self.fonte_titulo.render(
            titulo, True, (240, 240, 245)
        )

        tela.blit(
            texto_titulo,
            texto_titulo.get_rect(
                center=(largura // 2, altura // 3)
            )
        )

        self.botoes = []

        altura_botao = 55
        espacamento = 15
        largura_botao = 420

        inicio_y = altura // 2 - (
            len(opcoes) * (altura_botao + espacamento)
        ) // 2

        for indice, opcao in enumerate(opcoes):
            rect = pygame.Rect(
                (largura - largura_botao) // 2,
                inicio_y + indice * (altura_botao + espacamento),
                largura_botao,
                altura_botao
            )

            self.botoes.append(rect)

            selecionado = indice == self.selecionado

            cor_fundo = (
                (75, 105, 155)
                if selecionado
                else (48, 52, 65)
            )

            pygame.draw.rect(
                tela,
                cor_fundo,
                rect,
                border_radius=8
            )

            pygame.draw.rect(
                tela,
                (150, 155, 175),
                rect,
                width=2,
                border_radius=8
            )

            texto = self.fonte_botao.render(
                opcao,
                True,
                (255, 255, 255)
            )

            tela.blit(
                texto,
                texto.get_rect(center=rect.center)
            )

    def desenhar_controles(self, tela):
        largura, altura = tela.get_size()

        tela.fill((22, 24, 32))

        titulo = self.fonte_titulo.render(
            "CONTROLES",
            True,
            (240, 240, 245)
        )

        tela.blit(
            titulo,
            titulo.get_rect(
                center=(largura // 2, altura // 4)
            )
        )

        controles = [
            "W / A / S / D - Movimentar",
            "E - Minerar / Interagir",
            "I - Abrir inventario",
            "ESC - Pausar o jogo",
            "Mouse - Interagir com interfaces"
        ]

        fonte = pygame.font.Font(None, 32)

        for indice, controle in enumerate(controles):
            texto = fonte.render(
                controle,
                True,
                (220, 220, 225)
            )

            tela.blit(
                texto,
                texto.get_rect(
                    center=(
                        largura // 2,
                        altura // 2 + indice * 45
                    )
                )
            )

        instrucao = fonte.render(
            "ESC - Voltar",
            True,
            (160, 170, 190)
        )

        tela.blit(
            instrucao,
            instrucao.get_rect(
                center=(largura // 2, altura - 100)
            )
        )
