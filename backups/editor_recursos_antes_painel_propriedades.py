
import json
import os
import sys
import ctypes
import pygame

pygame.init()

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from sistemas.catalogo_itens import CatalogoItens

CAMINHO_MAPA = os.path.join(RAIZ, "dados", "mapas", "mapa_principal.json")
CAMINHO_SPRITES = os.path.join(RAIZ, "assets", "tiles", "superior")
CAMINHO_AREAS = os.path.join(RAIZ, "mapa", "areas_minerios.json")

if not os.path.isfile(CAMINHO_MAPA):
    raise FileNotFoundError(f"Mapa nao encontrado: {CAMINHO_MAPA}")

    raise FileNotFoundError(f"Imagem nÃ£o encontrada: {CAMINHO_IMAGEM}")

catalogo = CatalogoItens()


def carregar_recursos():
    itens = [
        item for item in catalogo.listar()
        if item["categoria"] in {"minerio", "planta"}
    ]

    resultado = {}

    for item in itens:
        resultado[item["id"]] = {
            "nome": item["nome"],
            "cor": tuple(item["cor"]),
            "maximo": 3,
            "respawn": 20.0,
            "inicial": 3,
            "pode_respawn": item.get("respawn", True),
        }

    return resultado


RECURSOS = carregar_recursos()

if not RECURSOS:
    raise ValueError(
        "Nenhum recurso das categorias 'minerio' ou 'planta' "
        "foi encontrado em dados/itens.json."
    )


LARGURA_JANELA = 1024
ALTURA_JANELA = 576
pygame.display.set_caption("SimpSmith - Editor de Recursos")

tela = pygame.display.set_mode(
    (LARGURA_JANELA, ALTURA_JANELA), pygame.RESIZABLE
)

try:
    pygame.display.flip()
    hwnd = pygame.display.get_wm_info().get("window")
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 3)
except (AttributeError, OSError):
    pass

with open(CAMINHO_MAPA, "r", encoding="utf-8-sig") as arquivo_mapa:
    dados_mapa = json.load(arquivo_mapa)

TAMANHO_TILE = dados_mapa["tile_size"]
IMG_LARGURA = dados_mapa["largura"] * TAMANHO_TILE
IMG_ALTURA = dados_mapa["altura"] * TAMANHO_TILE

imagem_original = pygame.Surface((IMG_LARGURA, IMG_ALTURA))
imagem_original.fill((35, 35, 40))

# Desenha as camadas do mapa.
for nome_camada, grade in dados_mapa["camadas"].items():
    for y, linha in enumerate(grade):
        for x, identificador in enumerate(linha):
            if identificador is None:
                continue

            informacoes = dados_mapa["tiles"][identificador]
            pygame.draw.rect(
                imagem_original,
                tuple(informacoes["cor"]),
                (
                    x * TAMANHO_TILE,
                    y * TAMANHO_TILE,
                    TAMANHO_TILE,
                    TAMANHO_TILE,
                ),
            )

# Carrega os sprites superiores.
sprites = {}

if os.path.isdir(CAMINHO_SPRITES):
    for raiz, _, arquivos in os.walk(CAMINHO_SPRITES):
        for nome_arquivo in arquivos:
            if not nome_arquivo.lower().endswith(".png"):
                continue

            caminho = os.path.join(raiz, nome_arquivo)
            identificador = os.path.relpath(
                caminho, CAMINHO_SPRITES
            )[:-4].replace(os.sep, "/")

            sprites[identificador] = pygame.image.load(
                caminho
            ).convert_alpha()

# Desenha os sprites nas coordenadas do mapa.
for sprite in dados_mapa.get("sprites_superiores", []):
    imagem_sprite = sprites.get(sprite["id"])

    if imagem_sprite is not None:
        imagem_original.blit(
            imagem_sprite,
            (sprite["x"], sprite["y"]),
        )

relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("arial", 16)
fonte_pequena = pygame.font.SysFont("arial", 13)

COR_TEXTO = (241, 241, 241)
COR_FUNDO = (23, 25, 31)
COR_PAINEL = (34, 37, 45)
COR_PAINEL_CLARO = (43, 47, 57)
COR_DESTAQUE = (217, 155, 69)
COR_SECUNDARIA = (160, 165, 176)
COR_SELECAO = (245, 245, 245)

ALTURA_CABECALHO = 112
ALTURA_RODAPE = 36

tipos_disponiveis = list(RECURSOS.keys())
tipo_atual = tipos_disponiveis[0]

mostrar_bordas = True
areas = []
area_selecionada = None
arrastando = False
inicio = None
fim = None
mensagem = ""
tempo_mensagem = 0



# C?mera do mapa
ZOOM_MINIMO = 0.25
ZOOM_MAXIMO = 4.0
FATOR_ZOOM = 1.15

escala_base = min(
    LARGURA_JANELA / IMG_LARGURA,
    ALTURA_JANELA / IMG_ALTURA,
)
zoom = 1.0
escala = escala_base

camera_x = (LARGURA_JANELA - IMG_LARGURA * escala) / 2
camera_y = (ALTURA_JANELA - IMG_ALTURA * escala) / 2

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
ultima_posicao_mouse = None

def carregar_areas():
    if not os.path.isfile(CAMINHO_AREAS):
        return

    try:
        with open(CAMINHO_AREAS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        if not isinstance(dados, dict) or not isinstance(
            dados.get("areas", []), list
        ):
            raise ValueError("O arquivo precisa conter uma lista 'areas'.")

        largura_antiga = int(dados.get("largura_imagem", IMG_LARGURA))
        altura_antiga = int(dados.get("altura_imagem", IMG_ALTURA))

        if largura_antiga <= 0 or altura_antiga <= 0:
            raise ValueError("Dimensoes antigas invalidas.")

        fator_x = IMG_LARGURA / largura_antiga
        fator_y = IMG_ALTURA / altura_antiga

        for item in dados.get("areas", []):
            tipo = item["tipo"]

            if tipo not in RECURSOS:
                raise ValueError(
                    f"O tipo '{tipo}' das Ã¡reas nÃ£o existe no catÃ¡logo "
                    "como recurso (minerio ou planta). "
                    "Cadastre-o em dados/itens.json ou corrija a Ã¡rea."
                )

            x = round(int(item["x"]) * fator_x)
            y = round(int(item["y"]) * fator_y)
            largura = round(int(item["largura"]) * fator_x)
            altura = round(int(item["altura"]) * fator_y)
            config = RECURSOS[tipo]

            maximo = int(item.get("maximo", config["maximo"]))
            inicial = int(item.get("inicial", min(config["inicial"], maximo)))
            respawn = float(item.get("respawn", config["respawn"]))

            if largura <= 0 or altura <= 0:
                raise ValueError("Ãrea com dimensÃµes invÃ¡lidas.")

            if maximo < 1 or not 0 <= inicial <= maximo:
                raise ValueError("Limite ou quantidade inicial invÃ¡lida.")

            if respawn <= 0:
                raise ValueError("O tempo de respawn precisa ser positivo.")

            areas.append({
                "x": x,
                "y": y,
                "largura": largura,
                "altura": altura,
                "tipo": tipo,
                "maximo": maximo,
                "inicial": inicial,
                "respawn": respawn,
            })

    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as erro:
        raise ValueError(
            f"NÃ£o foi possÃ­vel carregar {CAMINHO_AREAS}: {erro}"
        ) from erro


def avisar(texto):
    global mensagem, tempo_mensagem
    mensagem = texto
    tempo_mensagem = pygame.time.get_ticks() + 2500


def salvar():
    dados = {
        "largura_imagem": IMG_LARGURA,
        "altura_imagem": IMG_ALTURA,
        "areas": areas,
    }

    temporario = CAMINHO_AREAS + ".tmp"

    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)
        arquivo.write("\n")

    os.replace(temporario, CAMINHO_AREAS)
    avisar(f"{len(areas)} Ã¡reas salvas!")


def atualizar_escala():
    global escala
    escala = escala_base * zoom


def mouse_para_imagem(pos):
    if (
        pos[1] < ALTURA_CABECALHO
        or pos[1] >= tela.get_height() - ALTURA_RODAPE
    ):
        return None

    x = (pos[0] - camera_x) / escala
    y = (pos[1] - camera_y) / escala

    if not (0 <= x < IMG_LARGURA and 0 <= y < IMG_ALTURA):
        return None

    return round(x), round(y)


def retangulo_arrastado(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    return pygame.Rect(
        min(x1, x2),
        min(y1, y2),
        abs(x2 - x1),
        abs(y2 - y1),
    )


def area_para_tela(retangulo):
    return pygame.Rect(
        round(camera_x + retangulo.x * escala),
        round(camera_y + retangulo.y * escala),
        max(1, round(retangulo.width * escala)),
        max(1, round(retangulo.height * escala)),
    )


def obter_rect(item):
    return pygame.Rect(
        item["x"],
        item["y"],
        item["largura"],
        item["altura"],
    )


def selecionar_area(pos):
    ponto = mouse_para_imagem(pos)

    if ponto is None:
        return None

    px, py = ponto

    for indice in range(len(areas) - 1, -1, -1):
        if obter_rect(areas[indice]).collidepoint(px, py):
            return indice

    return None


def criar_area(rect):
    if rect.width < 3 or rect.height < 3:
        avisar("Ãrea muito pequena.")
        return

    config = RECURSOS[tipo_atual]

    areas.append({
        "x": rect.x,
        "y": rect.y,
        "largura": rect.width,
        "altura": rect.height,
        "tipo": tipo_atual,
        "maximo": config["maximo"],
        "inicial": min(config["inicial"], config["maximo"]),
        "respawn": config["respawn"],
    })

    global area_selecionada
    area_selecionada = len(areas) - 1

    salvar()


def remover_area(indice):
    global area_selecionada

    del areas[indice]

    if not areas:
        area_selecionada = None

    elif area_selecionada is not None:
        if area_selecionada == indice:
            area_selecionada = None
        elif area_selecionada > indice:
            area_selecionada -= 1

    salvar()


def alterar_configuracao(campo, valor):
    if area_selecionada is None:
        avisar("Selecione uma Ã¡rea primeiro.")
        return

    item = areas[area_selecionada]
    novo_valor = item[campo] + valor

    if campo == "maximo":
        novo_valor = max(1, min(100, novo_valor))
        item["maximo"] = novo_valor
        item["inicial"] = min(item["inicial"], novo_valor)

    elif campo == "inicial":
        item["inicial"] = max(0, min(item["maximo"], novo_valor))

    elif campo == "respawn":
        item["respawn"] = float(max(1.0, min(3600.0, novo_valor)))

    salvar()


def desenhar_texto(texto, x, y, cor=COR_TEXTO, pequena=False):
    fonte_usada = fonte_pequena if pequena else fonte
    superficie = fonte_usada.render(texto, True, cor)
    tela.blit(superficie, (x, y))


def selecionar_tipo_por_indice(indice):
    global tipo_atual

    if 0 <= indice < len(tipos_disponiveis):
        tipo_atual = tipos_disponiveis[indice]
        avisar(f"Recurso selecionado: {RECURSOS[tipo_atual]['nome']}")


carregar_areas()
executando = True

while executando:
    relogio.tick(60)

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            executando = False

        elif evento.type == pygame.VIDEORESIZE:
            ajustar_camera_janela()

        elif evento.type == pygame.MOUSEWHEEL:
            pos = pygame.mouse.get_pos()


            zoom_anterior = zoom


        


            if evento.y > 0:


                zoom = min(ZOOM_MAXIMO, zoom * FATOR_ZOOM)


            elif evento.y < 0:


                zoom = max(ZOOM_MINIMO, zoom / FATOR_ZOOM)


        


            if zoom != zoom_anterior:


                fator = zoom / zoom_anterior


                camera_x = pos[0] - (pos[0] - camera_x) * fator


                camera_y = pos[1] - (pos[1] - camera_y) * fator


                atualizar_escala()


        


        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                executando = False

            elif evento.key == pygame.K_b:
                mostrar_bordas = not mostrar_bordas

            elif evento.key == pygame.K_s and (
                pygame.key.get_mods() & pygame.KMOD_CTRL
            ):
                salvar()

            elif evento.key == pygame.K_TAB:
                indice = tipos_disponiveis.index(tipo_atual)
                selecionar_tipo_por_indice(
                    (indice + 1) % len(tipos_disponiveis)
                )

            elif pygame.K_1 <= evento.key <= pygame.K_9:
                selecionar_tipo_por_indice(evento.key - pygame.K_1)

            elif evento.key == pygame.K_DELETE and area_selecionada is not None:
                remover_area(area_selecionada)

            elif evento.key == pygame.K_UP:
                alterar_configuracao("maximo", 1)

            elif evento.key == pygame.K_DOWN:
                alterar_configuracao("maximo", -1)

            elif evento.key == pygame.K_RIGHT:
                alterar_configuracao("respawn", 1)

            elif evento.key == pygame.K_LEFT:
                alterar_configuracao("respawn", -1)

            elif evento.key == pygame.K_PAGEUP:
                alterar_configuracao("inicial", 1)

            elif evento.key == pygame.K_PAGEDOWN:
                alterar_configuracao("inicial", -1)

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:
                botao_voltar = pygame.Rect(
                    tela.get_width() - 190, 12, 170, 42
                )
                if botao_voltar.collidepoint(evento.pos):
                    executando = False
                    continue

            if evento.button == 2:
                movendo_camera = True
                ultima_posicao_mouse = evento.pos
            
            elif evento.button == 1:
                indice = selecionar_area(evento.pos)

                if indice is not None:
                    area_selecionada = indice

                else:
                    ponto = mouse_para_imagem(evento.pos)

                    if ponto is not None:
                        inicio = ponto
                        fim = ponto
                        arrastando = True
                        area_selecionada = None

            elif evento.button == 3:
                indice = selecionar_area(evento.pos)

                if indice is not None:
                    remover_area(indice)

        elif evento.type == pygame.MOUSEMOTION:
                if movendo_camera:
                    dx = evento.pos[0] - ultima_posicao_mouse[0]
                    dy = evento.pos[1] - ultima_posicao_mouse[1]
                    camera_x += dx
                    camera_y += dy
                    ultima_posicao_mouse = evento.pos

                elif arrastando:
                    ponto = mouse_para_imagem(evento.pos)
                    if ponto is not None:
                        fim = ponto

            

        elif evento.type == pygame.MOUSEBUTTONUP:
            if evento.button == 2:
                movendo_camera = False
                ultima_posicao_mouse = None
            
            elif evento.button == 1 and arrastando:
                ponto = mouse_para_imagem(evento.pos)

                if ponto is not None:
                    fim = ponto

                if inicio is not None and fim is not None:
                    criar_area(retangulo_arrastado(inicio, fim))

                arrastando = False
                inicio = None
                fim = None

    tela.fill(COR_FUNDO)

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

    pygame.display.flip()

pygame.quit()


