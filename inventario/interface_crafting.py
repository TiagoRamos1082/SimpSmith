
import pygame


class InterfaceCrafting:
    def __init__(self):
        self.aberto = False

        self.fonte_titulo = pygame.font.Font(None, 42)
        self.fonte_texto = pygame.font.Font(None, 28)
        self.fonte_detalhe = pygame.font.Font(None, 23)

        self.largura = 700
        self.altura = 500

        self.receitas = []
        self.selecionada = 0
        self.mensagem = ""

    def alternar(self):
        self.aberto = not self.aberto

        if self.aberto:
            self.selecionada = 0
            self.mensagem = ""

    def configurar_receitas(self, receitas):
        self.receitas = receitas
        self.selecionada = 0

    def tratar_evento(self, evento, crafting=None):
        if not self.aberto:
            return

        if evento.type != pygame.KEYDOWN:
            return

        if evento.key == pygame.K_ESCAPE:
            self.aberto = False
            return

        if not self.receitas:
            return

        if evento.key == pygame.K_UP:
            self.selecionada = (
                self.selecionada - 1
            ) % len(self.receitas)

        elif evento.key == pygame.K_DOWN:
            self.selecionada = (
                self.selecionada + 1
            ) % len(self.receitas)

        elif evento.key == pygame.K_RETURN and crafting is not None:
            receita = self.receitas[self.selecionada]

            sucesso = crafting.fabricar(receita["id"])

            if sucesso:
                self.mensagem = "Fabricacao realizada com sucesso!"
            else:
                self.mensagem = "Materiais insuficientes ou inventario cheio."

    def desenhar(self, tela):
        if not self.aberto:
            return

        largura_tela, altura_tela = tela.get_size()

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
            "Fornalha",
            True,
            (255, 255, 255)
        )
        tela.blit(titulo, (painel.x + 25, painel.y + 20))

        if not self.receitas:
            texto = self.fonte_texto.render(
                "Nenhuma receita disponivel.",
                True,
                (190, 190, 190)
            )
            tela.blit(texto, (painel.x + 25, painel.y + 100))

        else:
            receita = self.receitas[self.selecionada]

            nome = self.fonte_texto.render(
                receita["nome"],
                True,
                (255, 210, 120)
            )
            tela.blit(nome, (painel.x + 25, painel.y + 90))

            y = painel.y + 145

            texto = self.fonte_texto.render(
                "Ingredientes:",
                True,
                (255, 255, 255)
            )
            tela.blit(texto, (painel.x + 25, y))

            y += 35

            for item, quantidade in receita["ingredientes"].items():
                linha = self.fonte_detalhe.render(
                    f"{item}: {quantidade}",
                    True,
                    (190, 190, 190)
                )
                tela.blit(linha, (painel.x + 45, y))
                y += 27

            y += 15

            texto = self.fonte_texto.render(
                "Resultado:",
                True,
                (255, 255, 255)
            )
            tela.blit(texto, (painel.x + 25, y))

            y += 35

            for item, quantidade in receita["resultado"].items():
                linha = self.fonte_detalhe.render(
                    f"{item}: {quantidade}",
                    True,
                    (150, 220, 150)
                )
                tela.blit(linha, (painel.x + 45, y))
                y += 27

            navegacao = self.fonte_detalhe.render(
                f"Receita {self.selecionada + 1}/{len(self.receitas)}",
                True,
                (190, 190, 190)
            )
            tela.blit(
                navegacao,
                (painel.right - 180, painel.y + 90)
            )

        if self.mensagem:
            mensagem = self.fonte_detalhe.render(
                self.mensagem,
                True,
                (150, 220, 150)
            )
            tela.blit(
                mensagem,
                (painel.x + 25, painel.bottom - 90)
            )

        instrucao = self.fonte_detalhe.render(
            "SETAS: Selecionar | ENTER: Fabricar | ESC: Fechar",
            True,
            (160, 160, 160)
        )
        tela.blit(
            instrucao,
            (painel.x + 25, painel.bottom - 45)
        )
