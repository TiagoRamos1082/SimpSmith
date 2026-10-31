import pygame

from mapa.mapa_tileado import MapaTileado
from mapa.camera import Camera
from personagens.jogador import Jogador
from acoes.movimentacao import Movimentacao
from sistemas.gerenciador_interacoes import GerenciadorInteracoes


def abrir_fornalha(area):
    print(f"Fornalha utilizada: {area['id']}")


pygame.init()

LARGURA_TELA = 800
ALTURA_TELA = 600

tela = pygame.display.set_mode(
    (LARGURA_TELA, ALTURA_TELA)
)

pygame.display.set_caption("SimpSmith - Teste de Intera??es")

fonte = pygame.font.Font(None, 28)

mapa = MapaTileado("dados/mapas/mapa_teste.json")
gerenciador_interacoes = GerenciadorInteracoes(mapa)

gerenciador_interacoes.registrar_acao(
    "fornalha",
    abrir_fornalha
)

largura_mundo = mapa.largura * mapa.tile_size
altura_mundo = mapa.altura * mapa.tile_size

jogador = Jogador(
    largura_mundo // 2,
    altura_mundo // 2
)

camera = Camera(LARGURA_TELA, ALTURA_TELA)

relogio = pygame.time.Clock()
executando = True

while executando:
    dt = relogio.tick(60) / 1000

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            executando = False

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_e:
                executadas = gerenciador_interacoes.interagir(
                    jogador.rect
                )

                if not executadas:
                    print("Nenhuma intera??o dispon?vel.")

    Movimentacao.atualizar(
        jogador,
        mapa,
        dt
    )

    camera.atualizar(
        jogador.rect,
        largura_mundo,
        altura_mundo
    )

    areas = gerenciador_interacoes.obter_interacoes(
        jogador.rect
    )

    tela.fill((25, 25, 25))

    mapa.desenhar(tela, camera)

    # Desenha as ?reas de intera??o para depura??o.
    for area in mapa.retangulos_interacao:
        rect = area["rect"]

        posicao_tela = camera.aplicar((rect.x, rect.y))

        rect_tela = pygame.Rect(
            posicao_tela[0],
            posicao_tela[1],
            rect.width,
            rect.height
        )

        pygame.draw.rect(
            tela,
            (255, 220, 0),
            rect_tela,
            2
        )

    jogador.desenhar(tela, camera)

    if areas:
        tipos = ", ".join(area["tipo"] for area in areas)

        mensagem = fonte.render(
            f"Pressione E para interagir: {tipos}",
            True,
            (255, 255, 255)
        )

        tela.blit(mensagem, (20, 20))

    pygame.display.flip()

pygame.quit()
