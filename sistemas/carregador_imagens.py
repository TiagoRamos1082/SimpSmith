from pathlib import Path

import pygame


RAIZ_PROJETO = Path(__file__).resolve().parent.parent

_cache_originais = {}
_cache_redimensionadas = {}


def carregar_imagem(caminho):
    if not caminho:
        return None

    arquivo = (RAIZ_PROJETO / caminho).resolve()

    if not arquivo.is_file():
        return None

    chave = str(arquivo)

    if chave not in _cache_originais:
        try:
            imagem = pygame.image.load(chave)

            if pygame.display.get_surface() is not None:
                imagem = imagem.convert_alpha()

            _cache_originais[chave] = imagem

        except (pygame.error, OSError):
            return None

    return _cache_originais[chave]


def obter_imagem(caminho, tamanho):
    imagem = carregar_imagem(caminho)

    if imagem is None:
        return None

    largura_maxima, altura_maxima = tamanho

    if largura_maxima <= 0 or altura_maxima <= 0:
        return None

    chave = (
        str((RAIZ_PROJETO / caminho).resolve()),
        largura_maxima,
        altura_maxima,
    )

    if chave not in _cache_redimensionadas:
        largura, altura = imagem.get_size()

        escala = min(
            largura_maxima / largura,
            altura_maxima / altura,
        )

        nova_largura = max(1, round(largura * escala))
        nova_altura = max(1, round(altura * escala))

        redimensionada = pygame.transform.smoothscale(
            imagem,
            (nova_largura, nova_altura),
        )

        _cache_redimensionadas[chave] = redimensionada

    return _cache_redimensionadas[chave]
