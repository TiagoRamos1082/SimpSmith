
import pygame


class Colisao:
    @staticmethod
    def pode_mover(personagem, novo_x, novo_y, mapa, minerios=None, objetos=None):
        rect = pygame.Rect(
            round(novo_x) + 7,
            round(novo_y) + 5,
            personagem.largura - 14,
            personagem.altura - 7
        )

        if mapa.colide_com_obstaculo(rect):
            return False

        if minerios:
            for minerio in minerios:
                if getattr(minerio, "solido", True) and rect.colliderect(minerio.rect):
                    return False

        if objetos:
            for objeto in objetos:
                if getattr(objeto, "solido", True) and rect.colliderect(objeto.rect):
                    return False

        return True
