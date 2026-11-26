
import pygame


class Colisao:
    @staticmethod
    def pode_mover(personagem, novo_x, novo_y, mapa, minerios=None, objetos=None):
        obter_hitbox = getattr(personagem, "obter_rect_colisao", None)

        if callable(obter_hitbox):
            rect = obter_hitbox(novo_x, novo_y)
        else:
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
                if not getattr(minerio, "solido", True):
                    continue

                colisoes = getattr(minerio, "colisoes", None)

                # Compatibilidade com recursos/objetos antigos.
                if colisoes is None:
                    colisoes = [minerio.rect]

                if any(rect.colliderect(colisao) for colisao in colisoes):
                    return False

        if objetos:
            for objeto in objetos:
                if not getattr(objeto, "solido", True):
                    continue

                colisoes = getattr(objeto, "colisoes", None)

                if colisoes is None:
                    colisoes = [objeto.rect]

                if any(rect.colliderect(area) for area in colisoes):
                    return False

        return True
