import pygame
import sys

from mapa.mapa import Mapa
from mapa.camera import Camera
from personagens.jogador import Jogador
from acoes.movimentacao import Movimentacao
from acoes.mineracao import Mineracao
from acoes.spawn_minerios import SpawnMinerios
from acoes.crafting import Crafting

from inventario.inventario import Inventario
from inventario.interface_inventario import InterfaceInventario
from inventario.interface_crafting import InterfaceCrafting

from sistemas.tutorial import Tutorial
from sistemas.gerenciador_jogo import GerenciadorJogo

from interface.interface_menu import InterfaceMenu


def criar_partida():
    mapa = Mapa()
    spawn = mapa.spawn_jogador

    jogador = Jogador(
        spawn["x"],
        spawn["y"]
    )

    tutorial = Tutorial()
    spawn = SpawnMinerios(mapa)
    superficie = pygame.display.get_surface()
    camera = Camera(*superficie.get_size())

    interface_inventario = InterfaceInventario()
    interface_crafting = InterfaceCrafting()

    inventario = Inventario(
        interface_inventario.COLUNAS
        * interface_inventario.LINHAS
    )

    mineracao = Mineracao(inventario)
    crafting = Crafting(mapa, inventario)

    return {
        "mapa": mapa,
        "camera": camera,
        "jogador": jogador,
        "tutorial": tutorial,
        "spawn": spawn,
        "interface_inventario": interface_inventario,
        "interface_crafting": interface_crafting,
        "inventario": inventario,
        "mineracao": mineracao,
        "crafting": crafting
    }


def main():
    pygame.init()

    informacoes_tela = pygame.display.Info()
    LARGURA = min(1280, informacoes_tela.current_w)
    ALTURA = min(720, informacoes_tela.current_h)
    FPS = 60

    tela = pygame.display.set_mode(
        (LARGURA, ALTURA), pygame.RESIZABLE
    )
    pygame.display.set_caption("SimpSmith")

    relogio = pygame.time.Clock()

    menu = InterfaceMenu()
    gerenciador = GerenciadorJogo()

    opcoes_principais = [
        "Novo jogo",
        "Controles",
        "Sair"
    ]

    opcoes_pausa = [
        "Continuar",
        "Controles",
        "Menu principal",
        "Sair do jogo"
    ]

    while gerenciador.executando:
        dt = min(relogio.tick(FPS) / 1000, 0.05)

        for evento in pygame.event.get():

            if evento.type == pygame.VIDEORESIZE:
                tela = pygame.display.set_mode(
                    (evento.w, evento.h), pygame.RESIZABLE
                )
                if gerenciador.estado == "jogo":
                    gerenciador.partida["camera"].redimensionar(
                        *tela.get_size()
                    )
                continue

            if evento.type == pygame.QUIT:
                gerenciador.executando = False
                continue

            if gerenciador.estado == "menu":

                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    gerenciador.executando = False
                    continue

                acao = menu.tratar_evento(
                    evento, opcoes_principais
                )

                if acao is not None:
                    gerenciador.processar_opcao(
                        acao, criar_partida
                    )

                    if acao == "Novo jogo":
                        menu.selecionado = 0

            elif gerenciador.estado == "pausa":

                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    gerenciador.pausar()
                    gerenciador.estado = "jogo"
                    continue

                acao = menu.tratar_evento(
                    evento, opcoes_pausa
                )

                if acao is not None:
                    gerenciador.processar_opcao(
                        acao, criar_partida
                    )

                    if acao == "Menu principal":
                        menu.selecionado = 0

            elif gerenciador.estado == "controles":

                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    gerenciador.voltar_dos_controles()
                    continue

            elif gerenciador.estado == "jogo":

                crafting = gerenciador.partida["crafting"]
                interface_crafting = gerenciador.partida["interface_crafting"]
                interface_inventario = gerenciador.partida["interface_inventario"]

                if evento.type == pygame.KEYDOWN:

                    if evento.key == pygame.K_ESCAPE:

                        if crafting.aberto:
                            crafting.tratar_evento(
                                evento, interface_crafting
                            )

                        elif interface_inventario.aberto:
                            interface_inventario.alternar()

                        else:
                            gerenciador.pausar()
                            menu.selecionado = 0

                        continue

                    if (
                        evento.key == pygame.K_i
                        and not interface_crafting.aberto
                    ):
                        interface_inventario.alternar()
                        continue

                interface_inventario.tratar_evento(
                    evento, gerenciador.partida["inventario"]
                )

                crafting.tratar_evento(
                    evento, interface_crafting
                )

        if gerenciador.estado == "jogo":

            partida = gerenciador.partida

            mapa = partida["mapa"]
            jogador = partida["jogador"]
            camera = partida["camera"]
            spawn = partida["spawn"]
            inventario = partida["inventario"]
            mineracao = partida["mineracao"]
            crafting = partida["crafting"]

            interface_inventario = partida["interface_inventario"]
            interface_crafting = partida["interface_crafting"]

            crafting.atualizar(jogador)

            interface_aberta = (
                interface_inventario.aberto
                or interface_crafting.aberto
            )

            spawn.atualizar(dt, jogador)

            if not interface_aberta:

                mineracao.atualizar(
                    dt, jogador, spawn
                )

                if mineracao.alvo is None:
                    Movimentacao.atualizar(
                        jogador,
                        mapa,
                        dt,
                        spawn.minerios,
                        inventario,
                        objetos=mapa.objetos
                    )

            else:
                jogador.andando = False
                mineracao._cancelar()

            partida["tutorial"].atualizar(
                mineracao, interface_inventario
            )

            camera.atualizar(
                jogador.rect,
                mapa.largura_referencia,
                mapa.altura_referencia
            )

            mapa.desenhar(tela, camera)
            spawn.desenhar(tela, camera)
            jogador.desenhar(tela, camera)
            mineracao.desenhar(tela)

            interface_inventario.desenhar(
                tela, inventario
            )

            interface_crafting.desenhar(tela)

            partida["tutorial"].desenhar(tela)

        elif gerenciador.estado == "menu":

            menu.desenhar(
                tela,
                "SIMPSMITH",
                opcoes_principais
            )

        elif gerenciador.estado == "pausa":

            menu.desenhar(
                tela,
                "JOGO PAUSADO",
                opcoes_pausa,
                sobreposicao=True
            )

        elif gerenciador.estado == "controles":

            menu.desenhar_controles(tela)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()


