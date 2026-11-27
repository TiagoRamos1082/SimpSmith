
import json
import copy
import pygame
import ctypes
import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from sistemas.catalogo_itens import CatalogoItens
from sistemas.carregador_imagens import obter_imagem

CAMINHO_MAPA = RAIZ / "dados" / "mapas" / "mapa_principal.json"
CAMINHO_OBJETOS = RAIZ / "mapa" / "objetos_mapa.json"
CATEGORIAS_CONSTRUCAO = {"item", "construcao"}

TAMANHO_TILE = 32

COR_FUNDO = (35, 35, 40)
COR_PAINEL = (48, 48, 55)
COR_GRADE = (20, 20, 20)
COR_TEXTO = (240, 240, 240)
COR_SELECAO = (255, 210, 50)


class EditorMapa:
    def __init__(self):
        pygame.init()

        info = pygame.display.Info()

        self.largura_janela = min(1200, info.current_w)
        self.altura_janela = min(760, info.current_h)

        self.painel_largura = 320
        self.posicao_mapa_x = 20
        self.posicao_mapa_y = 60

        self.tela_cheia = False
        self.tela = pygame.display.set_mode(
            (self.largura_janela, self.altura_janela),
            pygame.RESIZABLE
        )
        pygame.display.set_caption("SimpSmith - Editor de Mapas")

        # Maximiza a janela mantendo bordas e barra de tarefas.
        try:
            pygame.display.flip()
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 3)
        except (AttributeError, OSError):
            pass


        self.fonte = pygame.font.Font(None, 25)
        self.fonte_pequena = pygame.font.Font(None, 20)

        self.relogio = pygame.time.Clock()
        self.executando = True

        self.carregar_mapa()

        # Estrutura de sprites organizada por camada.
        sprites_por_camada = self.dados.setdefault(
            "sprites_por_camada", {}
        )

        # Mantém compatibilidade com os editores antigos.
        sprites_superiores = self.dados.setdefault(
            "sprites_superiores", []
        )

        if "superior" not in sprites_por_camada:
            sprites_por_camada["superior"] = sprites_superiores

        # A nova estrutura é a fonte principal.
        self.dados["sprites_superiores"] = sprites_por_camada["superior"]

        # Garante uma lista de sprites para cada camada.
        for nome_camada in self.dados["camadas"]:
            sprites_por_camada.setdefault(nome_camada, [])

        self.sprites_por_camada = sprites_por_camada

        self.sprites = {}
        self.carregar_sprites()

        self.escala = max(1, min(
            20,
            (self.largura_janela - self.painel_largura - 50) // self.largura,
            (self.altura_janela - 90) // self.altura
        ))

        self.escala_inicial = self.escala

        self.painel_x = self.largura_janela - self.painel_largura

        self.zoom_minimo = 1
        self.zoom_maximo = 40
        self.arrastando_camera = False
        self.ultima_posicao_camera = None

        self.camadas = list(self.dados["camadas"].keys())
        self.indice_camada = 0

        self.tiles = self.dados["tiles"]
        self.tile_selecionado = None
        self.sprite_selecionado = None
        self.sprite_scroll = 0
        self.painel_scroll = 0
        self.painel_conteudo_altura = 0
        self.chao_base_inicio = None
        self.chao_base_fim = None
        self.imagens_chao_base_redimensionadas = {}

        self.modo = "sprites"

        self.salvar_mensagem = ""

        # Histórico de alterações.
        self.historico = []
        self.historico_refazer = []
        self.limite_historico = 50

        # Salvamento automático.
        self.mapa_alterado = False
        self.intervalo_autosalvamento = 2000
        self.tempo_ultima_alteracao = 0
        self.edicao_pintura_ativa = False
        self.mostrar_grade = False
        self.arrastando_sprites = False
        self.sequencia_historico_ativo = False
        self.tempo_ultimo_sprite = 0
        self.intervalo_sprites = 150

        # Construções (bigorna etc.) salvas em mapa/objetos_mapa.json.
        self.paleta_aberta = False
        self.construcao_selecionada = None
        self.paleta_scroll = 0
        self.catalogo = CatalogoItens()
        self.construcoes = []
        self.objetos_mapa = []
        self.carregar_construcoes_mapa()

    # ------------------------------------------------------------------
    # CONSTRUCOES
    # ------------------------------------------------------------------

    def carregar_construcoes_mapa(self):
        self.construcoes = [
            item for item in self.catalogo.listar()
            if item["categoria"] in CATEGORIAS_CONSTRUCAO
            and item.get("imagem")
        ]

        if self.construcoes and self.construcao_selecionada is None:
            self.construcao_selecionada = self.construcoes[0]["id"]

        self.objetos_mapa = []

        if not CAMINHO_OBJETOS.is_file():
            return

        try:
            with CAMINHO_OBJETOS.open("r", encoding="utf-8-sig") as arquivo:
                registros = json.load(arquivo).get("objetos", [])
        except (OSError, ValueError) as erro:
            self.salvar_mensagem = f"Erro ao ler construcoes: {erro}"
            return

        for registro in registros:
            if self.catalogo.obter(registro.get("id")) is None:
                continue

            self.objetos_mapa.append({
                "id": registro["id"],
                "x": int(registro["x"]),
                "y": int(registro["y"]),
            })

    def salvar_objetos_mapa(self):
        temporario = CAMINHO_OBJETOS.with_suffix(".tmp")

        try:
            CAMINHO_OBJETOS.parent.mkdir(parents=True, exist_ok=True)

            with temporario.open("w", encoding="utf-8") as arquivo:
                json.dump(
                    {"objetos": self.objetos_mapa},
                    arquivo, indent=4, ensure_ascii=False
                )

            temporario.replace(CAMINHO_OBJETOS)
            self.salvar_mensagem = (
                f"{len(self.objetos_mapa)} construcoes salvas!"
            )
        except OSError as erro:
            self.salvar_mensagem = f"Erro ao salvar construcoes: {erro}"

    def obter_rect_objeto_tela(self, registro):
        item = self.catalogo.obter(registro["id"])
        fator = self.escala / self.tile_size

        return pygame.Rect(
            self.posicao_mapa_x + round(registro["x"] * fator),
            self.posicao_mapa_y + round(registro["y"] * fator),
            max(1, round(item["largura_visual"] * fator)),
            max(1, round(item["altura_visual"] * fator)),
        )

    def desenhar_objetos_mapa(self):
        for registro in self.objetos_mapa:
            item = self.catalogo.obter(registro["id"])
            rect = self.obter_rect_objeto_tela(registro)
            imagem = obter_imagem(
                item.get("imagem"),
                (item["largura_visual"], item["altura_visual"])
            )

            if imagem is not None:
                self.tela.blit(
                    pygame.transform.scale(imagem, rect.size), rect.topleft
                )
            else:
                pygame.draw.rect(self.tela, tuple(item["cor"]), rect)

            if self.paleta_aberta:
                pygame.draw.rect(self.tela, COR_SELECAO, rect, 1)

    def obter_rect_paleta(self):
        altura = min(
            self.altura_janela - self.posicao_mapa_y - 30,
            44 + max(1, len(self.construcoes)) * 30
        )
        return pygame.Rect(
            self.posicao_mapa_x + 8, self.posicao_mapa_y + 8, 230, altura
        )

    def obter_linhas_paleta(self):
        paleta = self.obter_rect_paleta()
        return [
            (item, pygame.Rect(paleta.x + 6, paleta.y + 38 + i * 30
                               - self.paleta_scroll, paleta.width - 12, 26))
            for i, item in enumerate(self.construcoes)
        ]

    def desenhar_paleta_construcoes(self):
        if not self.paleta_aberta:
            return

        paleta = self.obter_rect_paleta()
        pygame.draw.rect(self.tela, (32, 35, 43), paleta, border_radius=6)
        pygame.draw.rect(self.tela, COR_SELECAO, paleta, 1, border_radius=6)
        self.desenhar_texto(
            "CONSTRUCOES (C: fechar)", paleta.x + 8, paleta.y + 8,
            self.fonte_pequena
        )

        if not self.construcoes:
            self.desenhar_texto(
                "Nenhuma construcao cadastrada.", paleta.x + 8,
                paleta.y + 40, self.fonte_pequena
            )
            return

        self.tela.set_clip(paleta.inflate(-4, -4))
        for item, linha in self.obter_linhas_paleta():
            ativo = item["id"] == self.construcao_selecionada
            pygame.draw.rect(
                self.tela, (60, 66, 80) if ativo else (43, 47, 57),
                linha, border_radius=4
            )
            if ativo:
                pygame.draw.rect(self.tela, COR_SELECAO, linha, 1, border_radius=4)
            self.desenhar_texto(
                f"{item['nome']} ({item['categoria']})",
                linha.x + 6, linha.y + 6, self.fonte_pequena
            )
        self.tela.set_clip(None)

    def tratar_clique_construcoes(self, posicao):
        """Retorna True quando o clique foi consumido pela paleta/colocação."""

        if not self.paleta_aberta or posicao[0] >= self.painel_x:
            return False

        if self.obter_rect_paleta().collidepoint(posicao):
            for item, linha in self.obter_linhas_paleta():
                if linha.collidepoint(posicao):
                    self.construcao_selecionada = item["id"]
            return True

        item = self.catalogo.obter(self.construcao_selecionada)
        mundo = self.obter_posicao_mundo(posicao)

        if item is None or mundo is None:
            return True

        # x e y são o canto superior esquerdo; o clique fica no centro.
        x = max(0, mundo[0] - item["largura_visual"] // 2)
        y = max(0, mundo[1] - item["altura_visual"] // 2)

        self.objetos_mapa.append({"id": item["id"], "x": x, "y": y})
        self.salvar_objetos_mapa()
        return True

    def remover_construcao_em(self, posicao):
        if not self.paleta_aberta:
            return False

        for registro in reversed(self.objetos_mapa):
            if self.obter_rect_objeto_tela(registro).collidepoint(posicao):
                self.objetos_mapa.remove(registro)
                self.salvar_objetos_mapa()
                return True

        return False

    @property
    def camada_atual(self):
        return self.camadas[self.indice_camada]

    @property
    def tiles_disponiveis(self):
        return {
            identificador: informacoes
            for identificador, informacoes in self.tiles.items()
            if informacoes.get("categoria") == self.camada_atual
        }

    def atualizar_camada(self, deslocamento):
        self.indice_camada = (
            self.indice_camada + deslocamento
        ) % len(self.camadas)

        self.tile_selecionado = None
        self.sprite_selecionado = None

        self.sprite_scroll = 0
        self.painel_scroll = 0
        self.modo = "sprites"

    def carregar_mapa(self):
        with CAMINHO_MAPA.open("r", encoding="utf-8-sig") as arquivo:
            self.dados = json.load(arquivo)

        self.largura = self.dados["largura"]
        self.altura = self.dados["altura"]
        self.tile_size = self.dados["tile_size"]

    def carregar_sprites(self):
        pasta_base = RAIZ / "assets" / "tiles"

        self.sprites_por_camada_imagens = {}

        for camada in self.dados["camadas"]:
            pasta = pasta_base / camada
            biblioteca = {}

            if pasta.exists():
                for caminho in pasta.rglob("*"):
                    if not caminho.is_file():
                        continue

                    if caminho.suffix.lower() != ".png":
                        continue

                    identificador = (
                        caminho.relative_to(pasta)
                        .with_suffix("")
                        .as_posix()
                    )

                    imagem = pygame.image.load(
                        str(caminho)
                    ).convert_alpha()

                    biblioteca[identificador] = {
                        "imagem": imagem,
                        "caminho": caminho.relative_to(
                            RAIZ
                        ).as_posix()
                    }

            self.sprites_por_camada_imagens[camada] = biblioteca

        # Compatibilidade temporária com o código antigo.
        self.sprites = self.sprites_por_camada_imagens.get(
            "superior", {}
        )

    def registrar_estado_anterior(self):
        self.historico.append(copy.deepcopy(self.dados))

        if len(self.historico) > self.limite_historico:
            self.historico.pop(0)

        self.historico_refazer.clear()

    def marcar_alteracao(self):
        self.mapa_alterado = True
        self.tempo_ultima_alteracao = pygame.time.get_ticks()

    def restaurar_referencias(self):
        self.sprites_por_camada = self.dados["sprites_por_camada"]
        self.dados["sprites_superiores"] = (
            self.sprites_por_camada["superior"]
        )
        self.tiles = self.dados["tiles"]

    def desfazer(self):
        if not self.historico:
            self.salvar_mensagem = "Nada para desfazer!"
            return

        self.historico_refazer.append(copy.deepcopy(self.dados))
        self.dados = self.historico.pop()
        self.restaurar_referencias()
        self.marcar_alteracao()
        self.salvar_mensagem = "Alteração desfeita!"

    def refazer(self):
        if not self.historico_refazer:
            self.salvar_mensagem = "Nada para refazer!"
            return

        self.historico.append(copy.deepcopy(self.dados))
        self.dados = self.historico_refazer.pop()
        self.restaurar_referencias()
        self.marcar_alteracao()
        self.salvar_mensagem = "Alteração refeita!"

    def processar_autosalvamento(self):
        if not self.mapa_alterado:
            return

        agora = pygame.time.get_ticks()

        if agora - self.tempo_ultima_alteracao >= self.intervalo_autosalvamento:
            self.salvar_mapa()

    def salvar_mapa(self):
        try:
            with CAMINHO_MAPA.open("w", encoding="utf-8") as arquivo:
                json.dump(
                    self.dados,
                    arquivo,
                    indent=4,
                    ensure_ascii=False
                )

            self.salvar_mensagem = "Mapa salvo com sucesso!"
            self.mapa_alterado = False

        except OSError as erro:
            self.salvar_mensagem = f"Erro ao salvar: {erro}"

    def obter_posicao_tile(self, posicao_mouse):
        mouse_x, mouse_y = posicao_mouse

        x = (mouse_x - self.posicao_mapa_x) // self.escala
        y = (mouse_y - self.posicao_mapa_y) // self.escala

        if 0 <= x < self.largura and 0 <= y < self.altura:
            return int(x), int(y)

        return None

    def obter_posicao_mundo(self, posicao_mouse):
        mouse_x, mouse_y = posicao_mouse

        fator = self.escala / self.tile_size

        mundo_x = (mouse_x - self.posicao_mapa_x) / fator
        mundo_y = (mouse_y - self.posicao_mapa_y) / fator

        largura_mapa = self.largura * self.tile_size
        altura_mapa = self.altura * self.tile_size

        if not (0 <= mundo_x < largura_mapa):
            return None

        if not (0 <= mundo_y < altura_mapa):
            return None

        return round(mundo_x), round(mundo_y)
    def pintar_tile(self, x, y):
        if self.tile_selecionado not in self.tiles_disponiveis:
            return

        matriz = self.dados["camadas"][self.camada_atual]

        if matriz[y][x] == self.tile_selecionado:
            return

        # Uma sequência contínua de pintura gera uma única ação.
        if not self.edicao_pintura_ativa:
            self.registrar_estado_anterior()
            self.edicao_pintura_ativa = True

        matriz[y][x] = self.tile_selecionado
        self.marcar_alteracao()

    def posicionar_spawn(self, x, y):
        novo_spawn = {
            "x": x * self.tile_size,
            "y": y * self.tile_size,
            "direcao": "down"
        }

        if self.dados.get("spawn_jogador") == novo_spawn:
            return

        self.registrar_estado_anterior()
        self.dados["spawn_jogador"] = novo_spawn
        self.marcar_alteracao()

        self.salvar_mensagem = "Spawn atualizado!"

    def desenhar_texto(self, texto, x, y, fonte=None):
        fonte = fonte or self.fonte

        imagem = fonte.render(
            texto,
            True,
            COR_TEXTO
        )

        self.tela.blit(imagem, (x, y))

    def obter_rect_sprite_tela(self, sprite, camada="superior"):
        biblioteca = self.sprites_por_camada_imagens.get(camada, {})
        imagem = biblioteca.get(sprite["id"], {}).get("imagem")

        if imagem is None:
            return None

        fator = (self.escala / self.tile_size) * 2

        x = self.posicao_mapa_x + round(
            sprite["x"] * self.escala / self.tile_size
        )
        y = self.posicao_mapa_y + round(
            sprite["y"] * self.escala / self.tile_size
        )

        tamanhos = self.dados.get("tamanhos_sprites", {})
        configuracao = tamanhos.get(camada, {}).get(sprite["id"], {})

        largura_original = configuracao.get(
            "largura", imagem.get_width()
        )
        altura_original = configuracao.get(
            "altura", imagem.get_height()
        )

        largura = max(1, round(largura_original * fator))
        altura = max(1, round(altura_original * fator))

        return pygame.Rect(x, y, largura, altura)

    def desenhar_sprites_camada(self, camada):
        biblioteca = self.sprites_por_camada_imagens.get(camada, {})
        sprites = self.sprites_por_camada.get(camada, [])

        for sprite in sprites:
            imagem = biblioteca.get(sprite["id"], {}).get("imagem")

            if imagem is None:
                continue

            rect = self.obter_rect_sprite_tela(sprite, camada)

            imagem_redimensionada = pygame.transform.scale(
                imagem, rect.size
            )

            self.tela.blit(imagem_redimensionada, rect.topleft)

    def desenhar_sprites_superiores(self):
        self.desenhar_sprites_camada("superior")

    def desenhar_mapa(self):
        tamanho = self.escala

        rect_fundo = pygame.Rect(
            self.posicao_mapa_x,
            self.posicao_mapa_y,
            self.largura * tamanho,
            self.altura * tamanho
        )

        pygame.draw.rect(self.tela, COR_FUNDO, rect_fundo)

        # Desenha o sprite escolhido como textura repetida do chao.
        identificador_base = self.dados.get("chao_base")
        biblioteca_terreno = self.sprites_por_camada_imagens.get(
            "terreno", {}
        )

        dados_sprite = biblioteca_terreno.get(identificador_base)

        if dados_sprite is not None:
            imagem = dados_sprite["imagem"]

            fator = (self.escala / self.tile_size) * 2.0

            chave = (
                identificador_base,
                round(imagem.get_width() * fator),
                round(imagem.get_height() * fator)
            )

            imagem_tela = self.imagens_chao_base_redimensionadas.get(chave)

            if imagem_tela is None:
                dimensoes = (chave[1], chave[2])

                imagem_tela = pygame.transform.scale(
                    imagem, dimensoes
                )

                self.imagens_chao_base_redimensionadas[chave] = imagem_tela

            area_visivel = rect_fundo.clip(self.tela.get_rect())

            if area_visivel.width > 0 and area_visivel.height > 0:
                clip_anterior = self.tela.get_clip()
                self.tela.set_clip(area_visivel)

                largura_sprite, altura_sprite = imagem_tela.get_size()

                for y in range(
                    rect_fundo.top, rect_fundo.bottom, altura_sprite
                ):
                    for x in range(
                        rect_fundo.left, rect_fundo.right, largura_sprite
                    ):
                        self.tela.blit(imagem_tela, (x, y))

                self.tela.set_clip(clip_anterior)

        # Desenha cada camada e seus sprites na sequência.
        for nome_camada in self.camadas:
            matriz = self.dados["camadas"][nome_camada]

            for y in range(self.altura):
                for x in range(self.largura):
                    identificador = matriz[y][x]

                    if identificador is None:
                        continue

                    cor = self.tiles[identificador]["cor"]

                    rect = pygame.Rect(
                        self.posicao_mapa_x + x * tamanho,
                        self.posicao_mapa_y + y * tamanho,
                        tamanho,
                        tamanho
                    )

                    pygame.draw.rect(self.tela, cor, rect)

            self.desenhar_sprites_camada(nome_camada)

        self.desenhar_objetos_mapa()
        self.desenhar_grade_auxiliar()
        self.desenhar_spawn()
        self.desenhar_preview_spawn()

    def desenhar_grade_auxiliar(self):
        if not self.mostrar_grade:
            return

        fator = self.escala / self.tile_size
        largura = self.largura * self.tile_size
        altura = self.altura * self.tile_size

        largura_tela = max(1, round(largura * fator))
        altura_tela = max(1, round(altura * fator))

        superficie = pygame.Surface(
            (largura_tela, altura_tela),
            pygame.SRCALPHA
        )

        cor = (0, 0, 0, 110)

        for x in range(0, largura + 1, self.tile_size):
            posicao = round(x * fator)
            pygame.draw.line(
                superficie, cor,
                (posicao, 0), (posicao, altura_tela)
            )

        for y in range(0, altura + 1, self.tile_size):
            posicao = round(y * fator)
            pygame.draw.line(
                superficie, cor,
                (0, posicao), (largura_tela, posicao)
            )

        self.tela.blit(
            superficie,
            (self.posicao_mapa_x, self.posicao_mapa_y)
        )

    def desenhar_preview_spawn(self):
        if self.modo != "spawn":
            return

        posicao = self.obter_posicao_tile(pygame.mouse.get_pos())

        if posicao is None:
            return

        x, y = posicao
        tamanho = self.escala

        rect = pygame.Rect(
            self.posicao_mapa_x + x * tamanho,
            self.posicao_mapa_y + y * tamanho,
            tamanho,
            tamanho
        )

        superficie = pygame.Surface(
            (tamanho, tamanho),
            pygame.SRCALPHA
        )
        superficie.fill((255, 210, 50, 90))

        self.tela.blit(superficie, rect.topleft)

        pygame.draw.rect(
            self.tela, COR_SELECAO, rect, max(2, tamanho // 10)
        )

        pygame.draw.circle(
            self.tela, (255, 255, 255), rect.center,
            max(3, tamanho // 5)
        )
    def desenhar_spawn(self):
        spawn = self.dados.get("spawn_jogador")

        if spawn is None:
            return

        x = spawn["x"] // self.tile_size
        y = spawn["y"] // self.tile_size

        centro_x = self.posicao_mapa_x + x * self.escala + self.escala // 2
        centro_y = self.posicao_mapa_y + y * self.escala + self.escala // 2

        pygame.draw.circle(
            self.tela,
            (255, 220, 40),
            (centro_x, centro_y),
            8
        )

        pygame.draw.circle(
            self.tela,
            (30, 30, 30),
            (centro_x, centro_y),
            8,
            2
        )

    def desenhar_biblioteca_sprites(self):
        self.desenhar_texto(
            "BIBLIOTECA DE SPRITES",
            self.painel_x + 20, 145
        )

        biblioteca = self.sprites_por_camada_imagens[self.camada_atual]
        sprites = list(biblioteca.keys())
        inicio = self.sprite_scroll
        visiveis = sprites[inicio:inicio + 12]

        y = 185

        for identificador in visiveis:
            dados = biblioteca[identificador]
            imagem = dados["imagem"]

            largura, altura = imagem.get_size()
            fator = min(28 / largura, 28 / altura)

            miniatura = pygame.transform.scale(
                imagem,
                (
                    max(1, int(largura * fator)),
                    max(1, int(altura * fator))
                )
            )

            rect = pygame.Rect(
                self.painel_x + 15, y, 285, 36
            )

            if identificador == self.sprite_selecionado:
                pygame.draw.rect(self.tela, (85, 75, 35), rect)
                pygame.draw.rect(self.tela, COR_SELECAO, rect, 2)

            self.tela.blit(
                miniatura,
                (self.painel_x + 20, y + 4)
            )

            nome = identificador.split("/")[-1]

            self.desenhar_texto(
                nome,
                self.painel_x + 60,
                y + 9,
                self.fonte_pequena
            )

            y += 40

        self.desenhar_texto(
            f"{len(sprites)} sprites | "
            f"{inicio + 1}-{min(inicio + 12, len(sprites))}",
            self.painel_x + 20, 685, self.fonte_pequena
        )

        self.desenhar_texto(
            "[O] Voltar para pintura",
            self.painel_x + 20, 715, self.fonte_pequena
        )

    def desenhar_painel(self):
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

        # Informações do mapa.
        texto(
            f"Dimensões: {self.largura} x {self.altura} tiles",
            y, self.fonte_pequena, (170, 176, 188)
        )
        y += 32

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

        # Biblioteca de sprites da camada atual.
        if self.camada_atual in self.sprites_por_camada_imagens:
            secao("SPRITES DISPONIVEIS", y)
            y += 38

            sprites = list(
                self.sprites_por_camada_imagens[
                    self.camada_atual
                ].items()
            )
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

        # Selecao independente do chao base por sprites PNG.
        secao("CHAO BASE", y)
        y += 38

        texto(
            "Preenche todo o mapa:",
            y, self.fonte_pequena,
            (170, 176, 188)
        )
        y += 28

        biblioteca_terreno = self.sprites_por_camada_imagens.get(
            "terreno", {}
        )

        self.chao_base_inicio = y
        opcoes_base = [None] + list(biblioteca_terreno.keys())

        for identificador in opcoes_base:
            rect = pygame.Rect(
                10, y - self.painel_scroll,
                area.width - 28, 48
            )

            selecionado = (
                self.dados.get("chao_base") == identificador
            )

            pygame.draw.rect(
                superficie,
                (66, 62, 43) if selecionado else (43, 47, 57),
                rect,
                border_radius=5
            )

            if selecionado:
                pygame.draw.rect(
                    superficie, COR_SELECAO,
                    rect, 1, border_radius=5
                )

            if identificador is None:
                nome = "Sem chao base"
                imagem = None
            else:
                nome = identificador
                imagem = biblioteca_terreno[identificador]["imagem"]

            if imagem is not None:
                largura, altura = imagem.get_size()
                fator = min(36 / largura, 36 / altura, 1)
                tamanho = (
                    max(1, round(largura * fator)),
                    max(1, round(altura * fator))
                )
                miniatura = pygame.transform.scale(imagem, tamanho)

                superficie.blit(
                    miniatura,
                    (
                        18,
                        y + (48 - tamanho[1]) // 2
                        - self.painel_scroll
                    )
                )

            imagem_nome = self.fonte_pequena.render(
                nome[:25], True, COR_TEXTO
            )
            superficie.blit(
                imagem_nome,
                (66, y + 16 - self.painel_scroll)
            )

            y += 54

        self.chao_base_fim = y
        y += 18

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


    def tratar_clique(self, posicao):
        mouse_x, mouse_y = posicao

        if mouse_x >= self.painel_x:
            if mouse_y < 151:
                return

            y_conteudo = mouse_y - 151 + self.painel_scroll

            # Selecao do chao base usando exclusivamente sprites PNG.
            if (
                self.chao_base_inicio is not None
                and self.chao_base_inicio <= y_conteudo < self.chao_base_fim
            ):
                indice = (
                    y_conteudo - self.chao_base_inicio
                ) // 54

                biblioteca_terreno = self.sprites_por_camada_imagens.get(
                    "terreno", {}
                )
                opcoes = [None] + list(biblioteca_terreno.keys())

                if 0 <= indice < len(opcoes):
                    novo_chao = opcoes[indice]

                    if self.dados.get("chao_base") != novo_chao:
                        self.registrar_estado_anterior()

                        if novo_chao is None:
                            self.dados.pop("chao_base", None)
                        else:
                            self.dados["chao_base"] = novo_chao

                        self.marcar_alteracao()
                        self.salvar_mensagem = (
                            "Chao base removido!"
                            if novo_chao is None
                            else f"Chao base: {novo_chao}"
                        )

                return

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

            if self.camada_atual in self.sprites_por_camada_imagens and self.modo != "spawn":
                inicio_lista = y_biblioteca + 38
                altura_item = 54

                if y_conteudo >= inicio_lista:
                    indice = (
                        (y_conteudo - inicio_lista) // altura_item
                        + self.sprite_scroll
                    )
                    sprites = list(
                        self.sprites_por_camada_imagens[
                            self.camada_atual
                        ].keys()
                    )

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
            self.posicionar_sprite((x, y))

        elif self.modo == "spawn":
            self.posicionar_spawn(x, y)


    def posicionar_sprite(self, posicao_mundo):
        if self.sprite_selecionado is None:
            return False

        x, y = posicao_mundo

        biblioteca = self.sprites_por_camada_imagens[
            self.camada_atual
        ]
        imagem = biblioteca[self.sprite_selecionado]["imagem"]

        # O cursor representa o centro visual do sprite.
        x_sprite = round(x - imagem.get_width())
        y_sprite = round(y - imagem.get_height())

        # A sequencia inteira representa uma unica acao no historico.
        if not self.sequencia_historico_ativo:
            self.registrar_estado_anterior()
            self.sequencia_historico_ativo = True

        self.sprites_por_camada[self.camada_atual].append({
            "id": self.sprite_selecionado,
            "x": x_sprite,
            "y": y_sprite
        })

        self.marcar_alteracao()
        self.salvar_mensagem = "Sprite posicionado!"

        return True

    def processar_posicionamento_continuo(self):
        if not self.arrastando_sprites:
            return

        if self.modo != "sprites" or self.sprite_selecionado is None:
            return

        agora = pygame.time.get_ticks()

        if agora - self.tempo_ultimo_sprite < self.intervalo_sprites:
            return

        posicao = pygame.mouse.get_pos()

        if posicao[0] >= self.painel_x:
            return

        posicao_mundo = self.obter_posicao_mundo(posicao)

        if posicao_mundo is None:
            return

        self.tempo_ultimo_sprite = agora
        self.posicionar_sprite(posicao_mundo)


    def alternar_tela_cheia(self):
        if self.tela_cheia:
            self.tela_cheia = False
            self.tela = pygame.display.set_mode(
                (self.largura_janela, self.altura_janela),
                pygame.RESIZABLE
            )
        else:
            self.largura_janela = self.tela.get_width()
            self.altura_janela = self.tela.get_height()

            self.tela_cheia = True
            self.tela = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN
            )

        self.largura_janela, self.altura_janela = self.tela.get_size()
        self.painel_x = self.largura_janela - self.painel_largura

    def voltar_central(self):
        self.executando = False

    def desenhar_botao_central(self):
        rect = pygame.Rect(
            self.painel_x + 20, 108, 280, 28
        )

        pygame.draw.rect(self.tela, (52, 61, 76), rect, border_radius=5)
        pygame.draw.rect(self.tela, (100, 130, 175), rect, 1, border_radius=5)

        texto = self.fonte_pequena.render(
            "VOLTAR À CENTRAL", True, (241, 241, 241)
        )
        self.tela.blit(
            texto,
            texto.get_rect(center=rect.center)
        )

    def ajustar_zoom(self, novo_zoom, referencia):
        novo_zoom = max(
            self.zoom_minimo,
            min(self.zoom_maximo, novo_zoom)
        )

        if novo_zoom == self.escala:
            return

        fator = novo_zoom / self.escala
        mouse_x, mouse_y = referencia

        self.posicao_mapa_x = round(
            mouse_x - (mouse_x - self.posicao_mapa_x) * fator
        )
        self.posicao_mapa_y = round(
            mouse_y - (mouse_y - self.posicao_mapa_y) * fator
        )

        self.escala = novo_zoom

    def desenhar_indicador_zoom(self):
        percentual = round(
            (self.escala / self.escala_inicial) * 100
        )

        texto = self.fonte_pequena.render(
            f"ZOOM: {percentual}%",
            True,
            (241, 241, 241)
        )

        rect = pygame.Rect(20, 16, 120, 32)

        pygame.draw.rect(
            self.tela, (32, 35, 43), rect, border_radius=5
        )
        pygame.draw.rect(
            self.tela, (100, 130, 175), rect, 1, border_radius=5
        )

        self.tela.blit(
            texto,
            texto.get_rect(center=rect.center)
        )

    def tratar_eventos(self):
        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                self.executando = False

            elif evento.type == pygame.KEYDOWN:

                if (
                    evento.key == pygame.K_z
                    and pygame.key.get_mods() & pygame.KMOD_CTRL
                ):
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.refazer()
                    else:
                        self.desfazer()

                elif evento.key in (
                    pygame.K_PLUS,
                    pygame.K_EQUALS,
                    pygame.K_KP_PLUS
                ):
                    incremento = max(1, round(self.escala * 0.15))
                    novo_zoom = self.escala + incremento

                    self.ajustar_zoom(
                        novo_zoom,
                        (self.painel_x // 2, self.altura_janela // 2)
                    )

                elif evento.key in (
                    pygame.K_MINUS,
                    pygame.K_KP_MINUS
                ):
                    incremento = max(1, round(self.escala * 0.15))
                    novo_zoom = self.escala - incremento

                    self.ajustar_zoom(
                        novo_zoom,
                        (self.painel_x // 2, self.altura_janela // 2)
                    )

                elif evento.key in (
                    pygame.K_0,
                    pygame.K_KP0
                ):
                    self.ajustar_zoom(
                        self.escala_inicial,
                        (self.painel_x // 2, self.altura_janela // 2)
                    )

                elif evento.key == pygame.K_g:
                    self.mostrar_grade = not self.mostrar_grade

                elif evento.key == pygame.K_ESCAPE:
                    self.executando = False

                elif evento.key == pygame.K_F11:
                    self.alternar_tela_cheia()

                elif evento.key == pygame.K_RETURN:
                    self.salvar_mapa()

                elif evento.key == pygame.K_a:
                    self.atualizar_camada(-1)

                elif evento.key == pygame.K_d:
                    self.atualizar_camada(1)

                elif evento.key == pygame.K_c:
                    self.paleta_aberta = not self.paleta_aberta
                    self.salvar_mensagem = (
                        "Paleta de construcoes aberta: clique no mapa para "
                        "colocar, botao direito remove."
                        if self.paleta_aberta
                        else "Paleta de construcoes fechada."
                    )

                elif evento.key == pygame.K_p:
                    self.modo = (
                        "pintura"
                        if self.modo == "sprites"
                        else "sprites"
                    )

                elif evento.key == pygame.K_s:
                    self.modo = "spawn"


            elif evento.type == pygame.MOUSEWHEEL:
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

                    if self.camada_atual in self.sprites_por_camada_imagens:
                        self.sprite_scroll = max(
                            0,
                            min(
                                max(
                                    0,
                                    len(
                                        self.sprites_por_camada_imagens[
                                            self.camada_atual
                                        ]
                                    ) - 1
                                ),
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

            elif evento.type == pygame.MOUSEBUTTONDOWN:

                if evento.button == 2:
                    self.arrastando_camera = True
                    self.ultima_posicao_camera = evento.pos

                elif evento.button == 1:
                    botao_central = pygame.Rect(
                        self.painel_x + 20, 108, 280, 28
                    )

                    if botao_central.collidepoint(evento.pos):
                        self.arrastando_sprites = False
                        self.voltar_central()
                    elif self.tratar_clique_construcoes(evento.pos):
                        self.arrastando_sprites = False
                    else:
                        self.arrastando_sprites = (
                            evento.pos[0] < self.painel_x
                            and self.modo == "sprites"
                            and self.sprite_selecionado is not None
                            and self.obter_posicao_mundo(evento.pos) is not None
                        )

                        self.sequencia_historico_ativo = False
                        self.tempo_ultimo_sprite = pygame.time.get_ticks()

                        self.tratar_clique(evento.pos)

                elif evento.button == 3:
                    if evento.pos[0] >= self.painel_x:
                        continue

                    if self.remover_construcao_em(evento.pos):
                        continue

                    elemento_removido = False
                    camada = self.camada_atual

                    # Primeiro, verifica os sprites da camada atual.
                    sprites = self.sprites_por_camada[camada]

                    for sprite in reversed(sprites):
                        rect = self.obter_rect_sprite_tela(
                            sprite, camada
                        )

                        if rect is not None and rect.collidepoint(evento.pos):
                            self.registrar_estado_anterior()
                            sprites.remove(sprite)
                            self.marcar_alteracao()
                            self.salvar_mensagem = "Sprite removido!"
                            elemento_removido = True
                            break

                    # Se não encontrou sprite, verifica o tile da camada atual.
                    if not elemento_removido:
                        posicao = self.obter_posicao_tile(evento.pos)

                        if posicao is not None:
                            x, y = posicao
                            matriz = self.dados["camadas"][camada]

                            if matriz[y][x] is not None:
                                self.registrar_estado_anterior()
                                matriz[y][x] = None
                                self.marcar_alteracao()
                                self.salvar_mensagem = (
                                    f"Elemento removido: {camada}"
                                )

            elif evento.type == pygame.VIDEORESIZE:
                if not self.tela_cheia:
                    self.largura_janela = max(800, evento.w)
                    self.altura_janela = max(600, evento.h)

                    self.tela = pygame.display.set_mode(
                        (self.largura_janela, self.altura_janela),
                        pygame.RESIZABLE
                    )

                    self.largura_janela, self.altura_janela = (
                        self.tela.get_size()
                    )
                    self.painel_x = (
                        self.largura_janela - self.painel_largura
                    )

            elif evento.type == pygame.MOUSEBUTTONUP:
                if evento.button == 1:
                    self.edicao_pintura_ativa = False
                    self.arrastando_sprites = False
                    self.sequencia_historico_ativo = False

                elif evento.button == 2:
                    self.arrastando_camera = False
                    self.ultima_posicao_camera = None

            elif evento.type == pygame.MOUSEMOTION:

                if self.arrastando_camera:
                    dx = evento.pos[0] - self.ultima_posicao_camera[0]
                    dy = evento.pos[1] - self.ultima_posicao_camera[1]

                    self.posicao_mapa_x += dx
                    self.posicao_mapa_y += dy
                    self.ultima_posicao_camera = evento.pos

                elif pygame.mouse.get_pressed()[0]:
                    posicao = self.obter_posicao_tile(evento.pos)

                    if posicao is not None and self.modo == "pintura":
                        x, y = posicao
                        self.pintar_tile(x, y)

    def executar(self):
        while self.executando:
            self.relogio.tick(60)

            self.tratar_eventos()
            self.processar_posicionamento_continuo()
            self.processar_autosalvamento()

            self.tela.fill(COR_FUNDO)

            self.desenhar_mapa()
            self.desenhar_indicador_zoom()
            self.desenhar_paleta_construcoes()
            self.desenhar_painel()

            pygame.display.flip()

        if self.mapa_alterado:
            self.salvar_mapa()

        pygame.quit()


if __name__ == "__main__":
    editor = EditorMapa()
    editor.executar()

