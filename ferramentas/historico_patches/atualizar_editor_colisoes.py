from pathlib import Path
import py_compile
import shutil

arquivo = Path("editores/mapas/editor_colisoes.py")
codigo = arquivo.read_text(encoding="utf-8")
original = codigo

def substituir(antigo, novo, descricao):
    global codigo
    if antigo not in codigo:
        raise SystemExit(f"Não foi possível localizar: {descricao}")
    codigo = codigo.replace(antigo, novo, 1)

# 1. Importações e maximização
substituir(
    "import json\nfrom pathlib import Path\nimport pygame\n",
    "import json\nimport ctypes\nfrom pathlib import Path\nimport pygame\n",
    "importações"
)

substituir(
    'tela = pygame.display.set_mode((1100, 650), pygame.RESIZABLE)\n'
    'pygame.display.set_caption("SimpSmith - Editor de Colisoes")\n',
    'tela = pygame.display.set_mode((1100, 650), pygame.RESIZABLE)\n'
    'pygame.display.set_caption("SimpSmith - Editor de Colisões")\n'
    '\n'
    '# Maximiza a janela mantendo bordas e barra de tarefas.\n'
    'try:\n'
    '    hwnd = pygame.display.get_wm_info().get("window")\n'
    '    if hwnd:\n'
    '        ctypes.windll.user32.ShowWindow(hwnd, 3)\n'
    'except (AttributeError, OSError):\n'
    '    pass\n',
    "criação da janela"
)

# 2. Paleta visual
substituir(
    'FUNDO = (35, 35, 35)\n'
    'COR_TEXTO = (255, 255, 255)\n'
    'COR_OBSTACULO = (255, 50, 50)\n'
    'COR_INTERACAO = (30, 150, 255)\n'
    'COR_SPRITE = (255, 190, 30)\n'
    'COR_SELECAO = (255, 255, 255)\n',
    'FUNDO = (23, 25, 31)\n'
    'PAINEL = (34, 37, 45)\n'
    'PAINEL_CLARO = (43, 47, 57)\n'
    'COR_DESTAQUE = (217, 155, 69)\n'
    'COR_TEXTO = (241, 241, 241)\n'
    'COR_SECUNDARIA = (160, 165, 176)\n'
    'COR_OBSTACULO = (235, 91, 91)\n'
    'COR_INTERACAO = (75, 158, 230)\n'
    'COR_SPRITE = (235, 180, 75)\n'
    'COR_SELECAO = (245, 245, 245)\n'
    'ALTURA_CABECALHO = 76\n'
    'ALTURA_RODAPE = 34\n',
    "paleta de cores"
)

# 3. Área útil do mapa, reservando cabeçalho e rodapé
substituir(
    '''def area_imagem():
    largura, altura = tela.get_size()

    escala_base = min(
        largura / IMG_LARGURA,
        altura / IMG_ALTURA
    )

    escala = escala_base * zoom

    w = max(1, round(IMG_LARGURA * escala))
    h = max(1, round(IMG_ALTURA * escala))

    x = (largura - w) // 2 + round(pan_x)
    y = (altura - h) // 2 + round(pan_y)

    return pygame.Rect(x, y, w, h), escala
''',
    '''def area_imagem():
    largura, altura = tela.get_size()

    area_topo = ALTURA_CABECALHO
    area_altura = max(100, altura - ALTURA_CABECALHO - ALTURA_RODAPE)

    escala_base = min(
        largura / IMG_LARGURA,
        area_altura / IMG_ALTURA
    )

    escala = escala_base * zoom

    w = max(1, round(IMG_LARGURA * escala))
    h = max(1, round(IMG_ALTURA * escala))

    x = (largura - w) // 2 + round(pan_x)
    y = area_topo + (area_altura - h) // 2 + round(pan_y)

    return pygame.Rect(x, y, w, h), escala
''',
    "cálculo da área do mapa"
)

# 4. Ajustar zoom para considerar a área útil
substituir(
    '''                escala_base = min(
                    tela.get_width() / IMG_LARGURA,
                    tela.get_height() / IMG_ALTURA
                )
''',
    '''                altura_util = max(
                    100,
                    tela.get_height() - ALTURA_CABECALHO - ALTURA_RODAPE
                )

                escala_base = min(
                    tela.get_width() / IMG_LARGURA,
                    altura_util / IMG_ALTURA
                )
''',
    "escala do zoom"
)

# 5. Substituir cabeçalho antigo por interface organizada
inicio = codigo.index("    # BARRA SUPERIOR")
fim = codigo.index('    pygame.display.flip()', inicio)

interface = '''    # ======================================================
    # INTERFACE
    # ======================================================

    largura_tela, altura_tela = tela.get_size()

    # Cabeçalho
    pygame.draw.rect(
        tela, PAINEL,
        (0, 0, largura_tela, ALTURA_CABECALHO)
    )
    pygame.draw.line(
        tela, PAINEL_CLARO,
        (0, ALTURA_CABECALHO - 1),
        (largura_tela, ALTURA_CABECALHO - 1), 1
    )

    titulo = fonte.render("SIMP SMITH", True, COR_DESTAQUE)
    subtitulo = fonte_pequena.render(
        "EDITOR DE COLISOES", True, COR_SECUNDARIA
    )
    tela.blit(titulo, (20, 12))
    tela.blit(subtitulo, (20, 39))

    nome_modo = {
        "mapa": "COLISAO DO MAPA",
        "interacao": "AREAS DE INTERACAO",
        "sprite": "COLISAO DOS SPRITES"
    }[modo]

    texto_modo = fonte.render(nome_modo, True, COR_TEXTO)
    tela.blit(
        texto_modo,
        (220, 15)
    )

    # Atalhos em uma segunda linha
    atalhos = (
        "1 Mapa   2 Interacao   3 Sprite     "
        "Esquerdo: criar/selecionar   Direito: apagar   "
        "Meio: mover   Scroll: zoom"
    )

    texto_atalhos = fonte_pequena.render(
        atalhos, True, COR_SECUNDARIA
    )
    tela.blit(texto_atalhos, (220, 43))

    if modo == "sprite":
        nome = sprite_selecionado or "Nenhum selecionado"
        texto_sprite = fonte_pequena.render(
            f"Sprite: {nome}", True, COR_SPRITE
        )
        tela.blit(
            texto_sprite,
            (largura_tela - texto_sprite.get_width() - 20, 15)
        )

    # Rodapé
    y_rodape = altura_tela - ALTURA_RODAPE
    pygame.draw.rect(
        tela, PAINEL,
        (0, y_rodape, largura_tela, ALTURA_RODAPE)
    )
    pygame.draw.line(
        tela, PAINEL_CLARO,
        (0, y_rodape),
        (largura_tela, y_rodape), 1
    )

    status = (
        f"Obstaculos: {len(obstaculos)}   |   "
        f"Areas de interacao: {len(areas_interacao)}   |   "
        f"Zoom: {zoom:.2f}x"
    )

    texto_status = fonte_pequena.render(
        status, True, COR_SECUNDARIA
    )
    tela.blit(texto_status, (20, y_rodape + 10))

    dicas = "B: bordas  |  G: grade  |  Ctrl+S: salvar  |  ESC: sair"
    texto_dicas = fonte_pequena.render(
        dicas, True, COR_SECUNDARIA
    )
    tela.blit(
        texto_dicas,
        (largura_tela - texto_dicas.get_width() - 20, y_rodape + 10)
    )

'''
codigo = codigo[:inicio] + interface + codigo[fim:]

if codigo == original:
    raise SystemExit("Nenhuma alteração foi aplicada.")

temporario = arquivo.with_name("editor_colisoes_temp.py")
temporario.write_text(codigo, encoding="utf-8")
py_compile.compile(str(temporario), doraise=True)

backup = Path("backups/editor_colisoes_antes_visual.py")
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(arquivo, backup)

temporario.replace(arquivo)

print("Editor de Colisões atualizado e sintaxe validada!")
print(f"Backup criado em: {backup}")

