
import os
import pygame


class Tutorial:
    ETAPAS = [
        {
            "titulo": "E para interagir",
            "descricao": "Aproxime-se de um minério e pressione E para minerar.",
            "imagem": "interagir.png",
        },
        {
            "titulo": "I para abrir o inventario",
            "descricao": "Pressione I para abrir seu inventario.",
            "imagem": "inventario.png",
        },
        {
            "titulo": "I para fechar o inventario",
            "descricao": "Pressione I novamente para fechar o inventario.",
            "imagem": "inventario.png",
        },
    ]

    def __init__(self):
        self.etapa_atual = 0

        self.fonte_titulo = pygame.font.Font(None, 38)
        self.fonte_descricao = pygame.font.Font(None, 26)

        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.pasta_imagens = os.path.join(raiz, "imagens", "tutorial")

        self.imagem_atual = None
        self._carregar_imagem()

    @property
    def concluido(self):
        return self.etapa_atual >= len(self.ETAPAS)

    def atualizar(self, mineracao, interface_inventario):
        if self.concluido:
            return

        # Etapa 1: o jogador começou a minerar.
        if self.etapa_atual == 0:
            if mineracao.coleta_concluida:
                self.etapa_atual = 1
                self._carregar_imagem()

        # Etapa 2: abriu o inventario.
        elif self.etapa_atual == 1:
            if interface_inventario.aberto:
                self.etapa_atual = 2
                self._carregar_imagem()

        # Etapa 3: fechou o inventario.
        elif self.etapa_atual == 2:
            if not interface_inventario.aberto:
                self.etapa_atual = 3
                self._carregar_imagem()

    def _carregar_imagem(self):
        self.imagem_atual = None

        if self.concluido:
            return

        nome = self.ETAPAS[self.etapa_atual]["imagem"]
        caminho = os.path.join(self.pasta_imagens, nome)

        if os.path.isfile(caminho):
            self.imagem_atual = pygame.image.load(caminho).convert_alpha()
            self.imagem_atual = pygame.transform.smoothscale(
                self.imagem_atual, (150, 150)
            )

    def desenhar(self, tela):
        if self.concluido:
            return

        etapa = self.ETAPAS[self.etapa_atual]

        largura = 560
        altura = 220
        margem = 25

        painel = pygame.Rect(
            tela.get_width() - largura - margem,
            margem,
            largura,
            altura,
        )

        # Fundo semitransparente.
        fundo = pygame.Surface(
            (painel.width, painel.height),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            fundo,
            (30, 30, 38, 110),
            fundo.get_rect(),
            border_radius=12
        )

        tela.blit(fundo, painel.topleft)

        # Borda.
        pygame.draw.rect(
            tela,
            (180, 180, 190),
            painel,
            width=2,
            border_radius=12
        )

        # Título.
        titulo = self.fonte_titulo.render(
            etapa["titulo"],
            True,
            (255, 220, 100)
        )

        tela.blit(
            titulo,
            (painel.x + 25, painel.y + 25)
        )

        # Descrição.
        descricao = self.fonte_descricao.render(
            etapa["descricao"],
            True,
            (255, 255, 255)
        )

        tela.blit(
            descricao,
            (painel.x + 25, painel.y + 85)
        )

        # Imagem ilustrativa.
        if self.imagem_atual is not None:
            tela.blit(
                self.imagem_atual,
                (painel.right - 170, painel.y + 55)
            )

        # Progresso.
        progresso = self.fonte_descricao.render(
            f"Etapa {self.etapa_atual + 1} de {len(self.ETAPAS)}",
            True,
            (180, 180, 180)
        )

        tela.blit(
            progresso,
            (painel.x + 25, painel.bottom - 40)
        )