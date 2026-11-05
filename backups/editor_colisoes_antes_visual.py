import json
from pathlib import Path
import pygame

pygame.init()

# ==========================================================
# CAMINHOS
# ==========================================================

RAIZ = Path(__file__).resolve().parents[2]

CAMINHO_MAPA = RAIZ / "dados" / "mapas" / "mapa_principal.json"
CAMINHO_COLISOES = RAIZ / "mapa" / "colisoes.json"
CAMINHO_COLISOES_SPRITES = RAIZ / "mapa" / "colisoes_sprites.json"

PASTA_SUPERIOR = RAIZ / "assets" / "tiles" / "superior"
PASTA_TERRENO = RAIZ / "assets" / "tiles" / "terreno"

if not CAMINHO_MAPA.is_file():
    raise FileNotFoundError(CAMINHO_MAPA)

with open(CAMINHO_MAPA, "r", encoding="utf-8") as arquivo:
    dados_mapa = json.load(arquivo)

CAMADAS = dados_mapa["camadas"]
TILES = dados_mapa.get("tiles", {})

LARGURA_MAPA = dados_mapa["largura"]
ALTURA_MAPA = dados_mapa["altura"]
TILE_SIZE = dados_mapa["tile_size"]

IMG_LARGURA = LARGURA_MAPA * TILE_SIZE
IMG_ALTURA = ALTURA_MAPA * TILE_SIZE

# ==========================================================
# PYGAME
# ==========================================================

tela = pygame.display.set_mode((1100, 650), pygame.RESIZABLE)
pygame.display.set_caption("SimpSmith - Editor de Colisoes")

relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("arial", 16)
fonte_pequena = pygame.font.SysFont("arial", 13)

FUNDO = (35, 35, 35)
COR_TEXTO = (255, 255, 255)
COR_OBSTACULO = (255, 50, 50)
COR_INTERACAO = (30, 150, 255)
COR_SPRITE = (255, 190, 30)
COR_SELECAO = (255, 255, 255)

mostrar_bordas = True
mostrar_grade = False

# 1 = mapa | 2 = interacao | 3 = sprite
modo = "mapa"

zoom = 1.0
zoom_minimo = 0.25
zoom_maximo = 5.0

pan_x = 0.0
pan_y = 0.0

arrastando_camera = False
ultima_posicao_camera = None

arrastando = False
inicio = None
fim = None

obstaculos = []
areas_interacao = []
colisoes_sprites = {}

sprite_selecionado = None
instancia_selecionada = None

# ==========================================================
# CARREGAR SPRITES
# ==========================================================

def carregar_sprites(pasta):
    sprites = {}

    if not pasta.exists():
        print(f"Pasta nao encontrada: {pasta}")
        return sprites

    for caminho in pasta.rglob("*.png"):
        identificador = caminho.relative_to(pasta).with_suffix("").as_posix()

        try:
            imagem = pygame.image.load(str(caminho)).convert_alpha()
            sprites[identificador] = imagem
        except pygame.error as erro:
            print(f"Erro ao carregar {caminho}: {erro}")

    return sprites


sprites_superiores = carregar_sprites(PASTA_SUPERIOR)
sprites_terreno = carregar_sprites(PASTA_TERRENO)

print(f"Mapa carregado: {CAMINHO_MAPA.name}")
print(f"Sprites superiores: {len(sprites_superiores)}")
print(f"Sprites de terreno: {len(sprites_terreno)}")

# ==========================================================
# CARREGAR COLISOES
# ==========================================================

if CAMINHO_COLISOES.exists():
    with open(CAMINHO_COLISOES, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    obstaculos = [
        pygame.Rect(
            item["x"],
            item["y"],
            item["largura"],
            item["altura"]
        )
        for item in dados.get("obstaculos", [])
    ]

    areas_interacao = dados.get(
        "areas_interacao",
        dados_mapa.get("areas_interacao", [])
    )
else:
    areas_interacao = dados_mapa.get("areas_interacao", [])


if CAMINHO_COLISOES_SPRITES.exists():
    with open(CAMINHO_COLISOES_SPRITES, "r", encoding="utf-8") as arquivo:
        dados_sprites = json.load(arquivo)

    colisoes_sprites = dados_sprites.get("sprites", {})


# ==========================================================
# TERRENO
# ==========================================================

def criar_superficie_mapa():
    superficie = pygame.Surface(
        (IMG_LARGURA, IMG_ALTURA)
    )

    superficie.fill((45, 45, 45))

    for nome_camada in ("terreno", "objetos"):
        matriz = CAMADAS.get(nome_camada, [])

        for y, linha in enumerate(matriz):
            for x, nome_tile in enumerate(linha):

                if nome_tile is None:
                    continue

                sprite = sprites_terreno.get(str(nome_tile))

                if sprite is not None:
                    imagem = pygame.transform.scale(
                        sprite,
                        (TILE_SIZE, TILE_SIZE)
                    )

                    superficie.blit(
                        imagem,
                        (x * TILE_SIZE, y * TILE_SIZE)
                    )
                    continue

                # Fallback: usa a cor cadastrada no JSON.
                definicao = TILES.get(nome_tile)

                if definicao and "cor" in definicao:
                    cor = tuple(definicao["cor"])
                else:
                    cor = (65, 65, 65)

                pygame.draw.rect(
                    superficie,
                    cor,
                    (
                        x * TILE_SIZE,
                        y * TILE_SIZE,
                        TILE_SIZE,
                        TILE_SIZE
                    )
                )

    return superficie


imagem_original = criar_superficie_mapa()

# ==========================================================
# INSTANCIAS DE SPRITES
# ==========================================================

def obter_instancias_sprites():
    return dados_mapa.get("sprites_superiores", [])


def obter_rect_sprite(sprite, escala=1.0):
    imagem = sprites_superiores.get(sprite.get("id"))

    if imagem is None:
        return None

    return pygame.Rect(
        sprite["x"],
        sprite["y"],
        imagem.get_width(),
        imagem.get_height()
    )


def encontrar_sprite(posicao):
    px, py = posicao

    # Percorre de trás para frente para selecionar o sprite
    # visualmente mais próximo do topo da pilha.
    for sprite in reversed(obter_instancias_sprites()):
        rect = obter_rect_sprite(sprite)

        if rect and rect.collidepoint(px, py):
            return sprite

    return None


# ==========================================================
# SALVAR
# ==========================================================

def salvar_mapa():
    CAMINHO_COLISOES.parent.mkdir(parents=True, exist_ok=True)

    dados = {
        "largura_imagem": IMG_LARGURA,
        "altura_imagem": IMG_ALTURA,
        "tile_size": TILE_SIZE,
        "mapa": dados_mapa.get("nome", "mapa_principal"),
        "obstaculos": [
            {
                "x": r.x,
                "y": r.y,
                "largura": r.width,
                "altura": r.height
            }
            for r in obstaculos
        ],
        "areas_interacao": areas_interacao
    }

    with open(CAMINHO_COLISOES, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)

    print("Colisoes do mapa salvas!")


def salvar_sprites():
    CAMINHO_COLISOES_SPRITES.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    dados = {
        "mapa": dados_mapa.get("nome", "mapa_principal"),
        "sprites": colisoes_sprites
    }

    with open(
        CAMINHO_COLISOES_SPRITES,
        "w",
        encoding="utf-8"
    ) as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)

    print("Colisoes dos sprites salvas!")


# ==========================================================
# CAMERA
# ==========================================================

def area_imagem():
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


def mouse_para_imagem(pos):
    area, escala = area_imagem()

    if not area.collidepoint(pos):
        return None

    x = int((pos[0] - area.x) / escala)
    y = int((pos[1] - area.y) / escala)

    x = max(0, min(IMG_LARGURA - 1, x))
    y = max(0, min(IMG_ALTURA - 1, y))

    return x, y


def retangulo_arrastado(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    return pygame.Rect(
        min(x1, x2),
        min(y1, y2),
        abs(x2 - x1),
        abs(y2 - y1)
    )


# ==========================================================
# COLISOES DOS SPRITES
# ==========================================================

def chave_sprite(sprite):
    return sprite.get("id")


def obter_colisoes_sprite(identificador):
    return colisoes_sprites.setdefault(identificador, [])


def apagar_colisao_sprite(posicao):
    ponto = mouse_para_imagem(posicao)

    if ponto is None:
        return

    instancia = encontrar_sprite(ponto)

    if instancia is None:
        return

    identificador = chave_sprite(instancia)
    lista = obter_colisoes_sprite(identificador)

    local_x = ponto[0] - instancia["x"]
    local_y = ponto[1] - instancia["y"]

    for i in range(len(lista) - 1, -1, -1):
        item = lista[i]

        rect = pygame.Rect(
            item["x"],
            item["y"],
            item["largura"],
            item["altura"]
        )

        if rect.collidepoint(local_x, local_y):
            del lista[i]
            salvar_sprites()
            return


def desenhar_colisoes_sprites(area, escala):
    for instancia in obter_instancias_sprites():

        identificador = chave_sprite(instancia)
        lista = colisoes_sprites.get(identificador, [])

        for item in lista:
            visual = pygame.Rect(
                area.x + round((instancia["x"] + item["x"]) * escala),
                area.y + round((instancia["y"] + item["y"]) * escala),
                max(1, round(item["largura"] * escala)),
                max(1, round(item["altura"] * escala))
            )

            pygame.draw.rect(
                tela,
                COR_SPRITE,
                visual,
                2
            )

        if identificador == sprite_selecionado:
            imagem = sprites_superiores.get(identificador)

            if imagem:
                visual = pygame.Rect(
                    area.x + round(instancia["x"] * escala),
                    area.y + round(instancia["y"] * escala),
                    max(1, round(imagem.get_width() * escala)),
                    max(1, round(imagem.get_height() * escala))
                )

                pygame.draw.rect(
                    tela,
                    COR_SELECAO,
                    visual,
                    1
                )


# ==========================================================
# DESENHAR SPRITES
# ==========================================================

def desenhar_sprites_superiores(area, escala):
    for instancia in obter_instancias_sprites():

        identificador = instancia.get("id")
        imagem = sprites_superiores.get(identificador)

        if imagem is None:
            continue

        largura = max(1, round(imagem.get_width() * escala))
        altura = max(1, round(imagem.get_height() * escala))

        redimensionada = pygame.transform.scale(
            imagem,
            (largura, altura)
        )

        x = area.x + round(instancia["x"] * escala)
        y = area.y + round(instancia["y"] * escala)

        tela.blit(redimensionada, (x, y))


# ==========================================================
# EXCLUIR
# ==========================================================

def apagar_proximo(posicao):
    ponto = mouse_para_imagem(posicao)

    if ponto is None:
        return

    px, py = ponto

    if modo == "mapa":

        for i in range(len(obstaculos) - 1, -1, -1):
            if obstaculos[i].collidepoint(px, py):
                del obstaculos[i]
                salvar_mapa()
                return

    elif modo == "interacao":

        for i in range(len(areas_interacao) - 1, -1, -1):
            item = areas_interacao[i]

            rect = pygame.Rect(
                item["x"],
                item["y"],
                item["largura"],
                item["altura"]
            )

            if rect.collidepoint(px, py):
                del areas_interacao[i]
                salvar_mapa()
                return

    elif modo == "sprite":
        apagar_colisao_sprite(posicao)


# ==========================================================
# LOOP PRINCIPAL
# ==========================================================

executando = True

while executando:
    relogio.tick(60)

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            executando = False

        elif evento.type == pygame.KEYDOWN:

            if evento.key == pygame.K_ESCAPE:
                executando = False

            elif evento.key == pygame.K_1:
                modo = "mapa"
                sprite_selecionado = None
                instancia_selecionada = None

            elif evento.key == pygame.K_2:
                modo = "interacao"
                sprite_selecionado = None
                instancia_selecionada = None

            elif evento.key == pygame.K_3:
                modo = "sprite"
                sprite_selecionado = None
                instancia_selecionada = None

            elif evento.key == pygame.K_b:
                mostrar_bordas = not mostrar_bordas

            elif evento.key == pygame.K_g:
                mostrar_grade = not mostrar_grade

            elif evento.key == pygame.K_s and (
                pygame.key.get_mods() & pygame.KMOD_CTRL
            ):
                salvar_mapa()
                salvar_sprites()

        elif evento.type == pygame.MOUSEWHEEL:

            mouse = pygame.mouse.get_pos()
            area, escala_atual = area_imagem()

            if area.collidepoint(mouse):

                escala_base = min(
                    tela.get_width() / IMG_LARGURA,
                    tela.get_height() / IMG_ALTURA
                )

                novo_zoom = max(
                    zoom_minimo,
                    min(zoom_maximo, zoom * (1.15 ** evento.y))
                )

                if novo_zoom != zoom:

                    mundo_x = (mouse[0] - area.x) / escala_atual
                    mundo_y = (mouse[1] - area.y) / escala_atual

                    zoom = novo_zoom
                    nova_escala = escala_base * zoom

                    pan_x = (
                        mouse[0] - mundo_x * nova_escala
                        - (tela.get_width() - IMG_LARGURA * nova_escala) / 2
                    )

                    pan_y = (
                        mouse[1] - mundo_y * nova_escala
                        - (tela.get_height() - IMG_ALTURA * nova_escala) / 2
                    )

        elif evento.type == pygame.MOUSEBUTTONDOWN:

            if evento.button == 2:
                arrastando_camera = True
                ultima_posicao_camera = evento.pos

            elif evento.button == 1:

                ponto = mouse_para_imagem(evento.pos)

                if ponto is None:
                    continue

                if modo == "sprite":

                    instancia = encontrar_sprite(ponto)

                    if instancia is None:
                        sprite_selecionado = None
                        instancia_selecionada = None
                        continue

                    identificador = chave_sprite(instancia)

                    # Primeiro clique seleciona o tipo de sprite.
                    # Depois, arrastar sobre ele cria a colisao.
                    if sprite_selecionado != identificador:
                        sprite_selecionado = identificador
                        instancia_selecionada = instancia
                        continue

                    instancia_selecionada = instancia

                    inicio = (
                        ponto[0] - instancia["x"],
                        ponto[1] - instancia["y"]
                    )

                    fim = inicio
                    arrastando = True

                else:
                    inicio = ponto
                    fim = ponto
                    arrastando = True

            elif evento.button == 3:
                apagar_proximo(evento.pos)

        elif evento.type == pygame.MOUSEMOTION:

            if arrastando_camera:

                dx = evento.pos[0] - ultima_posicao_camera[0]
                dy = evento.pos[1] - ultima_posicao_camera[1]

                pan_x += dx
                pan_y += dy

                ultima_posicao_camera = evento.pos

            elif arrastando:

                ponto = mouse_para_imagem(evento.pos)

                if ponto is not None:

                    if modo == "sprite" and instancia_selecionada:
                        fim = (
                            ponto[0] - instancia_selecionada["x"],
                            ponto[1] - instancia_selecionada["y"]
                        )
                    else:
                        fim = ponto

        elif evento.type == pygame.MOUSEBUTTONUP:

            if evento.button == 2:
                arrastando_camera = False
                ultima_posicao_camera = None

            elif evento.button == 1 and arrastando:

                ponto = mouse_para_imagem(evento.pos)

                if ponto is not None:

                    if modo == "sprite" and instancia_selecionada:
                        fim = (
                            ponto[0] - instancia_selecionada["x"],
                            ponto[1] - instancia_selecionada["y"]
                        )
                    else:
                        fim = ponto

                if inicio is not None and fim is not None:

                    novo = retangulo_arrastado(inicio, fim)

                    if novo.width >= 3 and novo.height >= 3:

                        if modo == "mapa":
                            obstaculos.append(novo)
                            salvar_mapa()

                        elif modo == "interacao":

                            numero = len(areas_interacao) + 1

                            areas_interacao.append({
                                "id": f"area_{numero}",
                                "x": novo.x,
                                "y": novo.y,
                                "largura": novo.width,
                                "altura": novo.height,
                                "tipo": "fornalha"
                            })

                            salvar_mapa()

                        elif modo == "sprite" and sprite_selecionado:

                            lista = obter_colisoes_sprite(
                                sprite_selecionado
                            )

                            lista.append({
                                "x": novo.x,
                                "y": novo.y,
                                "largura": novo.width,
                                "altura": novo.height
                            })

                            salvar_sprites()

                arrastando = False
                inicio = None
                fim = None

    # ======================================================
    # RENDERIZACAO
    # ======================================================

    tela.fill(FUNDO)

    area, escala = area_imagem()

    imagem = pygame.transform.scale(
        imagem_original,
        (area.width, area.height)
    )

    tela.blit(imagem, area.topleft)

    # Sprites do mapa
    desenhar_sprites_superiores(area, escala)

    # Grade
    if mostrar_grade:

        for x in range(LARGURA_MAPA + 1):
            px = area.x + round(x * TILE_SIZE * escala)

            pygame.draw.line(
                tela, (0, 0, 0),
                (px, area.y), (px, area.bottom), 1
            )

        for y in range(ALTURA_MAPA + 1):
            py = area.y + round(y * TILE_SIZE * escala)

            pygame.draw.line(
                tela, (0, 0, 0),
                (area.x, py), (area.right, py), 1
            )

    # Colisoes do mapa
    if mostrar_bordas:

        for obstaculo in obstaculos:

            visual = pygame.Rect(
                area.x + round(obstaculo.x * escala),
                area.y + round(obstaculo.y * escala),
                max(1, round(obstaculo.width * escala)),
                max(1, round(obstaculo.height * escala))
            )

            pygame.draw.rect(tela, COR_OBSTACULO, visual, 2)

        for item in areas_interacao:

            visual = pygame.Rect(
                area.x + round(item["x"] * escala),
                area.y + round(item["y"] * escala),
                max(1, round(item["largura"] * escala)),
                max(1, round(item["altura"] * escala))
            )

            pygame.draw.rect(tela, COR_INTERACAO, visual, 2)

            texto_area = fonte_pequena.render(
                item["id"], True, COR_TEXTO
            )

            tela.blit(texto_area, (visual.x + 2, visual.y + 2))

        # Colisoes reutilizaveis dos sprites
        desenhar_colisoes_sprites(area, escala)

    # Retangulo em criacao
    if arrastando and inicio is not None and fim is not None:

        r = retangulo_arrastado(inicio, fim)

        if modo == "sprite" and instancia_selecionada:

            origem_x = instancia_selecionada["x"]
            origem_y = instancia_selecionada["y"]

            r.x += origem_x
            r.y += origem_y

        visual = pygame.Rect(
            area.x + round(r.x * escala),
            area.y + round(r.y * escala),
            max(1, round(r.width * escala)),
            max(1, round(r.height * escala))
        )

        cor = {
            "mapa": COR_OBSTACULO,
            "interacao": COR_INTERACAO,
            "sprite": COR_SPRITE
        }[modo]

        pygame.draw.rect(tela, cor, visual, 2)

    # ======================================================
    # BARRA SUPERIOR
    # ======================================================

    pygame.draw.rect(
        tela,
        (22, 22, 22),
        (0, 0, tela.get_width(), 55)
    )

    nome_modo = {
        "mapa": "COLISAO DO MAPA",
        "interacao": "AREAS DE INTERACAO",
        "sprite": "COLISAO DOS SPRITES"
    }[modo]

    linha1 = (
        f"1: Mapa | 2: Interacao | 3: Sprite | "
        f"Modo: {nome_modo}"
    )

    linha2 = (
        "Esquerdo: criar/selecionar | Direito: apagar | "
        "Scroll: zoom | Meio: mover | B: bordas | "
        "G: grade | Ctrl+S: salvar | ESC: sair"
    )

    tela.blit(
        fonte.render(linha1, True, COR_TEXTO),
        (8, 5)
    )

    tela.blit(
        fonte_pequena.render(linha2, True, (200, 200, 200)),
        (8, 30)
    )

    if modo == "sprite":

        nome = sprite_selecionado or "Nenhum sprite selecionado"

        texto_sprite = fonte_pequena.render(
            f"Sprite selecionado: {nome}",
            True,
            COR_SPRITE
        )

        tela.blit(
            texto_sprite,
            (tela.get_width() - texto_sprite.get_width() - 10, 8)
        )

    pygame.display.flip()

pygame.quit()

