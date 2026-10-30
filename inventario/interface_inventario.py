
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

    TEMPO_CLIQUE_DUPLO = 350

    def __init__(self):
        self.catalogo = CatalogoItens()
        self.aberto = False
        self.fonte = pygame.font.Font(None, 24)
        self.fonte_pequena = pygame.font.Font(None, 20)

        self.slot_rects = []
        self.botao_descartar_rect = None

        self.slot_selecionado = None
        self.posicao_mouse = (0, 0)

        # Estado do arraste.
        self.slot_pressionado = None
        self.slot_arrastado = None
        self.mouse_pressionado = False
        self.arrastando = False
        self.posicao_inicio_arraste = None
        self.LIMITE_ARRASTE = 6

        self.ultimo_clique_slot = None
        self.tempo_ultimo_clique = 0

        self.quantidade_descartar = None
        self.modal_rect = None
        self.botao_menos = None
        self.botao_mais = None
        self.botao_confirmar = None
        self.botao_cancelar = None

    def tratar_evento(self, evento, inventario):
        if not self.aberto:
            return

        if evento.type == pygame.MOUSEMOTION:
            self.posicao_mouse = evento.pos

            if self.mouse_pressionado and self.slot_pressionado is not None:
                inicio_x, inicio_y = self.posicao_inicio_arraste
                atual_x, atual_y = evento.pos

                distancia = (
                    (atual_x - inicio_x) ** 2
                    + (atual_y - inicio_y) ** 2
                ) ** 0.5

                if distancia >= self.LIMITE_ARRASTE:
                    self.arrastando = True
                    self.slot_arrastado = self.slot_pressionado

            return

        if evento.type not in (
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP
        ):
            return

        if evento.button != 1:
            return

        self.posicao_mouse = evento.pos

        if evento.type == pygame.MOUSEBUTTONDOWN:
            if self.quantidade_descartar is not None:
                if self.botao_menos and self.botao_menos.collidepoint(evento.pos):
                    self.quantidade_descartar = max(
                        1, self.quantidade_descartar - 1
                    )

                elif self.botao_mais and self.botao_mais.collidepoint(evento.pos):
                    item = inventario.slots[self.slot_selecionado]

                    if item:
                        self.quantidade_descartar = min(
                            item["quantidade"],
                            self.quantidade_descartar + 1
                        )

                elif self.botao_confirmar and self.botao_confirmar.collidepoint(evento.pos):
                    inventario.descartar(
                        self.slot_selecionado,
                        self.quantidade_descartar
                    )
                    self._fechar_modal()

                elif self.botao_cancelar and self.botao_cancelar.collidepoint(evento.pos):
                    self._fechar_modal()

                elif self.modal_rect and not self.modal_rect.collidepoint(evento.pos):
                    self._fechar_modal()

                return

            if (
                self.slot_selecionado is not None
                and self.botao_descartar_rect
                and self.botao_descartar_rect.collidepoint(evento.pos)
            ):
                self._abrir_modal(inventario)
                return

            for indice, rect in enumerate(self.slot_rects):
                if rect.collidepoint(evento.pos):
                    self.slot_pressionado = indice
                    self.posicao_inicio_arraste = evento.pos
                    self.mouse_pressionado = True
                    return

        if evento.type == pygame.MOUSEBUTTONUP:
            if not self.mouse_pressionado:
                return

            origem = self.slot_pressionado
            arrastou = self.arrastando

            self.mouse_pressionado = False
            self.slot_pressionado = None
            self.posicao_inicio_arraste = None
            self.arrastando = False
            self.slot_arrastado = None

            if origem is None:
                return

            if (
                arrastou
                and self.botao_descartar_rect
                and self.botao_descartar_rect.collidepoint(evento.pos)
            ):
                self.slot_selecionado = origem
                self._abrir_modal(inventario)
                return

            if arrastou:
                for indice, rect in enumerate(self.slot_rects):
                    if rect.collidepoint(evento.pos):
                        if indice != origem:
                            inventario.mover(origem, indice)

                        self.slot_selecionado = None
                        self.ultimo_clique_slot = None
                        return

                return

            if (
                self.slot_selecionado is not None
                and self.botao_descartar_rect
                and self.botao_descartar_rect.collidepoint(evento.pos)
            ):
                self._abrir_modal(inventario)
                return

            for indice, rect in enumerate(self.slot_rects):
                if not rect.collidepoint(evento.pos):
                    continue

                item = inventario.slots[indice]

                if self.slot_selecionado is not None:
                    origem_selecionada = self.slot_selecionado

                    if indice != origem_selecionada:
                        inventario.mover(origem_selecionada, indice)

                    self.slot_selecionado = None
                    self.ultimo_clique_slot = None
                    return

                if item is None:
                    self.ultimo_clique_slot = None
                    return

                tempo_atual = pygame.time.get_ticks()

                clique_duplo = (
                    self.ultimo_clique_slot == indice
                    and tempo_atual - self.tempo_ultimo_clique
                    <= self.TEMPO_CLIQUE_DUPLO
                )

                if clique_duplo:
                    self.slot_selecionado = indice
                    self.ultimo_clique_slot = None
                else:
                    self.ultimo_clique_slot = indice
                    self.tempo_ultimo_clique = tempo_atual

                return


    def _abrir_modal(self, inventario):
        if self.slot_selecionado is None:
            return

        item = inventario.slots[self.slot_selecionado]

        if item is None:
            self.slot_selecionado = None
            return

        self.quantidade_descartar = item["quantidade"]

    def _fechar_modal(self):
        self.quantidade_descartar = None
        self.slot_selecionado = None

    def alternar(self):
        self.aberto = not self.aberto

        if not self.aberto:
            self.slot_selecionado = None
            self.ultimo_clique_slot = None
            self._fechar_modal()

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

            # Destaque do item selecionado.
            if indice == self.slot_selecionado:
                pygame.draw.rect(
                    tela,
                    self.COR_DESTAQUE,
                    slot_rect,
                    width=2,
                    border_radius=5
                )

            if item is not None and indice != self.slot_arrastado:
                self._desenhar_item(
                    tela, item, x, y, tamanho=32
                )

        # Desenha o item acompanhado pelo mouse.
        if self.arrastando and self.slot_arrastado is not None:
            item = inventario.slots[self.slot_arrastado]

            if item is not None:
                mouse_x, mouse_y = self.posicao_mouse

                self._desenhar_item(
                    tela,
                    item,
                    mouse_x - self.TAMANHO_SLOT // 2,
                    mouse_y - self.TAMANHO_SLOT // 2,
                    tamanho=32
                )

        # Botão de descarte.
        self.botao_descartar_rect = pygame.Rect(
            painel.right - 58,
            painel.bottom - 48,
            38,
            38,
        )

        pygame.draw.rect(
            tela,
            self.COR_DESCARTAR,
            self.botao_descartar_rect,
            border_radius=8,
        )

        # Ícone de lixeira.
        x = self.botao_descartar_rect.x
        y = self.botao_descartar_rect.y

        pygame.draw.line(
            tela, self.COR_TEXTO,
            (x + 9, y + 11), (x + 29, y + 11), 2
        )

        pygame.draw.line(
            tela, self.COR_TEXTO,
            (x + 15, y + 8), (x + 23, y + 8), 2
        )

        pygame.draw.polygon(
            tela,
            self.COR_TEXTO,
            [
                (x + 12, y + 14),
                (x + 26, y + 14),
                (x + 24, y + 29),
                (x + 14, y + 29),
            ],
            width=2,
        )

        pygame.draw.line(
            tela, self.COR_TEXTO,
            (x + 17, y + 17), (x + 17, y + 26), 2
        )

        pygame.draw.line(
            tela, self.COR_TEXTO,
            (x + 21, y + 17), (x + 21, y + 26), 2
        )

        # Modal de descarte.
        if self.quantidade_descartar is not None:
            self._desenhar_modal(tela, inventario)

    def _desenhar_modal(self, tela, inventario):
        largura, altura = 300, 170

        self.modal_rect = pygame.Rect(
            (tela.get_width() - largura) // 2,
            (tela.get_height() - altura) // 2,
            largura,
            altura,
        )

        pygame.draw.rect(
            tela, (20, 20, 25), self.modal_rect, border_radius=10
        )

        pygame.draw.rect(
            tela, self.COR_BORDA, self.modal_rect,
            width=2, border_radius=10
        )

        if self.slot_selecionado is None:
            self._fechar_modal()
            return

        item = inventario.slots[self.slot_selecionado]

        if item is None:
            self._fechar_modal()
            return

        titulo = self.fonte.render(
            "Quanto deseja descartar?", True, self.COR_TEXTO
        )

        tela.blit(
            titulo,
            titulo.get_rect(
                center=(self.modal_rect.centerx, self.modal_rect.y + 30)
            ),
        )

        self.botao_menos = pygame.Rect(
            self.modal_rect.x + 35,
            self.modal_rect.y + 65,
            40,
            32
        )

        self.botao_mais = pygame.Rect(
            self.modal_rect.right - 75,
            self.modal_rect.y + 65,
            40,
            32
        )

        for rect, simbolo in (
            (self.botao_menos, "-"),
            (self.botao_mais, "+"),
        ):
            pygame.draw.rect(
                tela, self.COR_SLOT, rect, border_radius=5
            )

            texto = self.fonte.render(
                simbolo, True, self.COR_TEXTO
            )

            tela.blit(
                texto, texto.get_rect(center=rect.center)
            )

        quantidade = self.fonte.render(
            str(self.quantidade_descartar),
            True,
            self.COR_DESTAQUE
        )

        tela.blit(
            quantidade,
            quantidade.get_rect(
                center=(
                    self.modal_rect.centerx,
                    self.modal_rect.y + 81
                )
            ),
        )

        self.botao_confirmar = pygame.Rect(
            self.modal_rect.x + 25,
            self.modal_rect.bottom - 45,
            115,
            30
        )

        self.botao_cancelar = pygame.Rect(
            self.modal_rect.right - 140,
            self.modal_rect.bottom - 45,
            115,
            30
        )

        for rect, texto, cor in (
            (self.botao_confirmar, "Confirmar", self.COR_DESCARTAR),
            (self.botao_cancelar, "Cancelar", self.COR_SLOT),
        ):
            pygame.draw.rect(
                tela, cor, rect, border_radius=5
            )

            render = self.fonte_pequena.render(
                texto, True, self.COR_TEXTO
            )

            tela.blit(
                render, render.get_rect(center=rect.center)
            )

    def _desenhar_item(self, tela, item, x, y, tamanho=32):
        dados_item = self.catalogo.obter(item["tipo"])

        if dados_item is None:
            return

        cor = dados_item.get("cor", (200, 200, 200))

        centro = (
            x + self.TAMANHO_SLOT // 2,
            y + self.TAMANHO_SLOT // 2
        )

        pygame.draw.rect(
            tela,
            cor,
            pygame.Rect(
                centro[0] - tamanho // 2,
                centro[1] - tamanho // 2,
                tamanho,
                tamanho
            ),
            border_radius=5
        )

        quantidade = self.fonte_pequena.render(
            str(item["quantidade"]),
            True,
            self.COR_TEXTO
        )

        tela.blit(
            quantidade,
            (
                x + self.TAMANHO_SLOT - quantidade.get_width() - 5,
                y + self.TAMANHO_SLOT - quantidade.get_height() - 3
            )
        )

    def _desenhar_tooltip(self, tela, item):
        dados_item = self.catalogo.obter(item["tipo"])

        if dados_item is None:
            return

        texto = self.fonte_pequena.render(
            dados_item["nome"],
            True,
            self.COR_TEXTO
        )

        largura = texto.get_width() + 16
        altura = texto.get_height() + 12

        mouse_x, mouse_y = pygame.mouse.get_pos()

        tooltip = pygame.Rect(
            mouse_x + 12,
            mouse_y + 12,
            largura,
            altura
        )

        if tooltip.right > tela.get_width():
            tooltip.right = tela.get_width() - 5

        if tooltip.bottom > tela.get_height():
            tooltip.bottom = tela.get_height() - 5

        pygame.draw.rect(
            tela, (25, 25, 30), tooltip, border_radius=5
        )

        pygame.draw.rect(
            tela, self.COR_BORDA, tooltip,
            width=1, border_radius=5
        )

        tela.blit(
            texto,
            (tooltip.x + 8, tooltip.y + 6)
        )
