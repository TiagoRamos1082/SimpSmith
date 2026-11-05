from pathlib import Path
import shutil
import py_compile
import sys

arquivo = Path("editores/tiles/editor_sprites.py")
if not arquivo.exists():
    sys.exit("Editor de Sprites nao encontrado.")

codigo = arquivo.read_text(encoding="utf-8-sig")

if "self.scroll_painel" in codigo:
    sys.exit("O patch de scroll ja parece estar aplicado. Nada alterado.")

# Conferir a estrutura antes de modificar.
marcadores = [
    "class EditorSprites:",
    "def desenhar_painel(self):",
    "def tratar_eventos(self):",
    "def exportar(self):",
    "def executar(self):",
    "self.tela_cheia = True",
    "elif evento.type == pygame.MOUSEWHEEL:",
]

for marcador in marcadores:
    if marcador not in codigo:
        sys.exit(f"Estrutura inesperada: {marcador}")

# 1. Inicializacao em janela normal.
antigo = '''        self.largura_janela = min(1200, info.current_w)
        self.altura_janela = min(760, info.current_h)
        self.tela_cheia = True

        self.tela = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.largura, self.altura = self.tela.get_size()
'''

novo = '''        self.largura_janela = min(1200, info.current_w)
        self.altura_janela = min(760, info.current_h)
        self.tela_cheia = False

        self.tela = pygame.display.set_mode(
            (self.largura_janela, self.altura_janela),
            pygame.RESIZABLE
        )
        self.largura, self.altura = self.tela.get_size()
'''

if antigo not in codigo:
    sys.exit("Inicializacao da janela nao encontrada.")

codigo = codigo.replace(antigo, novo, 1)

# 2. Estado do scroll.
marcador = '        self.largura_painel = 300\n'
if marcador not in codigo:
    sys.exit("Largura do painel nao encontrada.")

codigo = codigo.replace(
    marcador,
    marcador + '        self.scroll_painel = 0\n'
    '        self.max_scroll_painel = 0\n',
    1
)

# 3. Metodos de tela cheia e retorno.
metodos = '''    def alternar_tela_cheia(self):
        if self.tela_cheia:
            self.tela = pygame.display.set_mode(
                (self.largura_janela, self.altura_janela),
                pygame.RESIZABLE
            )
            self.tela_cheia = False
        else:
            self.largura_janela = self.largura
            self.altura_janela = self.altura
            self.tela = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN
            )
            self.tela_cheia = True

        self.largura, self.altura = self.tela.get_size()
        self.limite_visual = self.largura - self.largura_painel - 35

    def voltar_central(self):
        # A Central permanece aberta em segundo plano.
        self.executando = False

'''

marcador = '    def desenhar_texto(self, texto, x, y, fonte=None, cor=(240, 240, 240)):\n'
if marcador not in codigo:
    sys.exit("Metodo desenhar_texto nao encontrado.")

codigo = codigo.replace(marcador, metodos + marcador, 1)

# 4. Painel com conteudo rolavel e textos organizados.
inicio = codigo.index("    def desenhar_painel(self):")
fim = codigo.index("    def exportar(self):", inicio)

painel = '''    def desenhar_painel(self):
        fundo = (32, 35, 43)
        painel = (41, 45, 54)
        cartao = (48, 53, 64)
        borda = (58, 64, 77)
        texto = (240, 240, 240)
        secundario = (165, 170, 181)
        azul = (122, 162, 247)
        destaque = (217, 170, 91)

        painel_x = self.largura - self.largura_painel
        margem = 18
        x = painel_x + margem
        largura = self.largura_painel - margem * 2

        # Cabecalho.
        pygame.draw.rect(self.tela, fundo, (0, 0, self.largura, 70))
        pygame.draw.line(
            self.tela, borda, (0, 69), (self.largura, 69), 1
        )

        self.desenhar_texto("SimpSmith", 24, 10, self.fonte, texto)
        self.desenhar_texto(
            "EDITOR DE SPRITES", 25, 40,
            self.fonte_pequena, secundario
        )

        botao_voltar = pygame.Rect(self.largura - 190, 16, 166, 38)
        pygame.draw.rect(
            self.tela, (52, 56, 66), botao_voltar, border_radius=6
        )
        pygame.draw.rect(
            self.tela, borda, botao_voltar, 1, border_radius=6
        )
        label = self.fonte_pequena.render(
            "VOLTAR À CENTRAL", True, texto
        )
        self.tela.blit(label, label.get_rect(center=botao_voltar.center))

        # Fundo do painel.
        pygame.draw.rect(
            self.tela, painel,
            (painel_x, 70, self.largura_painel, self.altura - 70)
        )
        pygame.draw.line(
            self.tela, borda,
            (painel_x, 70), (painel_x, self.altura), 2
        )

        area_topo = 82
        area_base = self.altura - 18
        altura_area = max(1, area_base - area_topo)

        # Todo o conteudo abaixo respeita a area de recorte.
        clip_anterior = self.tela.get_clip()
        self.tela.set_clip(
            pygame.Rect(painel_x, area_topo,
                        self.largura_painel, altura_area)
        )

        def titulo(rotulo, y):
            self.desenhar_texto(
                rotulo, x, y - self.scroll_painel,
                self.fonte_pequena, azul
            )

        def linha(rotulo, y, cor=texto):
            self.desenhar_texto(
                rotulo, x, y - self.scroll_painel,
                self.fonte_pequena, cor
            )

        y = 95

        titulo("SPRITESHEET", y)
        y += 30
        linha(f"{self.imagem_largura} x {self.imagem_altura} px", y)
        y += 25
        linha(f"Grade: {self.colunas} x {self.linhas}", y)
        y += 25
        linha(f"Celula: {TAMANHO_CELULA} x {TAMANHO_CELULA}", y)
        y += 34

        pygame.draw.line(
            self.tela, borda,
            (x, y - self.scroll_painel),
            (x + largura, y - self.scroll_painel), 1
        )

        y += 18
        titulo("SELECAO ATUAL", y)
        y += 30

        selecao = self.obter_selecao()
        if selecao:
            x1, y1, x2, y2 = selecao
            colunas = x2 - x1
            linhas = y2 - y1
            linha(f"Colunas: {colunas}", y)
            y += 25
            linha(f"Linhas: {linhas}", y)
            y += 25
            linha(
                f"Pixels: {colunas * TAMANHO_CELULA} x "
                f"{linhas * TAMANHO_CELULA}", y
            )
        else:
            linha("Nenhuma regiao selecionada.", y, secundario)

        y += 42
        pygame.draw.line(
            self.tela, borda,
            (x, y - self.scroll_painel),
            (x + largura, y - self.scroll_painel), 1
        )

        y += 18
        titulo("CATEGORIA", y)
        y += 32

        categorias = [
            ("[1] Terreno", "terreno"),
            ("[2] Superior", "superior"),
            ("[3] Objetos", "objetos"),
        ]

        for nome, valor in categorias:
            cor = azul if self.categoria == valor else secundario
            prefixo = "> " if self.categoria == valor else "  "
            linha(prefixo + nome, y, cor)
            y += 29

        y += 12
        pygame.draw.line(
            self.tela, borda,
            (x, y - self.scroll_painel),
            (x + largura, y - self.scroll_painel), 1
        )

        y += 18
        titulo("NOME DO SPRITE", y)
        y += 32

        nome = self.nome
        if len(nome) > 27:
            nome = nome[:24] + "..."

        linha(
            nome, y,
            destaque if self.editando_nome else texto
        )
        y += 42

        pygame.draw.line(
            self.tela, borda,
            (x, y - self.scroll_painel),
            (x + largura, y - self.scroll_painel), 1
        )

        y += 18
        titulo("ATALHOS", y)
        y += 32

        atalhos = [
            "[F2] Editar nome",
            "[ENTER] Exportar",
            "[R] Limpar selecao",
            "[F11] Tela cheia",
            "[ESC] Fechar editor",
        ]

        for atalho in atalhos:
            linha(atalho, y, secundario)
            y += 27

        y += 15
        pygame.draw.line(
            self.tela, borda,
            (x, y - self.scroll_painel),
            (x + largura, y - self.scroll_painel), 1
        )
        y += 18
        titulo("STATUS", y)
        y += 30

        mensagem = self.mensagem
        if len(mensagem) > 35:
            mensagem = mensagem[:32] + "..."
        linha(mensagem, y, destaque)

        # Limite de rolagem.
        conteudo_altura = y + 45 - 95
        self.max_scroll_painel = max(
            0, conteudo_altura - altura_area
        )
        self.scroll_painel = max(
            0, min(self.scroll_painel, self.max_scroll_painel)
        )

        # Barra de rolagem.
        if self.max_scroll_painel > 0:
            trilho_x = self.largura - 9
            trilho = pygame.Rect(trilho_x, area_topo, 4, altura_area)
            pygame.draw.rect(self.tela, borda, trilho, border_radius=3)

            proporcao = altura_area / conteudo_altura
            altura_barra = max(28, int(altura_area * proporcao))
            deslocamento = int(
                (altura_area - altura_barra)
                * self.scroll_painel / self.max_scroll_painel
            )
            barra = pygame.Rect(
                trilho_x, area_topo + deslocamento,
                4, altura_barra
            )
            pygame.draw.rect(
                self.tela, azul, barra, border_radius=3
            )

        self.tela.set_clip(clip_anterior)

'''

codigo = codigo[:inicio] + painel + codigo[fim:]

# 5. Substituir tratamento da roda: painel rola, area de sprites aplica zoom.
inicio = codigo.index("            elif evento.type == pygame.MOUSEWHEEL:")
fim = codigo.index("            elif evento.type == pygame.MOUSEBUTTONDOWN:", inicio)

roda = '''            elif evento.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                if mouse_x >= self.largura - self.largura_painel:
                    self.scroll_painel -= evento.y * 35
                    self.scroll_painel = max(
                        0,
                        min(self.scroll_painel, self.max_scroll_painel)
                    )
                else:
                    zoom_anterior = self.escala
                    novo_zoom = max(
                        self.zoom_minimo,
                        min(self.zoom_maximo,
                            self.escala * (1.15 ** evento.y))
                    )

                    mundo_x = (
                        mouse_x - self.origem_x - self.pan_x
                    ) / zoom_anterior
                    mundo_y = (
                        mouse_y - self.origem_y - self.pan_y
                    ) / zoom_anterior

                    self.pan_x = (
                        mouse_x - self.origem_x - mundo_x * novo_zoom
                    )
                    self.pan_y = (
                        mouse_y - self.origem_y - mundo_y * novo_zoom
                    )

                    self.escala = novo_zoom
                    self.visual_largura = round(
                        self.imagem_largura * self.escala
                    )
                    self.visual_altura = round(
                        self.imagem_altura * self.escala
                    )
                    self.imagem_visual = pygame.transform.scale(
                        self.imagem,
                        (self.visual_largura, self.visual_altura)
                    )

'''

codigo = codigo[:inicio] + roda + codigo[fim:]

# 6. Eventos de teclado, retorno e redimensionamento.
codigo = codigo.replace(
    '''                if evento.key == pygame.K_ESCAPE:
                    self.executando = False

                elif evento.key == pygame.K_r:
''',
    '''                if evento.key == pygame.K_F11:
                    self.alternar_tela_cheia()

                elif evento.key == pygame.K_ESCAPE:
                    self.executando = False

                elif evento.key == pygame.K_r:
''',
    1
)

# Clique no botao de retorno antes das outras acoes do mouse.
codigo = codigo.replace(
    '''            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 2:
''',
    '''            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if (
                    evento.button == 1
                    and pygame.Rect(
                        self.largura - 190, 16, 166, 38
                    ).collidepoint(evento.pos)
                ):
                    self.voltar_central()

                elif evento.button == 2:
''',
    1
)

# Atualizar dimensoes quando a janela for redimensionada.
codigo = codigo.replace(
    '''            elif evento.type == pygame.MOUSEBUTTONDOWN:
''',
    '''            elif evento.type == pygame.VIDEORESIZE:
                if not self.tela_cheia:
                    self.largura, self.altura = evento.size
                    self.tela = pygame.display.set_mode(
                        evento.size, pygame.RESIZABLE
                    )
                    self.limite_visual = (
                        self.largura - self.largura_painel - 35
                    )

            elif evento.type == pygame.MOUSEBUTTONDOWN:
''',
    1
)

# 7. Salvar somente depois de validar.
backup = arquivo.with_name("editor_sprites.py.backup_scroll_retorno")
if backup.exists():
    sys.exit(f"Backup ja existe: {backup}. Nada alterado.")

temporario = arquivo.with_name("editor_sprites_patch.tmp")
temporario.write_text(codigo, encoding="utf-8")

try:
    py_compile.compile(str(temporario), doraise=True)
except Exception as erro:
    temporario.unlink(missing_ok=True)
    sys.exit(f"Falha na validacao. Original preservado: {erro}")

shutil.copy2(arquivo, backup)
temporario.replace(arquivo)

try:
    py_compile.compile(str(arquivo), doraise=True)
except Exception as erro:
    shutil.copy2(backup, arquivo)
    sys.exit(f"Falha final. Backup restaurado: {erro}")

print("Patch aplicado e validado!")
print(f"Backup: {backup}")
