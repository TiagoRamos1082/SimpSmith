from pathlib import Path
import py_compile
import shutil

arquivo = Path("editores/mapas/editor_recursos.py")
codigo = arquivo.read_text(encoding="utf-8")
original = codigo

def trocar(antigo, novo, descricao):
    global codigo
    if antigo not in codigo:
        raise SystemExit(f"Trecho não encontrado: {descricao}")
    codigo = codigo.replace(antigo, novo, 1)

# 1. Importar ctypes para maximizar a janela do Windows.
trocar(
    "import sys\nimport pygame\n",
    "import sys\nimport ctypes\nimport pygame\n",
    "importações"
)

# 2. Maximizar a janela sem entrar em tela cheia.
trocar(
    '''tela = pygame.display.set_mode(
    (LARGURA_JANELA, ALTURA_JANELA), pygame.RESIZABLE
)
''',
    '''tela = pygame.display.set_mode(
    (LARGURA_JANELA, ALTURA_JANELA), pygame.RESIZABLE
)

try:
    pygame.display.flip()
    hwnd = pygame.display.get_wm_info().get("window")
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 3)
except (AttributeError, OSError):
    pass
''',
    "maximização"
)

# 3. Paleta visual e dimensões da interface.
trocar(
    '''COR_TEXTO = (255, 255, 255)
COR_FUNDO = (25, 25, 25)
COR_SELECAO = (0, 255, 255)
''',
    '''COR_TEXTO = (241, 241, 241)
COR_FUNDO = (23, 25, 31)
COR_PAINEL = (34, 37, 45)
COR_PAINEL_CLARO = (43, 47, 57)
COR_DESTAQUE = (217, 155, 69)
COR_SECUNDARIA = (160, 165, 176)
COR_SELECAO = (245, 245, 245)

ALTURA_CABECALHO = 112
ALTURA_RODAPE = 36
''',
    "paleta visual"
)

# 4. Recalcular a câmera conforme a janela.
trocar(
    '''camera_y = (ALTURA_JANELA - IMG_ALTURA * escala) / 2

movendo_camera = False
''',
    '''camera_y = (ALTURA_JANELA - IMG_ALTURA * escala) / 2

def ajustar_camera_janela():
    global escala_base, escala, camera_x, camera_y

    largura, altura = tela.get_size()
    area_altura = max(
        100, altura - ALTURA_CABECALHO - ALTURA_RODAPE
    )

    escala_base = min(
        largura / IMG_LARGURA,
        area_altura / IMG_ALTURA
    )
    escala = escala_base * zoom

    camera_x = (largura - IMG_LARGURA * escala) / 2
    camera_y = (
        ALTURA_CABECALHO
        + (area_altura - IMG_ALTURA * escala) / 2
    )

movendo_camera = False
''',
    "câmera responsiva"
)

# 5. Impedir interação com as barras da interface.
trocar(
    '''def mouse_para_imagem(pos):
    x = (pos[0] - camera_x) / escala
''',
    '''def mouse_para_imagem(pos):
    if (
        pos[1] < ALTURA_CABECALHO
        or pos[1] >= tela.get_height() - ALTURA_RODAPE
    ):
        return None

    x = (pos[0] - camera_x) / escala
''',
    "área de interação do mapa"
)

# 6. Adicionar botão de retorno e tratamento de resize.
trocar(
    '''        elif evento.type == pygame.MOUSEWHEEL:


            pos = pygame.mouse.get_pos()
''',
    '''        elif evento.type == pygame.VIDEORESIZE:
            ajustar_camera_janela()

        elif evento.type == pygame.MOUSEWHEEL:
            pos = pygame.mouse.get_pos()
''',
    "redimensionamento"
)

trocar(
    '''        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 2:
''',
    '''        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:
                botao_voltar = pygame.Rect(
                    tela.get_width() - 190, 12, 170, 42
                )
                if botao_voltar.collidepoint(evento.pos):
                    executando = False
                    continue

            if evento.button == 2:
''',
    "clique no botão de retorno"
)

# 7. Substituir a renderização antiga por uma interface organizada.
inicio = codigo.index('    tela.fill((35, 35, 35))')
fim = codigo.index('    pygame.display.flip()', inicio)

renderizacao = '''    tela.fill(COR_FUNDO)

    largura_tela, altura_tela = tela.get_size()

    largura = max(1, round(IMG_LARGURA * escala))
    altura = max(1, round(IMG_ALTURA * escala))

    imagem = pygame.transform.scale(
        imagem_original,
        (largura, altura),
    )

    tela.blit(imagem, (round(camera_x), round(camera_y)))

    # Áreas de recursos
    for indice, item in enumerate(areas):
        rect = obter_rect(item)
        visual = area_para_tela(rect)
        cor = RECURSOS[item["tipo"]]["cor"]

        if mostrar_bordas:
            pygame.draw.rect(tela, cor, visual, 2)

            desenhar_texto(
                f"{indice + 1}: {RECURSOS[item['tipo']]['nome']}",
                visual.x + 3,
                visual.y + 3,
                cor,
                pequena=True,
            )

        if indice == area_selecionada:
            pygame.draw.rect(tela, COR_SELECAO, visual, 3)

    # Área sendo desenhada
    if arrastando and inicio is not None and fim is not None:
        rect = retangulo_arrastado(inicio, fim)
        visual = area_para_tela(rect)

        pygame.draw.rect(
            tela,
            RECURSOS[tipo_atual]["cor"],
            visual,
            2,
        )

    # Cabeçalho
    pygame.draw.rect(
        tela, COR_PAINEL,
        (0, 0, largura_tela, ALTURA_CABECALHO)
    )
    pygame.draw.line(
        tela, COR_PAINEL_CLARO,
        (0, ALTURA_CABECALHO - 1),
        (largura_tela, ALTURA_CABECALHO - 1),
        1,
    )

    desenhar_texto(
        "SIMP SMITH", 20, 12, COR_DESTAQUE
    )
    desenhar_texto(
        "EDITOR DE RECURSOS", 20, 39,
        COR_SECUNDARIA, pequena=True
    )

    desenhar_texto(
        f"Recurso atual: {RECURSOS[tipo_atual]['nome']}",
        230, 13, COR_TEXTO
    )

    desenhar_texto(
        "Clique e arraste: criar área | Clique: selecionar | "
        "Botão direito: remover | Scroll: zoom | Meio: mover",
        230, 43, COR_SECUNDARIA, pequena=True
    )

    legendas = []
    for indice, tipo in enumerate(tipos_disponiveis[:9]):
        legendas.append(
            f"{indice + 1}: {RECURSOS[tipo]['nome']}"
        )

    desenhar_texto(
        "Recursos: " + "  |  ".join(legendas)
        + "  |  TAB: próximo",
        230, 68, COR_SECUNDARIA, pequena=True
    )

    # Botão voltar à Central
    botao_voltar = pygame.Rect(
        largura_tela - 190, 12, 170, 42
    )

    pygame.draw.rect(
        tela, COR_PAINEL_CLARO,
        botao_voltar, border_radius=7
    )
    pygame.draw.rect(
        tela, COR_DESTAQUE,
        botao_voltar, width=1, border_radius=7
    )

    texto_voltar = fonte_pequena.render(
        "< VOLTAR À CENTRAL", True, COR_TEXTO
    )
    tela.blit(
        texto_voltar,
        texto_voltar.get_rect(center=botao_voltar.center)
    )

    # Informações da área selecionada
    if area_selecionada is not None:
        item = areas[area_selecionada]
        nome = RECURSOS[item["tipo"]]["nome"]

        info = (
            f"Selecionada: {nome}  |  Máximo: {item['maximo']}  |  "
            f"Inicial: {item['inicial']}  |  "
            f"Respawn: {item['respawn']:.0f}s"
        )
    else:
        info = (
            f"Tipo atual: {RECURSOS[tipo_atual]['nome']}  |  "
            f"Áreas cadastradas: {len(areas)}"
        )

    desenhar_texto(
        info, 20, 90, COR_TEXTO, pequena=True
    )

    # Rodapé
    y_rodape = altura_tela - ALTURA_RODAPE

    pygame.draw.rect(
        tela, COR_PAINEL,
        (0, y_rodape, largura_tela, ALTURA_RODAPE)
    )
    pygame.draw.line(
        tela, COR_PAINEL_CLARO,
        (0, y_rodape),
        (largura_tela, y_rodape), 1
    )

    desenhar_texto(
        f"Áreas: {len(areas)}  |  Zoom: {zoom:.2f}x  |  "
        "B: bordas  |  Ctrl+S: salvar  |  ESC: sair",
        20, y_rodape + 10, COR_SECUNDARIA, pequena=True
    )

    if pygame.time.get_ticks() < tempo_mensagem:
        superficie_mensagem = fonte_pequena.render(
            mensagem, True, COR_DESTAQUE
        )
        tela.blit(
            superficie_mensagem,
            (
                largura_tela - superficie_mensagem.get_width() - 20,
                y_rodape + 10,
            )
        )

'''

codigo = codigo[:inicio] + renderizacao + codigo[fim:]

if codigo == original:
    raise SystemExit("Nenhuma alteração foi aplicada.")

temporario = arquivo.with_name("editor_recursos_temp.py")
temporario.write_text(codigo, encoding="utf-8")
py_compile.compile(str(temporario), doraise=True)

backup = Path("backups/editor_recursos_antes_visual.py")
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(arquivo, backup)

temporario.replace(arquivo)

print("Editor de Recursos atualizado!")
print(f"Backup criado: {backup}")
print("Sintaxe validada com sucesso.")
