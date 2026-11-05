
import pygame


class InterfaceCrafting:
    def __init__(self):
        self.aberto = False

        self.fonte_titulo = pygame.font.Font(None, 42)
        self.fonte_texto = pygame.font.Font(None, 28)

        self.largura = 700
        self.altura = 500

    def alternar(self):
        self.aberto = not self.aberto

    def tratar_evento(self, evento):
        if not self.aberto:
            return

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self.aberto = False

    def desenhar(self, tela):
        if not self.aberto:
            return

        largura_tela, altura_tela = tela.get_size()

        # Fundo escurecido.
        fundo = pygame.Surface(
            (largura_tela, altura_tela),
            pygame.SRCALPHA
        )
        fundo.fill((0, 0, 0, 150))
        tela.blit(fundo, (0, 0))

        painel = pygame.Rect(
            (largura_tela - self.largura) // 2,
            (altura_tela - self.altura) // 2,
            self.largura,
            self.altura
        )

        pygame.draw.rect(
            tela,
            (38, 38, 48),
            painel,
            border_radius=12
        )

        pygame.draw.rect(
            tela,
            (180, 180, 190),
            painel,
            width=2,
            border_radius=12
        )

        titulo = self.fonte_titulo.render(
            "Bancada de Crafting",
            True,
            (255, 255, 255)
        )

        tela.blit(
            titulo,
            (painel.x + 25, painel.y + 20)
        )

        texto = self.fonte_texto.render(
            "Receitas disponiveis aparecerao aqui.",
            True,
            (190, 190, 190)
        )

        tela.blit(
            texto,
            (painel.x + 25, painel.y + 100)
        )

        instrucao = self.fonte_texto.render(
            "ESC - Fechar",
            True,
            (160, 160, 160)
        )

        tela.blit(
            instrucao,
            (painel.x + 25, painel.bottom - 45)
        )
