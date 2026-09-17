
import pygame
from pathlib import Path


class Personagem:
    def __init__(self, x, y, velocidade=150):
        self.x = float(x)
        self.y = float(y)
        self.velocidade = velocidade

        # Dimensões do personagem
        self.largura = 32
        self.altura = 40

        # Estado
        self.direcao = "down"
        self.andando = False

        # Animação
        self.tempo_animacao = 0
        self.velocidade_animacao = 8

        # Carrega os sprites
        self.sprites = self._carregar_sprites()

    def _carregar_sprites(self):
        pasta = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "player"
        )

        arquivos = {
            "up": "playerUp.png",
            "down": "playerDown.png",
            "left": "playerLeft.png",
            "right": "playerRight.png",
        }

        sprites = {}

        for direcao, arquivo in arquivos.items():
            caminho = pasta / arquivo

            if not caminho.exists():
                raise FileNotFoundError(
                    f"Sprite não encontrado: {caminho}"
                )

            sheet = pygame.image.load(
                str(caminho)
            ).convert_alpha()

            largura_sheet, altura_sheet = sheet.get_size()

            if largura_sheet % 4 != 0:
                raise ValueError(
                    f"{arquivo} precisa conter 4 frames "
                    "horizontais de mesma largura."
                )

            frame_largura = largura_sheet // 4
            frame_altura = altura_sheet

            frames = []

            for i in range(4):
                # Recorta um frame da spritesheet.
                frame = sheet.subsurface(
                    pygame.Rect(
                        i * frame_largura,
                        0,
                        frame_largura,
                        frame_altura
                    )
                ).copy()

                # Encontra os pixels visíveis.
                limites = frame.get_bounding_rect()

                canvas = pygame.Surface(
                    (self.largura, self.altura),
                    pygame.SRCALPHA
                )

                if limites.width > 0 and limites.height > 0:
                    sprite = frame.subsurface(
                        limites
                    ).copy()

                    # Redimensiona sem deformar o sprite.
                    escala = min(
                        self.largura / sprite.get_width(),
                        self.altura / sprite.get_height()
                    )

                    nova_largura = max(
                        1,
                        round(sprite.get_width() * escala)
                    )

                    nova_altura = max(
                        1,
                        round(sprite.get_height() * escala)
                    )

                    sprite = pygame.transform.scale(
                        sprite,
                        (nova_largura, nova_altura)
                    )

                    # Centraliza horizontalmente.
                    pos_x = (
                        self.largura - nova_largura
                    ) // 2

                    # Alinha pela base dos pés.
                    pos_y = (
                        self.altura - nova_altura
                    )

                    canvas.blit(
                        sprite,
                        (pos_x, pos_y)
                    )

                frames.append(canvas)

            sprites[direcao] = frames

        return sprites

    @property
    def rect(self):
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.largura,
            self.altura
        )

    def atualizar_animacao(self, dt):
        if self.andando:
            self.tempo_animacao += dt
        else:
            self.tempo_animacao = 0

    def desenhar(self, tela):
        frames = self.sprites[self.direcao]

        if self.andando:
            indice = int(
                self.tempo_animacao
                * self.velocidade_animacao
            ) % len(frames)
        else:
            indice = 0

        sprite = frames[indice]

        x = round(self.x)
        y = round(self.y)

        # Desenha o sprite.
        tela.blit(sprite, (x, y))

        # # BORDA DE TESTE: área total do personagem.
        # pygame.draw.rect(
        #     tela,
        #     (255, 0, 255),
        #     (x, y, self.largura, self.altura),
        #     1
        # )

        # # LINHA AMARELA: centro horizontal.
        # pygame.draw.line(
        #     tela,
        #     (255, 255, 0),
        #     (x + self.largura // 2, y),
        #     (
        #         x + self.largura // 2,
        #         y + self.altura - 1
        #     ),
        #     1
        # )

        # # LINHA CIANO: base dos pés.
        # pygame.draw.line(
        #     tela,
        #     (0, 255, 255),
        #     (x, y + self.altura - 1),
        #     (
        #         x + self.largura - 1,
        #         y + self.altura - 1
        #     ),
        #     1
        # )
