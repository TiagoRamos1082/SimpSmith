
import pygame
import math

from acoes.colisao import Colisao


class Movimentacao:
    INTERVALO_REDUCAO_VELOCIDADE = 5.0
    REDUCAO_VELOCIDADE = 0.10


    @staticmethod
    def atualizar(personagem, mapa, dt, minerios=None, inventario=None, objetos=None):
        teclas = pygame.key.get_pressed()

        dx = 0
        dy = 0

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx -= 1

        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx += 1

        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dy -= 1

        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dy += 1

        personagem.andando = dx != 0 or dy != 0

        if dx < 0:
            personagem.direcao = "left"
        elif dx > 0:
            personagem.direcao = "right"
        elif dy < 0:
            personagem.direcao = "up"
        elif dy > 0:
            personagem.direcao = "down"

        personagem.atualizar_animacao(dt)

        if not personagem.andando:
            return

        # Calcula a velocidade conforme o peso carregado.
        multiplicador = 1.0

        if inventario is not None:
            peso = inventario.peso_total

            reducoes = int(
                peso // Movimentacao.INTERVALO_REDUCAO_VELOCIDADE
            )

            multiplicador = max(
                0.0,
                1.0 - (
                    reducoes * Movimentacao.REDUCAO_VELOCIDADE
                )
            )

        velocidade = personagem.velocidade * multiplicador

        if dx != 0 and dy != 0:
            fator = 1 / math.sqrt(2)
            dx *= fator
            dy *= fator

        deslocamento_x = dx * velocidade * dt
        deslocamento_y = dy * velocidade * dt

        novo_x = personagem.x + deslocamento_x
        novo_y = personagem.y + deslocamento_y

        if Colisao.pode_mover(
            personagem, novo_x, personagem.y, mapa, minerios,
            objetos=objetos
        ):
            personagem.x = novo_x

        if Colisao.pode_mover(
            personagem, personagem.x, novo_y, mapa, minerios,
            objetos=objetos
        ):
            personagem.y = novo_y
