
import pygame
import json
from pathlib import Path


class Personagem:
    ESCALA_VISUAL = 0.85
    def __init__(self, x, y, velocidade=150):
        self.x = float(x)
        self.y = float(y)
        self.velocidade = velocidade

        # DimensÃµes do personagem
        self.configuracao = self._carregar_configuracao()

        visual = self.configuracao["visual"]
        colisao = self.configuracao["colisao"]

        self.largura = visual["largura"]
        self.altura = visual["altura"]

        self.colisao_x = colisao["x"]
        self.colisao_y = colisao["y"]
        self.colisao_largura = colisao["largura"]
        self.colisao_altura = colisao["altura"]

        # Estado
        self.direcao = "down"
        self.andando = False

        # AnimaÃ§Ã£o
        self.tempo_animacao = 0
        self.velocidade_animacao = 8

        # Carrega os sprites
        self.sprites = self._carregar_sprites()

    def _carregar_configuracao(self):
        caminho = (
            Path(__file__).resolve().parent.parent
            / "dados" / "personagens" / "jogador.json"
        )

        padrao = {
            "visual": {"largura": 32, "altura": 40},
            "colisao": {"x": 7, "y": 5, "largura": 18, "altura": 33}
        }

        try:
            with caminho.open("r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)

            visual = dados["visual"]
            colisao = dados["colisao"]

            largura = max(1, min(256, int(visual["largura"])))
            altura = max(1, min(256, int(visual["altura"])))

            hitbox_largura = max(1, min(largura, int(colisao["largura"])))
            hitbox_altura = max(1, min(altura, int(colisao["altura"])))

            hitbox_x = max(0, min(largura - hitbox_largura, int(colisao["x"])))
            hitbox_y = max(0, min(altura - hitbox_altura, int(colisao["y"])))

            return {
                "visual": {"largura": largura, "altura": altura},
                "colisao": {
                    "x": hitbox_x,
                    "y": hitbox_y,
                    "largura": hitbox_largura,
                    "altura": hitbox_altura
                }
            }

        except (OSError, ValueError, TypeError, KeyError):
            return padrao

    def _carregar_sprites(self):
        pasta = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "personagens" / "player"
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
                    f"Sprite nÃ£o encontrado: {caminho}"
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

                # Encontra os pixels visÃ­veis.
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
                    ) * self.ESCALA_VISUAL

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

                    # Alinha pela base dos pÃ©s.
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

    def obter_rect_colisao(self, x=None, y=None):
        if x is None:
            x = self.x
        if y is None:
            y = self.y

        return pygame.Rect(
            round(x) + self.colisao_x,
            round(y) + self.colisao_y,
            self.colisao_largura,
            self.colisao_altura
        )

    @property
    def rect_colisao(self):
        return self.obter_rect_colisao()

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

    def desenhar(self, tela, camera=None):
        frames = self.sprites[self.direcao]

        if self.andando:
            indice = int(
                self.tempo_animacao
                * self.velocidade_animacao
            ) % len(frames)
        else:
            indice = 0

        sprite = frames[indice]

        posicao = (round(self.x), round(self.y))

        if camera is not None:
            posicao = camera.aplicar(posicao)

        tela.blit(sprite, posicao)
