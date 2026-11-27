import pygame

from sistemas.catalogo_itens import CatalogoItens
from sistemas.carregador_imagens import obter_imagem


class InterfaceCrafting:
    def __init__(self):
        self.aberto = False

        self.fonte_titulo = pygame.font.Font(None, 40)
        self.fonte_secao = pygame.font.Font(None, 29)
        self.fonte_texto = pygame.font.Font(None, 25)
        self.fonte_detalhe = pygame.font.Font(None, 21)

        self.largura = 900
        self.altura = 540

        self.receitas = []
        self.selecionada = 0
        self.quantidade = 1
        self.mensagem = ""
        self.estacao = "bigorna"
        self.inventario = None

        self.catalogo_itens = CatalogoItens()

    def alternar(self):
        self.aberto = not self.aberto

        if self.aberto:
            self.selecionada = 0
            self.quantidade = 1
            self.mensagem = ""

    def configurar_receitas(
        self, receitas, estacao="bigorna", inventario=None
    ):
        self.receitas = list(receitas)
        self.estacao = estacao
        self.inventario = inventario
        self.selecionada = 0
        self.quantidade = 1

    def _nome_item(self, item_id):
        item = self.catalogo_itens.obter(item_id)
        return item["nome"] if item else item_id

    def _desenhar_texto(
        self, tela, texto, fonte, cor, posicao
    ):
        imagem = fonte.render(str(texto), True, cor)
        tela.blit(imagem, posicao)

    def _desenhar_secao(self, tela, rect, titulo):
        pygame.draw.rect(
            tela, (43, 43, 54), rect, border_radius=8
        )
        pygame.draw.rect(
            tela, (95, 95, 110), rect, 1, border_radius=8
        )

        self._desenhar_texto(
            tela, titulo, self.fonte_secao,
            (235, 210, 160),
            (rect.x + 15, rect.y + 12)
        )

        pygame.draw.line(
            tela, (85, 85, 100),
            (rect.x + 12, rect.y + 45),
            (rect.right - 12, rect.y + 45),
            1
        )

    def tratar_evento(self, evento, crafting=None):
        if not self.aberto or evento.type != pygame.KEYDOWN:
            return

        if evento.key == pygame.K_ESCAPE:
            self.aberto = False
            return

        if not self.receitas:
            return

        if evento.key == pygame.K_UP:
            self.selecionada = (
                self.selecionada - 1
            ) % len(self.receitas)
            self.mensagem = ""

        elif evento.key == pygame.K_DOWN:
            self.selecionada = (
                self.selecionada + 1
            ) % len(self.receitas)
            self.mensagem = ""

        elif evento.key == pygame.K_RIGHT:
            self.quantidade = min(99, self.quantidade + 1)
            self.mensagem = ""

        elif evento.key == pygame.K_LEFT:
            self.quantidade = max(1, self.quantidade - 1)
            self.mensagem = ""

        elif evento.key == pygame.K_RETURN and crafting is not None:
            receita = self.receitas[self.selecionada]

            sucesso = crafting.fabricar(
                receita["id"], self.quantidade
            )

            if sucesso:
                self.mensagem = "Fabricacao realizada com sucesso!"
            else:
                self.mensagem = (
                    "Materiais insuficientes ou inventario cheio."
                )

    def desenhar(self, tela):
        if not self.aberto:
            return

        largura_tela, altura_tela = tela.get_size()

        fundo = pygame.Surface(
            (largura_tela, altura_tela), pygame.SRCALPHA
        )
        fundo.fill((0, 0, 0, 165))
        tela.blit(fundo, (0, 0))

        painel = pygame.Rect(
            (largura_tela - self.largura) // 2,
            (altura_tela - self.altura) // 2,
            self.largura,
            self.altura
        )

        pygame.draw.rect(
            tela, (32, 32, 42), painel, border_radius=12
        )
        pygame.draw.rect(
            tela, (155, 155, 170), painel, 2,
            border_radius=12
        )

        nome_estacao = {
            "bigorna": "Bigorna",
            "fornalha": "Fornalha",
            "bancada": "Bancada",
        }.get(self.estacao, self.estacao.capitalize())

        self._desenhar_texto(
            tela, nome_estacao, self.fonte_titulo,
            (255, 255, 255),
            (painel.x + 22, painel.y + 15)
        )

        # Áreas independentes da interface.
        area_receitas = pygame.Rect(
            painel.x + 18, painel.y + 65, 230, 390
        )
        area_ingredientes = pygame.Rect(
            painel.x + 260, painel.y + 65, 340, 390
        )
        area_resultado = pygame.Rect(
            painel.x + 612, painel.y + 65, 270, 390
        )

        self._desenhar_secao(
            tela, area_receitas, "RECEITAS"
        )
        self._desenhar_secao(
            tela, area_ingredientes, "INGREDIENTES"
        )
        self._desenhar_secao(
            tela, area_resultado, "RESULTADO"
        )

        if not self.receitas:
            self._desenhar_texto(
                tela, "Nenhuma receita disponivel.",
                self.fonte_texto, (190, 190, 190),
                (area_receitas.x + 12, area_receitas.y + 65)
            )
        else:
            # Lista de receitas.
            for indice, receita in enumerate(self.receitas):
                y = area_receitas.y + 60 + indice * 38

                selecionada = indice == self.selecionada
                cor = (
                    (100, 85, 55)
                    if selecionada
                    else (43, 43, 54)
                )

                linha = pygame.Rect(
                    area_receitas.x + 8,
                    y,
                    area_receitas.width - 16,
                    32
                )
                pygame.draw.rect(
                    tela, cor, linha, border_radius=5
                )

                self._desenhar_texto(
                    tela, receita["nome"],
                    self.fonte_detalhe,
                    (255, 225, 170) if selecionada
                    else (220, 220, 220),
                    (linha.x + 8, linha.y + 7)
                )

            receita = self.receitas[self.selecionada]

            # Ingredientes e quantidades disponíveis.
            y = area_ingredientes.y + 65

            for item_id, quantidade in receita["ingredientes"].items():
                necessario = quantidade * self.quantidade
                disponivel = (
                    self.inventario.quantidade_disponivel(item_id)
                    if self.inventario else 0
                )

                cor = (
                    (145, 220, 145)
                    if disponivel >= necessario
                    else (240, 125, 125)
                )

                self._desenhar_texto(
                    tela, self._nome_item(item_id),
                    self.fonte_texto, (230, 230, 230),
                    (area_ingredientes.x + 16, y)
                )

                self._desenhar_texto(
                    tela, f"{necessario} / {disponivel}",
                    self.fonte_detalhe, cor,
                    (area_ingredientes.x + 190, y + 3)
                )

                y += 38

            # Prévia do produto fabricado.
            primeiro_resultado = next(
                iter(receita["resultado"].items())
            )
            item_id, quantidade_resultado = primeiro_resultado
            item = self.catalogo_itens.obter(item_id)

            nome = self._nome_item(item_id)
            imagem = None

            if item and item.get("imagem"):
                imagem = obter_imagem(
                    item["imagem"], (120, 120)
                )

            if imagem is not None:
                destino = imagem.get_rect(
                    center=(
                        area_resultado.centerx,
                        area_resultado.y + 145
                    )
                )
                tela.blit(imagem, destino)
            else:
                placeholder = pygame.Rect(
                    area_resultado.centerx - 55,
                    area_resultado.y + 90,
                    110,
                    110
                )
                pygame.draw.rect(
                    tela, (65, 65, 75), placeholder,
                    border_radius=8
                )

            nome_imagem = self.fonte_texto.render(
                nome, True, (255, 225, 170)
            )
            tela.blit(
                nome_imagem,
                nome_imagem.get_rect(
                    center=(
                        area_resultado.centerx,
                        area_resultado.y + 235
                    )
                )
            )

            total = quantidade_resultado * self.quantidade

            texto_quantidade = self.fonte_detalhe.render(
                f"Quantidade produzida: {total}",
                True, (170, 225, 170)
            )
            tela.blit(
                texto_quantidade,
                texto_quantidade.get_rect(
                    center=(
                        area_resultado.centerx,
                        area_resultado.y + 270
                    )
                )
            )

        # Rodapé separado do conteúdo.
        rodape_y = painel.bottom - 70

        pygame.draw.line(
            tela, (85, 85, 100),
            (painel.x + 18, rodape_y),
            (painel.right - 18, rodape_y),
            1
        )

        self._desenhar_texto(
            tela, f"Quantidade: {self.quantidade}",
            self.fonte_texto, (255, 255, 255),
            (painel.x + 22, rodape_y + 12)
        )

        if self.mensagem:
            self._desenhar_texto(
                tela, self.mensagem,
                self.fonte_detalhe, (255, 210, 120),
                (painel.x + 260, rodape_y + 15)
            )

        self._desenhar_texto(
            tela,
            "UP/DOWN: Receita | LEFT/RIGHT: Quantidade | "
            "ENTER: Fabricar | ESC: Fechar",
            self.fonte_detalhe, (170, 170, 180),
            (painel.x + 22, painel.bottom - 28)
        )
