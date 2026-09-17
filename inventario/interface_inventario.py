
import pygame
from sistemas.catalogo_itens import CatalogoItens

class InterfaceInventario:
    COLUNAS = 4
    LINHAS = 3
    TAMANHO_SLOT = 64
    ESPACO = 8

    COR_FUNDO = (30, 30, 35)
    COR_SLOT = (65, 65, 75)
    COR_BORDA = (150, 150, 160)
    COR_TEXTO = (255, 255, 255)
    COR_DESTAQUE = (255, 220, 100)
    COR_DESCARTAR = (170, 55, 55)

    CORES_MINERIOS = {
        "ferro": (150, 150, 150),
        "ouro": (255, 210, 0),
        "cobre": (220, 115, 45),
    }

    def __init__(self):
        self.catalogo = CatalogoItens()
        self.aberto = False
        self.fonte = pygame.font.Font(None, 24)
        self.fonte_pequena = pygame.font.Font(None, 20)

        self.slot_rects = []
        self.botao_descartar_rect = None

        self.slot_selecionado = None
        self.arrastando = False
        self.posicao_mouse = (0, 0)

    def tratar_evento(self, evento, inventario):
        if not self.aberto:
            return

        if evento.type == pygame.MOUSEMOTION:
            self.posicao_mouse = evento.pos

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            self.posicao_mouse = evento.pos

            if evento.button == 1:
                for indice, rect in enumerate(self.slot_rects):
                    if rect.collidepoint(evento.pos):
                        if inventario.slots[indice] is not None:
                            self.slot_selecionado = indice
                            self.arrastando = True
                        return

        elif evento.type == pygame.MOUSEBUTTONUP:
            self.posicao_mouse = evento.pos

            if evento.button != 1:
                return

            if not self.arrastando or self.slot_selecionado is None:
                return

            origem = self.slot_selecionado
            destino = None

            # Só descarta pelo botão de descarte.
            if (
                self.botao_descartar_rect is not None
                and self.botao_descartar_rect.collidepoint(evento.pos)
            ):
                inventario.descartar(origem)

            else:
                # Move somente quando soltar sobre outro slot.
                for indice, rect in enumerate(self.slot_rects):
                    if rect.collidepoint(evento.pos):
                        destino = indice
                        break

                if destino is not None and destino != origem:
                    inventario.mover(origem, destino)

                # Fora dos slots, o item permanece na origem.

            self.slot_selecionado = None
            self.arrastando = False

    def alternar(self):
        self.aberto = not self.aberto

        if not self.aberto:
            self.slot_selecionado = None
            self.arrastando = False

    def desenhar(self, tela, inventario):
        if not self.aberto:
            return

        largura_grade = (
            self.COLUNAS * self.TAMANHO_SLOT
            + (self.COLUNAS - 1) * self.ESPACO
        )

        altura_grade = (
            self.LINHAS * self.TAMANHO_SLOT
            + (self.LINHAS - 1) * self.ESPACO
        )

        largura_painel = largura_grade + 40
        altura_painel = altura_grade + 100

        painel = pygame.Rect(
            (tela.get_width() - largura_painel) // 2,
            (tela.get_height() - altura_painel) // 2,
            largura_painel,
            altura_painel,
        )

        pygame.draw.rect(
            tela, self.COR_FUNDO, painel, border_radius=10
        )
        pygame.draw.rect(
            tela, self.COR_BORDA, painel,
            width=2, border_radius=10
        )

        titulo = self.fonte.render(
            "INVENTARIO", True, self.COR_TEXTO
        )
        tela.blit(titulo, (painel.x + 20, painel.y + 15))

        inicio_x = painel.x + 20
        inicio_y = painel.y + 50

        self.slot_rects = []

        for indice, item in enumerate(inventario.slots):
            coluna = indice % self.COLUNAS
            linha = indice // self.COLUNAS

            x = inicio_x + coluna * (
                self.TAMANHO_SLOT + self.ESPACO
            )
            y = inicio_y + linha * (
                self.TAMANHO_SLOT + self.ESPACO
            )

            slot_rect = pygame.Rect(
                x, y, self.TAMANHO_SLOT, self.TAMANHO_SLOT
            )
            self.slot_rects.append(slot_rect)

            pygame.draw.rect(
                tela, self.COR_SLOT, slot_rect, border_radius=5
            )

            pygame.draw.rect(
                tela, self.COR_BORDA, slot_rect,
                width=1, border_radius=5
            )

            if item is not None:
                # Esconde o ícone original durante o arraste.
                if (
                    self.arrastando
                    and indice == self.slot_selecionado
                ):
                    continue

                self._desenhar_item(
                    tela, item, x, y, tamanho=32
                )

        # Botão de descarte.
        self.botao_descartar_rect = pygame.Rect(
            painel.x + 20,
            painel.bottom - 45,
            130,
            28,
        )

        pygame.draw.rect(
            tela,
            self.COR_DESCARTAR,
            self.botao_descartar_rect,
            border_radius=5,
        )

        texto_descartar = self.fonte_pequena.render(
            "Descartar item",
            True,
            self.COR_TEXTO,
        )

        tela.blit(
            texto_descartar,
            texto_descartar.get_rect(
                center=self.botao_descartar_rect.center
            ),
        )

        # Peso do inventário.
        peso = inventario.peso_total

        cor_peso = (
            (255, 70, 70)
            if inventario.sobrecarregado
            else self.COR_TEXTO
        )

        texto_peso = self.fonte_pequena.render(
            f"Peso: {peso:.1f} / "
            f"{inventario.PESO_MAXIMO:.1f} kg",
            True,
            cor_peso,
        )

        tela.blit(
            texto_peso,
            (painel.x + 160, painel.bottom - 40),
        )

        # Desenha o item maior, acompanhando o mouse.
        if (
            self.arrastando
            and self.slot_selecionado is not None
        ):
            item = inventario.slots[self.slot_selecionado]

            if item is not None:
                mouse_x, mouse_y = self.posicao_mouse
                tamanho = 44

                x = mouse_x - tamanho // 2
                y = mouse_y - tamanho // 2

                self._desenhar_item(
                    tela, item, x, y, tamanho=tamanho
                )

   
    def _desenhar_item(self, tela, item, x, y, tamanho):
        dados_item = self.catalogo.obter(item["tipo"])

        if dados_item:
            cor = tuple(dados_item["cor"])
        else:
            cor = self.CORES_MINERIOS.get(
                item["tipo"], (180, 180, 180)
            )

        # Centraliza o ícone horizontal e verticalmente.
        icone = pygame.Rect(
            x + (self.TAMANHO_SLOT - tamanho) // 2,
            y + (self.TAMANHO_SLOT - tamanho) // 2,
            tamanho,
            tamanho,
        )

        pygame.draw.rect(
            tela, cor, icone, border_radius=5
        )

        pygame.draw.rect(
            tela, (25, 25, 25), icone,
            width=2, border_radius=5
        )

        quantidade = self.fonte_pequena.render(
            str(item["quantidade"]),
            True,
            self.COR_TEXTO,
        )

        # Quantidade no canto inferior direito do slot.
        tela.blit(
            quantidade,
            (
                x + self.TAMANHO_SLOT
                - quantidade.get_width() - 5,
                y + self.TAMANHO_SLOT
                - quantidade.get_height() - 3,
            ),
        )
