
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
from sistemas.carregador_imagens import obter_imagem
from mapa.renderizador_mapa import RenderizadorMapa

CAMINHO_MAPA = os.path.join(RAIZ, "dados", "mapas", "mapa_principal.json")
CAMINHO_SPRITES = os.path.join(RAIZ, "assets", "tiles", "superior")
CAMINHO_AREAS = os.path.join(RAIZ, "mapa", "areas_minerios.json")
CAMINHO_OBJETOS = os.path.join(RAIZ, "mapa", "objetos_mapa.json")

if not os.path.isfile(CAMINHO_MAPA):
    raise FileNotFoundError(f"Mapa nao encontrado: {CAMINHO_MAPA}")

catalogo = CatalogoItens()


def carregar_recursos():
    itens = [
        item for item in catalogo.listar()
        if item["categoria"] == "minerio"
    ]

    resultado = {}

    for item in itens:
        resultado[item["id"]] = {
            "nome": item["nome"],
            "cor": tuple(item["cor"]),
            "imagem": item.get("imagem"),
            "largura_visual": item["largura_visual"],
            "altura_visual": item["altura_visual"],
            "maximo": 3,
            "respawn": 20.0,
            "inicial": 3,
            "pode_respawn": item.get("respawn", True),
        }

    return resultado


RECURSOS = carregar_recursos()


def carregar_construcoes():
    resultado = {}

    for item in catalogo.listar():
        if item["categoria"] not in {"item", "construcao"}:
            continue

        if not item.get("imagem"):
            continue

        resultado[item["id"]] = {
            "nome": item["nome"],
            "cor": tuple(item["cor"]),
            "imagem": item["imagem"],
            "largura_visual": item["largura_visual"],
            "altura_visual": item["altura_visual"],
        }

    return resultado


CONSTRUCOES = carregar_construcoes()

if not RECURSOS and not CONSTRUCOES:
    raise ValueError(
        "Nenhum item das categorias 'minerio', 'item' ou 'construcao' "
        "com imagem foi encontrado em dados/itens/itens.json."
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

# ==========================================================
# RENDERIZACAO DO MAPA
# Utiliza o mesmo renderizador do jogo principal.
# ==========================================================

renderizador_mapa = RenderizadorMapa(RAIZ, dados_mapa)

imagem_original = pygame.Surface(
    (IMG_LARGURA, IMG_ALTURA)
)

imagem_original.fill((35, 35, 40))

# Mantem a ordem oficial das camadas:
# tiles da camada -> sprites da camada.
for nome_camada in renderizador_mapa.camadas:
    renderizador_mapa.desenhar_tiles_camada(
        imagem_original,
        nome_camada
    )

    renderizador_mapa.desenhar_sprites_camada(
        imagem_original,
        nome_camada
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

ALTURA_CABECALHO = 64
ALTURA_RODAPE = 36

LARGURA_PAINEL_ESQUERDO = 190
LARGURA_PAINEL_DIREITO = 250

modo_editor = "recursos" if RECURSOS else "construcoes"
tipos_disponiveis = list(RECURSOS.keys() if RECURSOS else CONSTRUCOES.keys())
tipo_atual = tipos_disponiveis[0]
deslocamento_lista_recursos = 0

objetos_mapa = []
objeto_selecionado = None

mostrar_bordas = True
mostrar_grade = False
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

camera_x = 0
camera_y = 0

def ajustar_camera_janela():
    global escala_base, escala, camera_x, camera_y

    largura, altura = tela.get_size()

    area_largura = max(
        100,
        largura - LARGURA_PAINEL_ESQUERDO - LARGURA_PAINEL_DIREITO,
    )

    area_altura = max(
        100,
        altura - ALTURA_CABECALHO - ALTURA_RODAPE,
    )

    escala_base = min(
        area_largura / IMG_LARGURA,
        area_altura / IMG_ALTURA,
    )

    escala = escala_base * zoom

    camera_x = (
        LARGURA_PAINEL_ESQUERDO
        + (area_largura - IMG_LARGURA * escala) / 2
    )

    camera_y = (
        ALTURA_CABECALHO
        + (area_altura - IMG_ALTURA * escala) / 2
    )

ajustar_camera_janela()

movendo_camera = False
ultima_posicao_mouse = None

def carregar_objetos_mapa():
    global objetos_mapa

    if not os.path.isfile(CAMINHO_OBJETOS):
        objetos_mapa = []
        return

    with open(CAMINHO_OBJETOS, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    registros = dados.get("objetos", [])
    if not isinstance(registros, list):
        raise ValueError("objetos_mapa.json precisa conter uma lista 'objetos'.")

    objetos_mapa = []

    for registro in registros:
        identificador = registro["id"]

        if identificador not in CONSTRUCOES:
            raise ValueError(
                f"Objeto '{identificador}' não existe na biblioteca de construções."
            )

        largura = CONSTRUCOES[identificador]["largura_visual"]
        altura = CONSTRUCOES[identificador]["altura_visual"]

        x = int(registro["x"])
        y = int(registro["y"])

        if x < 0 or y < 0 or x + largura > IMG_LARGURA or y + altura > IMG_ALTURA:
            raise ValueError(
                f"Objeto '{identificador}' está fora dos limites do mapa."
            )

        objetos_mapa.append({
            "id": identificador,
            "x": x,
            "y": y,
        })


def salvar_objetos_mapa():
    dados = {"objetos": objetos_mapa}
    temporario = CAMINHO_OBJETOS + ".tmp"

    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)
        arquivo.write("\n")

    os.replace(temporario, CAMINHO_OBJETOS)
    avisar(f"{len(objetos_mapa)} construções salvas!")


def alternar_modo_editor(novo_modo):
    global modo_editor, tipos_disponiveis, tipo_atual
    global area_selecionada, objeto_selecionado
    global arrastando, inicio, fim, deslocamento_lista_recursos

    if novo_modo == modo_editor:
        return

    modo_editor = novo_modo
    tipos_disponiveis = list(
        RECURSOS if modo_editor == "recursos" else CONSTRUCOES
    )

    if tipos_disponiveis:
        tipo_atual = tipos_disponiveis[0]

    area_selecionada = None
    objeto_selecionado = None
    arrastando = False
    inicio = None
    fim = None
    deslocamento_lista_recursos = 0

    nome = "Recursos" if modo_editor == "recursos" else "Construções"
    avisar(f"Modo {nome}.")


def obter_configuracao_atual():
    biblioteca = RECURSOS if modo_editor == "recursos" else CONSTRUCOES
    return biblioteca[tipo_atual]


def obter_rect_objeto(registro):
    config = CONSTRUCOES[registro["id"]]
    return pygame.Rect(
        registro["x"],
        registro["y"],
        config["largura_visual"],
        config["altura_visual"],
    )


def selecionar_objeto(pos):
    ponto = mouse_para_imagem(pos)

    if ponto is None:
        return None

    for indice in range(len(objetos_mapa) - 1, -1, -1):
        if obter_rect_objeto(objetos_mapa[indice]).collidepoint(ponto):
            return indice

    return None


def posicionar_construcao(pos):
    ponto = mouse_para_imagem(pos)

    if ponto is None:
        return

    config = CONSTRUCOES[tipo_atual]
    largura = config["largura_visual"]
    altura = config["altura_visual"]

    x = ponto[0] - largura // 2
    y = ponto[1] - altura // 2

    x = max(0, min(IMG_LARGURA - largura, x))
    y = max(0, min(IMG_ALTURA - altura, y))

    objetos_mapa.append({
        "id": tipo_atual,
        "x": x,
        "y": y,
    })

    global objeto_selecionado
    objeto_selecionado = len(objetos_mapa) - 1
    salvar_objetos_mapa()


def remover_objeto(indice):
    global objeto_selecionado

    del objetos_mapa[indice]

    if not objetos_mapa:
        objeto_selecionado = None
    elif objeto_selecionado is not None:
        if objeto_selecionado == indice:
            objeto_selecionado = None
        elif objeto_selecionado > indice:
            objeto_selecionado -= 1

    salvar_objetos_mapa()


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
                    "com categoria minerio. "
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
    largura, altura = tela.get_size()

    if (
        pos[0] < LARGURA_PAINEL_ESQUERDO
        or pos[0] >= largura - LARGURA_PAINEL_DIREITO
        or pos[1] < ALTURA_CABECALHO
        or pos[1] >= altura - ALTURA_RODAPE
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


def obter_botoes_propriedades(largura, y):
    botoes = {}
    x_painel = largura - LARGURA_PAINEL_DIREITO

    for indice, campo in enumerate(("maximo", "inicial", "respawn")):
        y_linha = y + 72 + indice * 105

        botoes[campo] = {
            "menos": pygame.Rect(x_painel + 16, y_linha + 26, 34, 30),
            "mais": pygame.Rect(x_painel + 200, y_linha + 26, 34, 30),
            "centro": (x_painel + 125, y_linha + 41),
        }

    return botoes



def selecionar_tipo_por_indice(indice):
    global tipo_atual

    if 0 <= indice < len(tipos_disponiveis):
        tipo_atual = tipos_disponiveis[indice]
        config = obter_configuracao_atual()
        avisar(f"Selecionado: {config['nome']}")


def obter_cartoes_recursos():
    global deslocamento_lista_recursos

    topo = ALTURA_CABECALHO + 36
    base = tela.get_height() - ALTURA_RODAPE
    altura_disponivel = max(0, base - topo)
    altura_conteudo = max(0, len(tipos_disponiveis) * 70 - 8)
    deslocamento_maximo = max(0, altura_conteudo - altura_disponivel)

    deslocamento_lista_recursos = max(
        0, min(deslocamento_lista_recursos, deslocamento_maximo)
    )

    return {
        tipo: pygame.Rect(
            10,
            topo + indice * 70 - deslocamento_lista_recursos,
            LARGURA_PAINEL_ESQUERDO - 20,
            62,
        )
        for indice, tipo in enumerate(tipos_disponiveis)
    }


carregar_areas()
carregar_objetos_mapa()
executando = True

while executando:
    relogio.tick(60)

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            executando = False

        elif evento.type == pygame.VIDEORESIZE:
            ajustar_camera_janela()

        elif evento.type == pygame.MOUSEWHEEL:
            pos = getattr(evento, "pos", pygame.mouse.get_pos())

            if (
                pos[0] < LARGURA_PAINEL_ESQUERDO
                and ALTURA_CABECALHO <= pos[1]
                < tela.get_height() - ALTURA_RODAPE
            ):
                deslocamento_lista_recursos -= evento.y * 70
                obter_cartoes_recursos()
                continue


            if not (
                LARGURA_PAINEL_ESQUERDO <= pos[0]
                < tela.get_width() - LARGURA_PAINEL_DIREITO
                and ALTURA_CABECALHO <= pos[1]
                < tela.get_height() - ALTURA_RODAPE
            ):
                continue

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

            elif evento.key == pygame.K_g:
                mostrar_grade = not mostrar_grade

            elif evento.key == pygame.K_b:
                mostrar_bordas = not mostrar_bordas

            elif evento.key == pygame.K_s and (
                pygame.key.get_mods() & pygame.KMOD_CTRL
            ):
                salvar()

            elif evento.key == pygame.K_TAB and tipos_disponiveis:
                indice = tipos_disponiveis.index(tipo_atual)
                selecionar_tipo_por_indice(
                    (indice + 1) % len(tipos_disponiveis)
                )

            elif pygame.K_1 <= evento.key <= pygame.K_9:
                selecionar_tipo_por_indice(evento.key - pygame.K_1)

            elif evento.key == pygame.K_DELETE:
                if modo_editor == "recursos" and area_selecionada is not None:
                    remover_area(area_selecionada)
                elif modo_editor == "construcoes" and objeto_selecionado is not None:
                    remover_objeto(objeto_selecionado)

            elif modo_editor == "recursos" and evento.key == pygame.K_UP:
                alterar_configuracao("maximo", 1)

            elif modo_editor == "recursos" and evento.key == pygame.K_DOWN:
                alterar_configuracao("maximo", -1)

            elif modo_editor == "recursos" and evento.key == pygame.K_RIGHT:
                alterar_configuracao("respawn", 1)

            elif modo_editor == "recursos" and evento.key == pygame.K_LEFT:
                alterar_configuracao("respawn", -1)

            elif modo_editor == "recursos" and evento.key == pygame.K_PAGEUP:
                alterar_configuracao("inicial", 1)

            elif modo_editor == "recursos" and evento.key == pygame.K_PAGEDOWN:
                alterar_configuracao("inicial", -1)

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:
                botao_voltar = pygame.Rect(
                    tela.get_width() - 190, 12, 170, 42
                )
                if botao_voltar.collidepoint(evento.pos):
                    executando = False
                    continue

                botao_recursos = pygame.Rect(390, 12, 125, 42)
                botao_construcoes = pygame.Rect(522, 12, 145, 42)

                if botao_recursos.collidepoint(evento.pos):
                    alternar_modo_editor("recursos")
                    continue

                if botao_construcoes.collidepoint(evento.pos):
                    alternar_modo_editor("construcoes")
                    continue

                if evento.pos[0] < LARGURA_PAINEL_ESQUERDO:
                    cartoes = obter_cartoes_recursos()

                    for indice, tipo in enumerate(tipos_disponiveis):
                        if cartoes[tipo].collidepoint(evento.pos):
                            selecionar_tipo_por_indice(indice)
                            break

                    continue

            if evento.button == 2:
                movendo_camera = True
                ultima_posicao_mouse = evento.pos
            
            elif evento.button == 1:
                x_painel_direito = (
                    tela.get_width() - LARGURA_PAINEL_DIREITO
                )

                if evento.pos[0] >= x_painel_direito:
                    if area_selecionada is not None:
                        botoes = obter_botoes_propriedades(
                            tela.get_width(), ALTURA_CABECALHO
                        )

                        for campo, controles in botoes.items():
                            if controles["menos"].collidepoint(evento.pos):
                                alterar_configuracao(campo, -1)
                                break

                            if controles["mais"].collidepoint(evento.pos):
                                alterar_configuracao(campo, 1)
                                break

                    continue

                if modo_editor == "construcoes":
                    indice = selecionar_objeto(evento.pos)

                    if indice is not None:
                        objeto_selecionado = indice
                    else:
                        posicionar_construcao(evento.pos)
                        objeto_selecionado = (
                            len(objetos_mapa) - 1 if objetos_mapa else None
                        )

                else:
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
                if modo_editor == "construcoes":
                    indice = selecionar_objeto(evento.pos)
                    if indice is not None:
                        remover_objeto(indice)
                else:
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
            
            elif (
                evento.button == 1
                and modo_editor == "recursos"
                and arrastando
            ):
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

    # Grade alinhada aos tiles do mapa.
    if mostrar_grade:
        area_mapa = pygame.Rect(
            round(camera_x),
            round(camera_y),
            largura,
            altura
        )

        area_util = pygame.Rect(
            LARGURA_PAINEL_ESQUERDO,
            ALTURA_CABECALHO,
            max(
                0,
                tela.get_width()
                - LARGURA_PAINEL_ESQUERDO
                - LARGURA_PAINEL_DIREITO
            ),
            max(
                0,
                tela.get_height()
                - ALTURA_CABECALHO
                - ALTURA_RODAPE
            ),
        )

        tela.set_clip(area_mapa.clip(area_util))

        for x in range(0, IMG_LARGURA + 1, TAMANHO_TILE):
            px = round(camera_x + x * escala)
            pygame.draw.line(
                tela, (0, 0, 0),
                (px, area_mapa.top),
                (px, area_mapa.bottom), 1
            )

        for y in range(0, IMG_ALTURA + 1, TAMANHO_TILE):
            py = round(camera_y + y * escala)
            pygame.draw.line(
                tela, (0, 0, 0),
                (area_mapa.left, py),
                (area_mapa.right, py), 1
            )

        tela.set_clip(None)

    # Construções posicionadas no mapa.
    if modo_editor == "construcoes":
        for indice, registro in enumerate(objetos_mapa):
            config_objeto = CONSTRUCOES[registro["id"]]
            rect_mapa = obter_rect_objeto(registro)
            visual_objeto = area_para_tela(rect_mapa)
            imagem_objeto = obter_imagem(
                config_objeto["imagem"],
                (config_objeto["largura_visual"], config_objeto["altura_visual"]),
            )

            if imagem_objeto is not None:
                imagem_renderizada = (
                    imagem_objeto
                    if imagem_objeto.get_size() == visual_objeto.size
                    else pygame.transform.smoothscale(
                        imagem_objeto, visual_objeto.size
                    )
                )
                tela.blit(imagem_renderizada, visual_objeto.topleft)
            else:
                pygame.draw.rect(tela, config_objeto["cor"], visual_objeto)

            if indice == objeto_selecionado:
                pygame.draw.rect(tela, COR_SELECAO, visual_objeto, 2)

        ponto_mouse = mouse_para_imagem(pygame.mouse.get_pos())
        if ponto_mouse is not None and tipo_atual in CONSTRUCOES:
            config_previa = CONSTRUCOES[tipo_atual]
            largura_previa = config_previa["largura_visual"]
            altura_previa = config_previa["altura_visual"]

            rect_previa = pygame.Rect(
                ponto_mouse[0] - largura_previa // 2,
                ponto_mouse[1] - altura_previa // 2,
                largura_previa,
                altura_previa,
            )
            rect_previa.clamp_ip(pygame.Rect(0, 0, IMG_LARGURA, IMG_ALTURA))
            visual_previa = area_para_tela(rect_previa)

            imagem_previa_construcao = obter_imagem(
                config_previa["imagem"],
                (largura_previa, altura_previa),
            )

            if imagem_previa_construcao is not None:
                imagem_previa_construcao = imagem_previa_construcao.copy()
                if imagem_previa_construcao.get_size() != visual_previa.size:
                    imagem_previa_construcao = pygame.transform.smoothscale(
                        imagem_previa_construcao, visual_previa.size
                    )
                imagem_previa_construcao.set_alpha(150)
                tela.blit(imagem_previa_construcao, visual_previa.topleft)

            pygame.draw.rect(tela, COR_DESTAQUE, visual_previa, 2)

    # Áreas de recursos
    if modo_editor == "recursos":
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


    # Painel lateral de seleção de recursos.
    painel_esquerdo = pygame.Rect(
        0,
        ALTURA_CABECALHO,
        LARGURA_PAINEL_ESQUERDO,
        max(0, altura_tela - ALTURA_CABECALHO - ALTURA_RODAPE),
    )

    pygame.draw.rect(tela, COR_PAINEL, painel_esquerdo)
    pygame.draw.line(
        tela,
        COR_PAINEL_CLARO,
        (LARGURA_PAINEL_ESQUERDO - 1, painel_esquerdo.top),
        (LARGURA_PAINEL_ESQUERDO - 1, painel_esquerdo.bottom),
        1,
    )

    desenhar_texto(
        "RECURSOS" if modo_editor == "recursos" else "CONSTRUÇÕES",
        12, ALTURA_CABECALHO + 10,
        COR_DESTAQUE, pequena=True
    )

    cartoes = obter_cartoes_recursos()

    area_lista = pygame.Rect(
        5,
        ALTURA_CABECALHO + 36,
        LARGURA_PAINEL_ESQUERDO - 10,
        max(0, altura_tela - ALTURA_CABECALHO - ALTURA_RODAPE - 36),
    )

    tela.set_clip(area_lista)

    for tipo, cartao in cartoes.items():
        if not cartao.colliderect(area_lista):
            continue

        selecionado = tipo == tipo_atual
        cor_borda = COR_DESTAQUE if selecionado else COR_PAINEL_CLARO

        pygame.draw.rect(
            tela,
            COR_PAINEL_CLARO if selecionado else COR_FUNDO,
            cartao,
            border_radius=6,
        )

        pygame.draw.rect(
            tela,
            cor_borda,
            cartao,
            width=2 if selecionado else 1,
            border_radius=6,
        )

        recurso = obter_configuracao_atual()
        recurso = (
            RECURSOS[tipo] if modo_editor == "recursos"
            else CONSTRUCOES[tipo]
        )
        imagem_cartao = obter_imagem(recurso["imagem"], (38, 38))
        centro_imagem = (cartao.x + 29, cartao.centery)

        if imagem_cartao is not None:
            tela.blit(
                imagem_cartao,
                imagem_cartao.get_rect(center=centro_imagem),
            )
        else:
            miniatura = pygame.Rect(0, 0, 28, 28)
            miniatura.center = centro_imagem
            pygame.draw.rect(
                tela, recurso["cor"], miniatura, border_radius=4
            )

        nome = fonte_pequena.render(
            recurso["nome"], True, COR_TEXTO
        )

        tela.blit(
            nome,
            nome.get_rect(midleft=(cartao.x + 54, cartao.centery)),
        )

    tela.set_clip(None)

    # Cabeçalho compacto.
    pygame.draw.rect(
        tela,
        COR_PAINEL,
        (0, 0, largura_tela, ALTURA_CABECALHO),
    )

    pygame.draw.line(
        tela,
        COR_PAINEL_CLARO,
        (0, ALTURA_CABECALHO - 1),
        (largura_tela, ALTURA_CABECALHO - 1),
        1,
    )

    desenhar_texto(
        "EDITOR DE RECURSOS E CONSTRUÇÕES",
        20, 22, COR_DESTAQUE
    )

    recurso_atual = obter_configuracao_atual()
    quadro_previa = pygame.Rect(190, 8, 48, 48)

    pygame.draw.rect(
        tela, COR_PAINEL_CLARO, quadro_previa, border_radius=6
    )

    imagem_previa = obter_imagem(
        recurso_atual["imagem"],
        (42, 42),
    )

    if imagem_previa is not None:
        tela.blit(
            imagem_previa,
            imagem_previa.get_rect(center=quadro_previa.center),
        )
    else:
        miniatura = pygame.Rect(0, 0, 28, 28)
        miniatura.center = quadro_previa.center
        pygame.draw.rect(
            tela, recurso_atual["cor"], miniatura, border_radius=4
        )

    desenhar_texto(
        f"{'Recurso' if modo_editor == 'recursos' else 'Construção'} atual: {recurso_atual['nome']}",
        252, 22, COR_TEXTO
    )

    # Alternância entre edição de áreas e posicionamento de construções.
    botao_recursos = pygame.Rect(390, 12, 125, 42)
    botao_construcoes = pygame.Rect(522, 12, 145, 42)

    for botao, rotulo, ativo in (
        (botao_recursos, "RECURSOS", modo_editor == "recursos"),
        (botao_construcoes, "CONSTRUÇÕES", modo_editor == "construcoes"),
    ):
        pygame.draw.rect(
            tela,
            COR_DESTAQUE if ativo else COR_PAINEL_CLARO,
            botao,
            border_radius=7,
        )
        pygame.draw.rect(
            tela, COR_DESTAQUE, botao, 1, border_radius=7
        )
        texto_modo = fonte_pequena.render(rotulo, True, COR_TEXTO)
        tela.blit(texto_modo, texto_modo.get_rect(center=botao.center))

    # Botão voltar à Central.
    botao_voltar = pygame.Rect(
        largura_tela - 190, 12, 170, 42
    )

    pygame.draw.rect(
        tela, COR_PAINEL_CLARO, botao_voltar, border_radius=7
    )
    pygame.draw.rect(
        tela, COR_DESTAQUE, botao_voltar,
        width=1, border_radius=7
    )

    texto_voltar = fonte_pequena.render(
        "< VOLTAR À CENTRAL", True, COR_TEXTO
    )
    tela.blit(
        texto_voltar,
        texto_voltar.get_rect(center=botao_voltar.center)
    )

    # Painel lateral direito: propriedades ou informações da seleção.
    x_painel = largura_tela - LARGURA_PAINEL_DIREITO

    painel_direito = pygame.Rect(
        x_painel,
        ALTURA_CABECALHO,
        LARGURA_PAINEL_DIREITO,
        max(0, altura_tela - ALTURA_CABECALHO - ALTURA_RODAPE),
    )

    pygame.draw.rect(tela, COR_PAINEL, painel_direito)

    pygame.draw.line(
        tela,
        COR_PAINEL_CLARO,
        (x_painel, painel_direito.top),
        (x_painel, painel_direito.bottom),
        1,
    )

    desenhar_texto(
        "PROPRIEDADES",
        x_painel + 14,
        ALTURA_CABECALHO + 16,
        COR_DESTAQUE,
        pequena=True,
    )

    if modo_editor == "construcoes" and objeto_selecionado is not None:
        registro = objetos_mapa[objeto_selecionado]
        config = CONSTRUCOES[registro["id"]]

        desenhar_texto(
            config["nome"],
            x_painel + 14,
            ALTURA_CABECALHO + 48,
            COR_TEXTO,
            pequena=True,
        )
        desenhar_texto(
            f"Posição: {registro['x']}, {registro['y']}",
            x_painel + 14,
            ALTURA_CABECALHO + 78,
            COR_SECUNDARIA,
            pequena=True,
        )
        desenhar_texto(
            f"Tamanho: {config['largura_visual']} x {config['altura_visual']}",
            x_painel + 14,
            ALTURA_CABECALHO + 102,
            COR_SECUNDARIA,
            pequena=True,
        )
        desenhar_texto(
            "Clique no mapa para adicionar.",
            x_painel + 14,
            ALTURA_CABECALHO + 145,
            COR_SECUNDARIA,
            pequena=True,
        )
        desenhar_texto(
            "Clique com botão direito ou",
            x_painel + 14,
            ALTURA_CABECALHO + 170,
            COR_SECUNDARIA,
            pequena=True,
        )
        desenhar_texto(
            "DELETE para remover.",
            x_painel + 14,
            ALTURA_CABECALHO + 190,
            COR_SECUNDARIA,
            pequena=True,
        )

    elif modo_editor == "recursos" and area_selecionada is not None:
        item = areas[area_selecionada]

        nome = RECURSOS[item["tipo"]]["nome"]
        desenhar_texto(
            nome,
            x_painel + 14,
            ALTURA_CABECALHO + 42,
            COR_TEXTO,
            pequena=True,
        )

        propriedades = [
            ("maximo", "Quantidade máxima", str(item["maximo"])),
            ("inicial", "Quantidade inicial", str(item["inicial"])),
            ("respawn", "Tempo de respawn", f"{item['respawn']:.0f} s"),
        ]

        botoes = obter_botoes_propriedades(
            largura_tela, ALTURA_CABECALHO
        )

        for campo, rotulo, valor in propriedades:
            controles = botoes[campo]

            desenhar_texto(
                rotulo,
                x_painel + 14,
                controles["menos"].top - 23,
                COR_SECUNDARIA,
                pequena=True,
            )

            for acao in ("menos", "mais"):
                botao = controles[acao]

                pygame.draw.rect(
                    tela,
                    COR_PAINEL_CLARO,
                    botao,
                    border_radius=5,
                )
                pygame.draw.rect(
                    tela,
                    COR_DESTAQUE,
                    botao,
                    width=1,
                    border_radius=5,
                )

                simbolo = "-" if acao == "menos" else "+"
                superficie = fonte.render(
                    simbolo, True, COR_TEXTO
                )
                tela.blit(
                    superficie,
                    superficie.get_rect(center=botao.center),
                )

            superficie_valor = fonte_pequena.render(
                valor, True, COR_TEXTO
            )
            tela.blit(
                superficie_valor,
                superficie_valor.get_rect(
                    center=controles["centro"]
                ),
            )

        desenhar_texto(
            "Alterações salvas automaticamente.",
            x_painel + 12,
            altura_tela - ALTURA_RODAPE - 28,
            COR_SECUNDARIA,
            pequena=True,
        )

    elif modo_editor == "recursos":
        desenhar_texto(
            "Selecione uma área",
            x_painel + 14,
            ALTURA_CABECALHO + 55,
            COR_SECUNDARIA,
            pequena=True,
        )
        desenhar_texto(
            "no mapa para editar",
            x_painel + 14,
            ALTURA_CABECALHO + 75,
            COR_SECUNDARIA,
            pequena=True,
        )

    else:
        desenhar_texto(
            "Selecione uma construção",
            x_painel + 14,
            ALTURA_CABECALHO + 55,
            COR_SECUNDARIA,
            pequena=True,
        )
        desenhar_texto(
            "ou clique no mapa para",
            x_painel + 14,
            ALTURA_CABECALHO + 75,
            COR_SECUNDARIA,
            pequena=True,
        )
        desenhar_texto(
            "posicionar a atual.",
            x_painel + 14,
            ALTURA_CABECALHO + 95,
            COR_SECUNDARIA,
            pequena=True,
        )

    if pygame.time.get_ticks() < tempo_mensagem:
        superficie_mensagem = fonte_pequena.render(
            mensagem, True, COR_DESTAQUE
        )
        x_mensagem = (
            LARGURA_PAINEL_ESQUERDO
            + (
                largura_tela
                - LARGURA_PAINEL_ESQUERDO
                - LARGURA_PAINEL_DIREITO
                - superficie_mensagem.get_width()
            ) // 2
        )

        y_mensagem = (
            altura_tela
            - ALTURA_RODAPE
            - superficie_mensagem.get_height()
            - 8
        )

        tela.blit(
            superficie_mensagem,
            (x_mensagem, y_mensagem)
        )

    pygame.display.flip()

pygame.quit()


