from pathlib import Path
import py_compile
import shutil

arquivo = Path("editores/mapas/editor_mapa.py")
backup = Path("backups/editor_mapa_antes_painel_rolavel.py")

codigo = arquivo.read_text(encoding="utf-8")

if "self.painel_scroll = 0" in codigo:
    raise SystemExit("A rolagem do painel já foi adicionada.")

def substituir_metodo(texto, inicio, fim, novo):
    pos_inicio = texto.index(inicio)
    pos_fim = texto.index(fim, pos_inicio)
    return texto[:pos_inicio] + novo + "\n\n" + texto[pos_fim:]

# Estado da rolagem.
marcador = "        self.sprite_scroll = 0"
assert marcador in codigo
codigo = codigo.replace(
    marcador,
    marcador + "\n        self.painel_scroll = 0\n        self.painel_conteudo_altura = 0",
    1
)

# Painel completo: cabeçalho fixo e conteúdo rolável.
novo_painel = '''    def desenhar_painel(self):
        painel = pygame.Rect(
            self.painel_x, 0,
            self.painel_largura, self.altura_janela
        )
        pygame.draw.rect(self.tela, (32, 35, 43), painel)

        # Cabeçalho fixo.
        self.desenhar_texto(
            "SimpSmith", self.painel_x + 20, 16
        )
        self.desenhar_texto(
            "EDITOR DE MAPAS", self.painel_x + 20, 43,
            self.fonte_pequena
        )

        self.desenhar_botao_central()

        self.desenhar_texto(
            f"Mapa: {self.dados['nome']}",
            self.painel_x + 20, 78, self.fonte_pequena
        )
        self.desenhar_texto(
            f"{self.largura} x {self.altura} tiles",
            self.painel_x + 20, 101, self.fonte_pequena
        )

        pygame.draw.line(
            self.tela, (65, 70, 82),
            (self.painel_x + 15, 140),
            (self.painel_x + self.painel_largura - 15, 140), 1
        )

        # Área rolável.
        topo = 151
        rodape = self.altura_janela - 18
        altura_area = max(50, rodape - topo)

        area = pygame.Rect(
            self.painel_x + 8, topo,
            self.painel_largura - 16, altura_area
        )

        superficie = pygame.Surface(
            (area.width, area.height)
        )
        superficie.fill((32, 35, 43))

        tela_original = self.tela
        deslocamento_x = self.painel_x + 8
        deslocamento_y = topo

        class SuperficiePainel:
            def __init__(self, destino, x, y):
                self.destino = destino
                self.x = x
                self.y = y

            def blit(self, imagem, posicao, *args, **kwargs):
                self.destino.blit(
                    imagem,
                    (posicao[0] - self.x, posicao[1] - self.y),
                    *args, **kwargs
                )

        # Desenha os elementos usando coordenadas do painel.
        y = 0

        def texto(texto, posicao_y, fonte=None, cor=COR_TEXTO):
            fonte_usada = fonte or self.fonte
            imagem = fonte_usada.render(texto, True, cor)
            superficie.blit(imagem, (12, posicao_y - self.painel_scroll))

        def secao(titulo, posicao_y):
            texto(titulo, posicao_y)
            pygame.draw.line(
                superficie, (65, 70, 82),
                (12, posicao_y + 27 - self.painel_scroll),
                (area.width - 12, posicao_y + 27 - self.painel_scroll), 1
            )

        # Camada.
        secao("CAMADA ATUAL", y)
        y += 42

        texto(f"<  {self.camada_atual.upper()}  >", y)
        y += 34

        descricoes = {
            "terreno": [
                "Base visual do mapa.",
                "Grama, terra, areia e agua."
            ],
            "superior": [
                "Detalhes sobre o terreno:",
                "flores e vegetacao."
            ],
            "objetos": [
                "Estruturas e elementos",
                "visuais do cenario."
            ]
        }

        for linha in descricoes.get(
            self.camada_atual, ["Camada personalizada."]
        ):
            texto(linha, y, self.fonte_pequena, (170, 176, 188))
            y += 22

        y += 18

        # Biblioteca.
        if self.camada_atual == "superior":
            secao("SPRITES DISPONIVEIS", y)
            y += 38

            sprites = list(self.sprites.items())
            inicio = self.sprite_scroll
            altura_item = 54

            for identificador, informacoes in sprites[inicio:]:
                rect = pygame.Rect(
                    10, y - self.painel_scroll,
                    area.width - 28, 46
                )

                selecionado = identificador == self.sprite_selecionado

                if selecionado:
                    pygame.draw.rect(
                        superficie, (66, 62, 43), rect,
                        border_radius=5
                    )
                    pygame.draw.rect(
                        superficie, COR_SELECAO, rect, 1,
                        border_radius=5
                    )
                else:
                    pygame.draw.rect(
                        superficie, (43, 47, 57), rect,
                        border_radius=5
                    )

                imagem = informacoes["imagem"]
                largura, altura = imagem.get_size()
                fator = min(34 / largura, 34 / altura)

                miniatura = pygame.transform.scale(
                    imagem,
                    (
                        max(1, int(largura * fator)),
                        max(1, int(altura * fator))
                    )
                )

                superficie.blit(
                    miniatura,
                    (17, y + 6 - self.painel_scroll)
                )

                nome = identificador.split("/")[-1]
                fonte_item = self.fonte_pequena
                imagem_nome = fonte_item.render(
                    nome[:25], True, COR_TEXTO
                )
                superficie.blit(
                    imagem_nome,
                    (60, y + 14 - self.painel_scroll)
                )

                y += altura_item

            texto(
                f"{len(sprites)} sprites disponíveis",
                y + 2, self.fonte_pequena,
                (170, 176, 188)
            )
            y += 32

            texto(
                "Use O para voltar à pintura.",
                y, self.fonte_pequena,
                (170, 176, 188)
            )
            y += 38

        else:
            secao("TILES DISPONIVEIS", y)
            y += 38

            disponiveis = list(self.tiles_disponiveis.items())

            if not disponiveis:
                texto(
                    "Nenhum tile cadastrado.",
                    y, self.fonte_pequena
                )
                y += 42
            else:
                for identificador, informacoes in disponiveis:
                    rect = pygame.Rect(
                        10, y - self.painel_scroll,
                        area.width - 28, 44
                    )

                    selecionado = identificador == self.tile_selecionado

                    pygame.draw.rect(
                        superficie,
                        (66, 62, 43) if selecionado else (43, 47, 57),
                        rect, border_radius=5
                    )

                    if selecionado:
                        pygame.draw.rect(
                            superficie, COR_SELECAO,
                            rect, 1, border_radius=5
                        )

                    cor = tuple(informacoes["cor"])
                    pygame.draw.rect(
                        superficie, cor,
                        (18, y + 8 - self.painel_scroll, 28, 28),
                        border_radius=3
                    )

                    nome = identificador[:25]
                    imagem_nome = self.fonte_pequena.render(
                        nome, True, COR_TEXTO
                    )
                    superficie.blit(
                        imagem_nome,
                        (58, y + 13 - self.painel_scroll)
                    )

                    y += 52

            y += 20

        # Ferramentas.
        secao("FERRAMENTAS", y)
        y += 40

        if self.modo == "spawn":
            modo_texto = "Modo: posicionar spawn"
        elif self.modo == "sprites":
            modo_texto = "Modo: posicionar sprites"
        else:
            modo_texto = "Modo: pintura"

        texto(modo_texto, y, self.fonte_pequena)
        y += 34

        controles = [
            ("P", "Alternar modo"),
            ("S", "Posicionar spawn"),
            ("A / D", "Trocar camada"),
            ("ENTER", "Salvar mapa"),
            ("Clique direito", "Apagar elemento"),
            ("F11", "Tela cheia"),
            ("ESC", "Sair do editor")
        ]

        for tecla, descricao in controles:
            pygame.draw.rect(
                superficie, (43, 47, 57),
                (10, y - self.painel_scroll, area.width - 28, 36),
                border_radius=4
            )

            imagem_tecla = self.fonte_pequena.render(
                tecla, True, (150, 180, 235)
            )
            imagem_descricao = self.fonte_pequena.render(
                descricao, True, COR_TEXTO
            )

            superficie.blit(
                imagem_tecla,
                (17, y + 9 - self.painel_scroll)
            )
            superficie.blit(
                imagem_descricao,
                (105, y + 9 - self.painel_scroll)
            )

            y += 43

        y += 12
        texto(
            "Spawn: circulo amarelo",
            y, self.fonte_pequena,
            (220, 195, 90)
        )
        y += 32

        if self.salvar_mensagem:
            texto(
                self.salvar_mensagem,
                y, self.fonte_pequena,
                (130, 205, 150)
            )
            y += 30

        self.painel_conteudo_altura = y
        max_scroll = max(0, y - altura_area)
        self.painel_scroll = max(
            0, min(self.painel_scroll, max_scroll)
        )

        # Recorta o conteúdo dentro da área rolável.
        tela_original.blit(superficie, area.topleft)

        # Barra de rolagem.
        if max_scroll > 0:
            trilho = pygame.Rect(
                self.painel_x + self.painel_largura - 9,
                topo, 4, altura_area
            )
            pygame.draw.rect(
                tela_original, (55, 60, 72), trilho,
                border_radius=3
            )

            altura_barra = max(
                28,
                int(altura_area * altura_area / y)
            )
            deslocamento = int(
                (altura_area - altura_barra)
                * self.painel_scroll / max_scroll
            )

            barra = pygame.Rect(
                trilho.x, trilho.y + deslocamento,
                trilho.width, altura_barra
            )
            pygame.draw.rect(
                tela_original, (130, 145, 170), barra,
                border_radius=3
            )
'''

codigo = substituir_metodo(
    codigo,
    "    def desenhar_painel(self):",
    "    def tratar_clique(self, posicao):",
    novo_painel
)

# Clique no painel com coordenadas ajustadas pelo scroll.
novo_clique = '''    def tratar_clique(self, posicao):
        mouse_x, mouse_y = posicao

        if mouse_x >= self.painel_x:
            if mouse_y < 151:
                return

            y_conteudo = mouse_y - 151 + self.painel_scroll

            y = 42
            descricoes = self.camada_atual

            if y_conteudo < 76:
                self.atualizar_camada(
                    -1 if y_conteudo < 59 else 1
                )
                self.painel_scroll = 0
                return

            # A biblioteca começa depois da descrição da camada.
            y_biblioteca = 42 + 34 + 34 + 44

            if self.camada_atual == "superior" and self.modo != "spawn":
                inicio_lista = y_biblioteca + 38
                altura_item = 54

                if y_conteudo >= inicio_lista:
                    indice = (
                        (y_conteudo - inicio_lista) // altura_item
                        + self.sprite_scroll
                    )
                    sprites = list(self.sprites.keys())

                    if 0 <= indice < len(sprites):
                        self.sprite_selecionado = sprites[indice]
                        self.modo = "sprites"
                return

            disponiveis = list(self.tiles_disponiveis.keys())
            inicio_lista = y_biblioteca + 38

            if y_conteudo >= inicio_lista:
                indice = (y_conteudo - inicio_lista) // 52

                if 0 <= indice < len(disponiveis):
                    self.tile_selecionado = disponiveis[indice]
                    self.modo = "pintura"
            return

        if self.modo == "sprites":
            posicao_mundo = self.obter_posicao_mundo(posicao)
            if posicao_mundo is None:
                return
            x, y = posicao_mundo
        else:
            posicao_tile = self.obter_posicao_tile(posicao)
            if posicao_tile is None:
                return
            x, y = posicao_tile

        if self.modo == "pintura":
            self.pintar_tile(x, y)

        elif self.modo == "sprites":
            if self.sprite_selecionado is not None:
                self.dados["sprites_superiores"].append({
                    "id": self.sprite_selecionado,
                    "x": x,
                    "y": y
                })
                self.salvar_mensagem = "Sprite posicionado!"

        elif self.modo == "spawn":
            self.posicionar_spawn(x, y)
'''

codigo = substituir_metodo(
    codigo,
    "    def tratar_clique(self, posicao):",
    "    def alternar_tela_cheia(self):",
    novo_clique
)

# Rolagem do painel sem afetar o zoom do mapa.
inicio = codigo.index("            elif evento.type == pygame.MOUSEWHEEL:")
fim = codigo.index("            elif evento.type == pygame.MOUSEBUTTONDOWN:", inicio)

novo_scroll = '''            elif evento.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                if mouse_x >= self.painel_x:
                    topo = 151
                    rodape = self.altura_janela - 18
                    altura_area = max(50, rodape - topo)
                    max_scroll = max(
                        0, self.painel_conteudo_altura - altura_area
                    )

                    self.painel_scroll = max(
                        0,
                        min(
                            max_scroll,
                            self.painel_scroll - evento.y * 45
                        )
                    )

                    if self.camada_atual == "superior":
                        self.sprite_scroll = max(
                            0,
                            min(
                                max(0, len(self.sprites) - 1),
                                self.sprite_scroll - evento.y
                            )
                        )

                else:
                    zoom_anterior = self.escala
                    novo_zoom = max(
                        self.zoom_minimo,
                        min(
                            self.zoom_maximo,
                            round(self.escala * (1.15 ** evento.y))
                        )
                    )

                    if novo_zoom != zoom_anterior:
                        fator = novo_zoom / zoom_anterior

                        self.posicao_mapa_x = round(
                            mouse_x - (mouse_x - self.posicao_mapa_x) * fator
                        )
                        self.posicao_mapa_y = round(
                            mouse_y - (mouse_y - self.posicao_mapa_y) * fator
                        )
                        self.escala = novo_zoom

'''

codigo = codigo[:inicio] + novo_scroll + codigo[fim:]

# Corrige o botão de retorno que apareceu com codificação incorreta.
codigo = codigo.replace("VOLTAR Ã€ CENTRAL", "VOLTAR À CENTRAL")

# Compila em arquivo temporário antes de substituir.
temporario = arquivo.with_name("editor_mapa_temp.py")
temporario.write_text(codigo, encoding="utf-8")

try:
    py_compile.compile(str(temporario), doraise=True)
except Exception:
    temporario.unlink(missing_ok=True)
    raise

backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(arquivo, backup)
temporario.replace(arquivo)

print("Painel rolável aplicado e validado!")
print(f"Backup: {backup}")
