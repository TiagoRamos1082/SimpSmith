
import pygame


class Mineracao:
    TECLA = pygame.K_e
    TEMPO_MINERACAO = 2.0
    TAMANHO_SENSOR = 8

    LARGURA_BARRA = 300
    ALTURA_BARRA = 18
    MARGEM_INFERIOR = 55

    COR_FUNDO = (35, 35, 35)
    COR_BARRA = (245, 190, 55)
    COR_BORDA = (240, 240, 240)

    def __init__(self, inventario):
        self.inventario = inventario
        self.alvo = None
        self.progresso = 0.0
        self._aguardando_soltar = False
        self.mensagem = ""
        self.coleta_concluida = False

    def atualizar(self, dt, jogador, spawn):
        teclas = pygame.key.get_pressed()

        # Exige soltar E depois de uma falha.
        if not teclas[self.TECLA]:
            self._aguardando_soltar = False
            self.mensagem = ""
            self._cancelar()
            return

        if self._aguardando_soltar:
            return

        recurso = self._encontrar_alvo(jogador, spawn)

        if recurso is None:
            self._cancelar()
            return

        if recurso is not self.alvo:
            self.alvo = recurso
            self.progresso = 0.0

        dados_item = self.inventario.catalogo.obter(self.alvo.tipo)

        if dados_item is None:
            self.mensagem = (
                f"Item '{self.alvo.tipo}' não existe no catálogo."
            )
            self._aguardando_soltar = True
            self._cancelar()
            return

        tempo = float(
            dados_item.get("tempo_coleta", self.TEMPO_MINERACAO)
        )

        self.progresso += dt

        if self.progresso >= tempo:
            tipo_recurso = self.alvo.tipo

            if self.inventario.adicionar(tipo_recurso):
                spawn.minerar(self.alvo)
                self.coleta_concluida = True
                self.mensagem = ""
                self._cancelar()
                self._aguardando_soltar = True
            else:
                self.mensagem = (
                    "Inventário cheio. Solte E para tentar novamente."
                )
                self._aguardando_soltar = True
                self._cancelar()

    def _encontrar_alvo(self, jogador, spawn):
        jogador_rect = jogador.rect
        alvos_validos = []

        tamanho_sensor = self.TAMANHO_SENSOR

        if jogador.direcao == "up":
            sensor = pygame.Rect(
                jogador_rect.centerx - tamanho_sensor // 2,
                jogador_rect.top - tamanho_sensor + 2,
                tamanho_sensor,
                tamanho_sensor
            )

        elif jogador.direcao == "down":
            sensor = pygame.Rect(
                jogador_rect.centerx - tamanho_sensor // 2,
                jogador_rect.bottom - 2,
                tamanho_sensor,
                tamanho_sensor
            )

        elif jogador.direcao == "left":
            sensor = pygame.Rect(
                jogador_rect.left - tamanho_sensor + 2,
                jogador_rect.centery - tamanho_sensor // 2,
                tamanho_sensor,
                tamanho_sensor
            )

        elif jogador.direcao == "right":
            sensor = pygame.Rect(
                jogador_rect.right - 2,
                jogador_rect.centery - tamanho_sensor // 2,
                tamanho_sensor,
                tamanho_sensor
            )

        else:
            return None

        for recurso in spawn.minerios:
            recurso_rect = recurso.rect

            areas_interacao = getattr(
                recurso, "areas_interacao", None
            )

            # A interacao utiliza a mesma geometria configurada
            # no editor para a colisao do recurso.
            if areas_interacao is None:
                areas_interacao = [recurso_rect]

            olhando_para_recurso = any(
                sensor.colliderect(area)
                for area in areas_interacao
            )

            if olhando_para_recurso:
                dx = jogador_rect.centerx - recurso_rect.centerx
                dy = jogador_rect.centery - recurso_rect.centery
                distancia = dx ** 2 + dy ** 2

                alvos_validos.append((distancia, recurso))

        if not alvos_validos:
            return None

        return min(alvos_validos, key=lambda alvo: alvo[0])[1]

    def _cancelar(self):
        self.alvo = None
        self.progresso = 0.0

    def desenhar(self, tela):
        if self.alvo is None and not self.mensagem:
            return

        largura = self.LARGURA_BARRA
        altura = self.ALTURA_BARRA

        x = (tela.get_width() - largura) // 2
        y = tela.get_height() - self.MARGEM_INFERIOR - altura

        fundo = pygame.Rect(x, y, largura, altura)

        pygame.draw.rect(
            tela,
            self.COR_FUNDO,
            fundo,
            border_radius=8
        )

        if self.alvo is not None:
            dados_item = self.inventario.catalogo.obter(
                self.alvo.tipo
            )

            tempo = (
                float(dados_item.get("tempo_coleta", self.TEMPO_MINERACAO))
                if dados_item
                else self.TEMPO_MINERACAO
            )

            percentual = min(self.progresso / tempo, 1.0)

            largura_preenchida = round(largura * percentual)
            x_preenchimento = (
                tela.get_width() - largura_preenchida
            ) // 2

            preenchimento = pygame.Rect(
                x_preenchimento,
                y,
                largura_preenchida,
                altura
            )

            if largura_preenchida > 0:
                pygame.draw.rect(
                    tela,
                    self.COR_BARRA,
                    preenchimento,
                    border_radius=8
                )

            mensagem = (
                "Coletando..."
                if self.alvo.categoria == "minerio"
                else "Minerando..."
            )

            texto = pygame.font.Font(None, 24).render(
                mensagem,
                True,
                (0, 0, 0)
            )

            tela.blit(
                texto,
                texto.get_rect(
                    center=(tela.get_width() // 2, y - 18)
                )
            )

        pygame.draw.rect(
            tela,
            self.COR_BORDA,
            fundo,
            width=2,
            border_radius=8
        )

        if self.mensagem:
            texto = pygame.font.Font(None, 22).render(
                self.mensagem,
                True,
                (255, 220, 120)
            )

            tela.blit(
                texto,
                texto.get_rect(
                    center=(tela.get_width() // 2, y - 22)
                )
            )



