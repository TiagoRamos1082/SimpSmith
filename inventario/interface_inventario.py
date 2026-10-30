
import pygame
from sistemas.catalogo_itens import CatalogoItens


class InterfaceInventario:
    COLUNAS = 4
    LINHAS = 3
    TAMANHO_SLOT = 64
    ESPACO = 8

    COR_FUNDO = (22, 22, 28)
    COR_SLOT = (65, 65, 75)
    COR_BORDA = (150, 150, 160)
    COR_TEXTO = (255, 255, 255)
    COR_DESTAQUE = (255, 220, 100)
    COR_DESCARTAR = (170, 55, 55)

    TEMPO_CLIQUE_DUPLO = 350

    def __init__(self):
        self.catalogo = CatalogoItens()
        self.aberto = False
        self.fonte = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.fonte_pequena = pygame.font.SysFont("Segoe UI", 18)

        self.slot_rects = []
        self.botao_descartar_rect = None

        self.slot_selecionado = None
        self.posicao_mouse = (0, 0)

        # Estado do arraste.
        self.slot_pressionado = None
        self.slot_arrastado = None
        self.mouse_pressionado = False
        self.arrastando = False
        self.escala_arraste = 1.0
        self.ultimo_update_arraste = pygame.time.get_ticks()
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

        # Painel de detalhes do item.
        self.detalhe_item_indice = None
        self.detalhe_rect = None
        self.painel_detalhes_rect = None
        self.botao_fechar_detalhe = None
        self.tela_atual = 'inventario'
        self.botao_voltar_rect = None
        self.inicio_animacao = 0
        self.DURACAO_ANIMACAO = 250

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
            if self.tela_atual in ("detalhes", "fechando_detalhes"):
                if (
                    self.tela_atual == "detalhes"
                    and self.botao_voltar_rect
                    and self.botao_voltar_rect.collidepoint(evento.pos)
                ):
                    self.tela_atual = "fechando_detalhes"
                    self.inicio_animacao = pygame.time.get_ticks()
                    self.botao_voltar_rect = None

                return

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

            for indice, rect in enumerate(self.slot_rects):
                if not rect.collidepoint(evento.pos):
                    continue

                item = inventario.slots[indice]

                if item is None:
                    self.slot_selecionado = None
                    self.detalhe_item_indice = None
                    self.ultimo_clique_slot = None
                    return

                tempo_atual = pygame.time.get_ticks()

                clique_duplo = (
                    self.ultimo_clique_slot == indice
                    and tempo_atual - self.tempo_ultimo_clique
                    <= self.TEMPO_CLIQUE_DUPLO
                )

                self.slot_selecionado = indice
                self.detalhe_item_indice = indice

                if clique_duplo:
                    self.tela_atual = "detalhes"
                    self.inicio_animacao = tempo_atual
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
            self.detalhe_item_indice = None
            self.tela_atual = 'inventario'
            self.botao_voltar_rect = None
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

        mostrando_detalhes = self.tela_atual in (
            "detalhes", "fechando_detalhes"
        )

        largura_detalhes = 330
        espacamento = 12

        largura_total = largura_painel

        if mostrando_detalhes:
            largura_total += espacamento + largura_detalhes

        inicio_x = (tela.get_width() - largura_total) // 2
        inicio_y = (tela.get_height() - altura_painel) // 2

        painel = pygame.Rect(
            inicio_x,
            inicio_y,
            largura_painel,
            altura_painel
        )

        pygame.draw.rect(
            tela, self.COR_FUNDO, painel, border_radius=10
        )
        pygame.draw.rect(
            tela, self.COR_BORDA, painel,
            width=2, border_radius=10
        )

        if mostrando_detalhes:
            self.painel_detalhes_rect = pygame.Rect(
                painel.right + espacamento,
                inicio_y,
                largura_detalhes,
                altura_painel
            )
            self._desenhar_detalhes(tela, inventario)
        else:
            self.painel_detalhes_rect = None
            self.botao_voltar_rect = None


        titulo = self.fonte.render(
            "INVENTARIO", True, self.COR_TEXTO
        )

        tela.blit(
            titulo,
            titulo.get_rect(
                center=(painel.centerx, painel.y + 27)
            )
        )

        inicio_x = painel.x + 20
        inicio_y = painel.y + 50

        self.slot_rects = []
        tooltip_item = None

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
                    tela, item, x, y, tamanho=34
                )

            if (
                item is not None
                and slot_rect.collidepoint(self.posicao_mouse)
                and not self.arrastando
            ):
                tooltip_item = item

        # Anima o item ao se aproximar da lixeira.
        if self.arrastando:
            alvo = 1.0

            if (
                self.botao_descartar_rect
                and self.botao_descartar_rect.collidepoint(
                    self.posicao_mouse
                )
            ):
                alvo = 0.45

            agora = pygame.time.get_ticks()
            delta = min(
                50,
                max(0, agora - self.ultimo_update_arraste)
            )

            fator = min(1.0, delta / 100)

            self.escala_arraste += (
                alvo - self.escala_arraste
            ) * fator

            self.ultimo_update_arraste = agora

        else:
            self.escala_arraste = 1.0
            self.ultimo_update_arraste = pygame.time.get_ticks()

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
                    tamanho=max(8, round(32 * self.escala_arraste))
                )
        # Tooltip desenhado por ?ltimo, acima da grade.
        if tooltip_item is not None and not self.arrastando:
            self._desenhar_tooltip(tela, tooltip_item)

        # Modal de descarte.
        if self.quantidade_descartar is not None:
            self._desenhar_modal(tela, inventario)

    def _desenhar_detalhes(self, tela, inventario):
        indice = self.detalhe_item_indice
        painel = self.painel_detalhes_rect

        if painel is None:
            return

        if indice is None or not (0 <= indice < len(inventario.slots)):
            return

        item = inventario.slots[indice]

        if item is None:
            return

        dados = self.catalogo.obter(item["tipo"])

        if dados is None:
            return

        tempo_atual = pygame.time.get_ticks()
        progresso = min(
            1.0,
            (tempo_atual - self.inicio_animacao)
            / self.DURACAO_ANIMACAO
        )

        fechando = self.tela_atual == "fechando_detalhes"

        if fechando:
            progresso = 1 - progresso

        # Suaviza??o da anima??o.
        suavizado = progresso * progresso * (3 - 2 * progresso)

        alpha = int(255 * suavizado)
        deslocamento = int(35 * (1 - suavizado))

        camada = pygame.Surface(
            (painel.width, painel.height),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            camada,
            (*self.COR_FUNDO, 255),
            camada.get_rect(),
            border_radius=10
        )

        pygame.draw.rect(
            camada,
            (*self.COR_BORDA, 255),
            camada.get_rect(),
            width=2,
            border_radius=10
        )

        titulo = self.fonte.render(
            "DETALHES", True, self.COR_TEXTO
        )

        camada.blit(
            titulo,
            titulo.get_rect(
                center=(painel.width // 2, 27)
            )
        )

        # ?cone do item.
        icone = pygame.Rect(22, 65, 70, 70)

        pygame.draw.rect(
            camada,
            dados.get("cor", (150, 150, 150)),
            icone,
            border_radius=8
        )

        nome = self.fonte.render(
            dados["nome"], True, self.COR_DESTAQUE
        )

        camada.blit(
            nome,
            nome.get_rect(midleft=(105, icone.centery))
        )

        linhas = [
            f"Categoria: {dados['categoria'].capitalize()}",
            f"Preco base: R$ {dados.get('preco_base', 0):.2f}".replace(".", ","),
            f"Peso: {dados.get('peso', 0):.2f} kg".replace(".", ","),
            f"Tempo de coleta: {dados.get('tempo_coleta', 0):.1f} s".replace(".", ","),
            f"Quantidade: {item['quantidade']}",
        ]

        y = 165

        for linha in linhas:
            texto = self.fonte_pequena.render(
                linha, True, self.COR_TEXTO
            )

            camada.blit(
                texto,
                texto.get_rect(
                    midleft=(22, y + texto.get_height() // 2)
                )
            )

            y += 25

        # Bot?o minimalista: c?rculo vermelho com X branco.
        centro_x = painel.width - 27
        centro_y = 27
        raio = 11

        pygame.draw.circle(
            camada,
            self.COR_DESCARTAR,
            (centro_x, centro_y),
            raio
        )

        pygame.draw.line(
            camada,
            self.COR_TEXTO,
            (centro_x - 4, centro_y - 4),
            (centro_x + 4, centro_y + 4),
            2
        )

        pygame.draw.line(
            camada,
            self.COR_TEXTO,
            (centro_x + 4, centro_y - 4),
            (centro_x - 4, centro_y + 4),
            2
        )

        # ?rea de clique acompanha a posi??o animada do painel.
        posicao_x = painel.x + deslocamento

        self.botao_voltar_rect = pygame.Rect(
            posicao_x + centro_x - raio,
            painel.y + centro_y - raio,
            raio * 2,
            raio * 2
        )

        camada.set_alpha(alpha)

        tela.blit(
            camada,
            (posicao_x, painel.y)
        )

        if fechando and progresso <= 0:
            self.tela_atual = "inventario"
            self.botao_voltar_rect = None

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

        tamanho_fonte = max(8, round(13 * tamanho / 32))

        fonte_quantidade = pygame.font.SysFont(
            "Segoe UI", tamanho_fonte, bold=True
        )

        quantidade = fonte_quantidade.render(
            f"{item['quantidade']}x",
            True,
            self.COR_TEXTO
        )

        area_quantidade = quantidade.get_rect()
        area_quantidade.bottomright = (
            x + self.TAMANHO_SLOT - 4,
            y + self.TAMANHO_SLOT - 4
        )

        fundo_quantidade = pygame.Surface(
            (area_quantidade.width + 8, area_quantidade.height + 4),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            fundo_quantidade,
            (15, 15, 20, 145),
            fundo_quantidade.get_rect(),
            border_radius=4
        )

        tela.blit(
            fundo_quantidade,
            (area_quantidade.x - 4, area_quantidade.y - 2)
        )

        tela.blit(quantidade, area_quantidade)

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

        mouse_x, mouse_y = self.posicao_mouse

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
