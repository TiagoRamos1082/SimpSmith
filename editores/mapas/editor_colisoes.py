import json
import ctypes
import sys
from pathlib import Path
import pygame

RAIZ = Path(__file__).resolve().parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from sistemas.catalogo_itens import CatalogoItens
from sistemas.carregador_imagens import obter_imagem

pygame.init()

# ==========================================================
# CAMINHOS
# ==========================================================

RAIZ = Path(__file__).resolve().parents[2]

CAMINHO_MAPA = RAIZ / "dados" / "mapas" / "mapa_principal.json"
CAMINHO_COLISOES = RAIZ / "mapa" / "colisoes.json"
CAMINHO_COLISOES_SPRITES = RAIZ / "mapa" / "colisoes_sprites.json"
CAMINHO_CONFIG_PERSONAGEM = RAIZ / "dados" / "personagens" / "jogador.json"

PASTA_SUPERIOR = RAIZ / "assets" / "tiles" / "superior"
PASTA_TERRENO = RAIZ / "assets" / "tiles" / "terreno"
CAMADAS_SPRITES = ("terreno", "superior")

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

ESCALA_SPRITES_JOGO = 2.0

# ==========================================================
# PYGAME
# ==========================================================

tela = pygame.display.set_mode((1100, 650), pygame.RESIZABLE)
pygame.display.set_caption("SimpSmith - Editor de Colisões")

# Maximiza a janela mantendo bordas e barra de tarefas.
try:
    hwnd = pygame.display.get_wm_info().get("window")
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 3)
except (AttributeError, OSError):
    pass

relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("arial", 16)
fonte_pequena = pygame.font.SysFont("arial", 13)

FUNDO = (23, 25, 31)
PAINEL = (34, 37, 45)
PAINEL_CLARO = (43, 47, 57)
COR_DESTAQUE = (217, 155, 69)
COR_TEXTO = (241, 241, 241)
COR_SECUNDARIA = (160, 165, 176)
COR_OBSTACULO = (235, 91, 91)
COR_INTERACAO = (75, 158, 230)
COR_SPRITE = (235, 180, 75)
COR_SELECAO = (245, 245, 245)
ALTURA_CABECALHO = 64
ALTURA_RODAPE = 36

LARGURA_PAINEL_ESQUERDO = 210
LARGURA_PAINEL_DIREITO = 300

mostrar_bordas = True
mostrar_grade = False

# 1 = mapa | 2 = interacao | 3 = sprite | 4 = recursos | 5 = personagem
modo = "mapa"

LARGURA_PAINEL_RECURSOS = 280
ALTURA_LINHA_RECURSO = 36

catalogo_editor = CatalogoItens()
itens_editor = catalogo_editor.listar()
item_selecionado_id = (
    itens_editor[0]["id"] if itens_editor else None
)
rolagem_itens = 0

# Ferramentas de desenho na previa dos recursos.
ferramenta_recurso = "colisao"
colisao_recurso_selecionada = None
interacao_recurso_selecionada = None
arrastando_previa_recurso = False
edicao_personagem = None
inicio_previa_recurso = None
fim_previa_recurso = None
visualizacao_recurso_ativa = False
visualizacao_personagem_ativa = False
centro_previa_recurso = None

zoom = 1.0
zoom_recurso = 1.0
zoom_minimo = 0.25
zoom_maximo = 5.0

pan_x = 0.0
pan_y = 0.0

CONFIG_PERSONAGEM_PADRAO = {
    "visual": {"largura": 32, "altura": 40},
    "colisao": {"x": 7, "y": 5, "largura": 18, "altura": 33},
}

sprite_previa_personagem = None


def limitar_colisao_personagem():
    visual = config_personagem["visual"]
    colisao = config_personagem["colisao"]

    colisao["largura"] = max(1, min(colisao["largura"], visual["largura"]))
    colisao["altura"] = max(1, min(colisao["altura"], visual["altura"]))
    colisao["x"] = max(0, min(colisao["x"], visual["largura"] - colisao["largura"]))
    colisao["y"] = max(0, min(colisao["y"], visual["altura"] - colisao["altura"]))


def carregar_config_personagem():
    configuracao = json.loads(json.dumps(CONFIG_PERSONAGEM_PADRAO))

    if CAMINHO_CONFIG_PERSONAGEM.is_file():
        try:
            with open(CAMINHO_CONFIG_PERSONAGEM, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)

            for secao in configuracao:
                valores = dados.get(secao, {})
                for propriedade in configuracao[secao]:
                    valor = int(valores.get(
                        propriedade,
                        configuracao[secao][propriedade]
                    ))
                    minimo = 1 if propriedade in ("largura", "altura") else 0
                    configuracao[secao][propriedade] = max(minimo, valor)

        except (OSError, ValueError, TypeError, json.JSONDecodeError) as erro:
            print(f"[AVISO] Configuração do personagem inválida: {erro}")

    return configuracao


config_personagem = carregar_config_personagem()
limitar_colisao_personagem()

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
camada_sprite_selecionada = None
colisao_sprite_selecionada = None

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

bibliotecas_sprites = {
    "terreno": sprites_terreno,
    "superior": sprites_superiores,
}

tamanhos_sprites = dados_mapa.setdefault("tamanhos_sprites", {})
for camada_sprite in CAMADAS_SPRITES:
    tamanhos_sprites.setdefault(camada_sprite, {})

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

def obter_instancias_sprites(camada=None):
    """Obtém as instâncias das camadas que possuem sprites editáveis."""
    sprites_por_camada = dados_mapa.get("sprites_por_camada", {})

    if camada is not None:
        if camada == "superior":
            return sprites_por_camada.get(
                "superior",
                dados_mapa.get("sprites_superiores", [])
            )
        return sprites_por_camada.get(camada, [])

    resultado = []
    for nome_camada in CAMADAS_SPRITES:
        resultado.extend(obter_instancias_sprites(nome_camada))
    return resultado


def obter_imagem_sprite(identificador, camada=None):
    if camada is None:
        camada = camada_sprite_selecionada

    return bibliotecas_sprites.get(camada, {}).get(identificador)


def obter_tamanho_sprite(identificador, camada=None):
    imagem = obter_imagem_sprite(identificador, camada)

    if imagem is None:
        return None

    configuracao = (
        tamanhos_sprites.get(camada, {}).get(identificador, {})
        if camada is not None else {}
    )

    return (
        max(1, int(configuracao.get("largura", imagem.get_width()))),
        max(1, int(configuracao.get("altura", imagem.get_height())))
    )


def obter_rect_sprite(sprite, escala=1.0, camada=None):
    if camada is None:
        camada = camada_sprite_selecionada

    identificador = sprite.get("id")
    tamanho = obter_tamanho_sprite(identificador, camada)

    if tamanho is None:
        return None

    fator = ESCALA_SPRITES_JOGO

    return pygame.Rect(
        sprite["x"],
        sprite["y"],
        round(tamanho[0] * fator),
        round(tamanho[1] * fator)
    )


def encontrar_sprite(posicao):
    px, py = posicao

    # A camada superior é desenhada por último e tem prioridade.
    for camada in reversed(CAMADAS_SPRITES):
        for sprite in reversed(obter_instancias_sprites(camada)):
            rect = obter_rect_sprite(sprite, camada=camada)

            if rect and rect.collidepoint(px, py):
                return sprite, camada

    return None, None



# ==========================================================
# SALVAR
# ==========================================================

def salvar_mapa():
    print(f"[DIAGNOSTICO] Salvando {len(obstaculos)} obstaculos")
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


def salvar_tamanhos_sprites():
    """Persiste os tamanhos visuais no próprio arquivo do mapa."""
    dados_mapa["tamanhos_sprites"] = tamanhos_sprites

    sprites_por_camada = dados_mapa.setdefault("sprites_por_camada", {})
    sprites_por_camada.setdefault("superior", dados_mapa.get("sprites_superiores", []))
    dados_mapa["sprites_superiores"] = sprites_por_camada["superior"]

    CAMINHO_MAPA.write_text(
        json.dumps(dados_mapa, indent=4, ensure_ascii=False) + "\\n",
        encoding="utf-8"
    )


def ajustar_tamanho_sprite(propriedade, variacao):
    if sprite_selecionado is None or camada_sprite_selecionada is None:
        return

    imagem = obter_imagem_sprite(
        sprite_selecionado, camada_sprite_selecionada
    )
    if imagem is None:
        return

    configuracao = tamanhos_sprites.setdefault(
        camada_sprite_selecionada, {}
    ).setdefault(
        sprite_selecionado,
        {
            "largura": imagem.get_width(),
            "altura": imagem.get_height()
        }
    )

    configuracao[propriedade] = max(
        1, int(configuracao[propiedade]) + variacao
    )

    salvar_tamanhos_sprites()


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

    area_topo = ALTURA_CABECALHO
    area_altura = max(100, altura - ALTURA_CABECALHO - ALTURA_RODAPE)

    margem_esquerda = LARGURA_PAINEL_ESQUERDO
    margem_direita = LARGURA_PAINEL_DIREITO

    largura_util = max(
        100,
        largura - margem_esquerda - margem_direita
    )

    escala_base = min(
        largura_util / IMG_LARGURA,
        area_altura / IMG_ALTURA
    )

    zoom_atual = (
        zoom_recurso
        if modo == "recursos" and not visualizacao_recurso_ativa
        else zoom
    )
    escala = escala_base * zoom_atual

    w = max(1, round(IMG_LARGURA * escala))
    h = max(1, round(IMG_ALTURA * escala))

    x = (
        margem_esquerda
        + (largura_util - w) // 2
        + round(pan_x)
    )
    y = area_topo + (area_altura - h) // 2 + round(pan_y)

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


def ponto_para_sprite(ponto, instancia, camada=None):
    """Converte coordenadas visuais para pixels da imagem original."""
    identificador = instancia.get("id")
    imagem = obter_imagem_sprite(identificador, camada)

    if imagem is None:
        return None

    largura_visual, altura_visual = obter_tamanho_sprite(
        identificador, camada
    )

    local_x = (
        (ponto[0] - instancia["x"])
        / ESCALA_SPRITES_JOGO
        * imagem.get_width() / largura_visual
    )
    local_y = (
        (ponto[1] - instancia["y"])
        / ESCALA_SPRITES_JOGO
        * imagem.get_height() / altura_visual
    )

    local_x = max(0, min(imagem.get_width(), int(local_x)))
    local_y = max(0, min(imagem.get_height(), int(local_y)))

    return local_x, local_y



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


def obter_colisao_sprite_selecionada():
    if sprite_selecionado is None:
        return None

    if colisao_sprite_selecionada is None:
        return None

    lista = colisoes_sprites.get(sprite_selecionado, [])

    if not 0 <= colisao_sprite_selecionada < len(lista):
        return None

    return lista[colisao_sprite_selecionada]


def obter_layout_painel_direito():
    """Define áreas independentes para informações, visual e colisão."""
    painel_x = tela.get_width() - LARGURA_PAINEL_DIREITO
    conteudo_x = painel_x + 14
    largura = LARGURA_PAINEL_DIREITO - 28
    topo = ALTURA_CABECALHO + 16

    area_informacoes = pygame.Rect(conteudo_x, topo, largura, 150)
    proximo_topo = area_informacoes.bottom + 10

    area_visual = None
    area_colisao = None

    if modo == "sprite" and sprite_selecionado is not None:
        area_visual = pygame.Rect(
            conteudo_x, proximo_topo, largura, 94
        )
        proximo_topo = area_visual.bottom + 10

    if modo == "sprite" and obter_colisao_sprite_selecionada():
        area_colisao = pygame.Rect(
            conteudo_x, proximo_topo, largura, 150
        )
        proximo_topo = area_colisao.bottom + 10

    limite_inferior = tela.get_height() - ALTURA_RODAPE - 10

    area_ferramentas = pygame.Rect(
        conteudo_x,
        proximo_topo,
        largura,
        max(0, limite_inferior - proximo_topo)
    )

    return {
        "informacoes": area_informacoes,
        "visual": area_visual,
        "colisao": area_colisao,
        "ferramentas": area_ferramentas,
    }



def obter_botoes_propriedades_sprite():
    """Posiciona os botões dentro da área reservada para colisão."""
    """Posiciona os botoes dentro da area reservada para colisao."""

    layout = obter_layout_painel_direito()
    area = layout["colisao"]

    if area is None:
        return {}

    x = area.x
    y = area.y + 28

    botoes = {}

    for indice, propriedade in enumerate(
        ("x", "y", "largura", "altura")
    ):
        linha_y = y + indice * 30

        botoes[propriedade] = {
            "menos": pygame.Rect(x + 218, linha_y, 24, 22),
            "mais": pygame.Rect(x + 246, linha_y, 24, 22),
        }

    return botoes


def obter_botoes_tamanho_sprite():
    layout = obter_layout_painel_direito()
    area = layout["visual"]

    if area is None:
        return {}

    botoes = {}
    for indice, propriedade in enumerate(("largura", "altura")):
        linha_y = area.y + 30 + indice * 30
        botoes[propriedade] = {
            "menos": pygame.Rect(area.x + 218, linha_y, 24, 22),
            "mais": pygame.Rect(area.x + 246, linha_y, 24, 22),
        }

    return botoes


def ajustar_colisao_sprite(propriedade, variacao):
    """Ajusta uma propriedade respeitando os limites do sprite."""
    colisao = obter_colisao_sprite_selecionada()

    if colisao is None:
        return

    imagem = obter_imagem_sprite(
        sprite_selecionado, camada_sprite_selecionada
    )

    if imagem is None:
        return

    largura_sprite = imagem.get_width()
    altura_sprite = imagem.get_height()

    x = colisao["x"]
    y = colisao["y"]
    largura = colisao["largura"]
    altura = colisao["altura"]

    if propriedade == "x":
        colisao["x"] = max(
            0,
            min(largura_sprite - largura, x + variacao)
        )

    elif propriedade == "y":
        colisao["y"] = max(
            0,
            min(altura_sprite - altura, y + variacao)
        )

    elif propriedade == "largura":
        colisao["largura"] = max(
            1,
            min(largura_sprite - x, largura + variacao)
        )

    elif propriedade == "altura":
        colisao["altura"] = max(
            1,
            min(altura_sprite - y, altura + variacao)
        )

    salvar_sprites()


def encontrar_colisao_sprite(instancia, ponto, camada=None):
    identificador = chave_sprite(instancia)
    lista = obter_colisoes_sprite(identificador)
    local = ponto_para_sprite(ponto, instancia, camada)

    if local is None:
        return None

    local_x, local_y = local

    for indice in range(len(lista) - 1, -1, -1):
        item = lista[indice]
        retangulo = pygame.Rect(
            item["x"], item["y"],
            item["largura"], item["altura"]
        )
        if retangulo.collidepoint(local_x, local_y):
            return indice

    return None



def apagar_colisao_sprite(posicao):
    global colisao_sprite_selecionada
    ponto = mouse_para_imagem(posicao)

    if ponto is None:
        return

    instancia, camada = encontrar_sprite(ponto)

    if instancia is None:
        return

    identificador = chave_sprite(instancia)
    lista = obter_colisoes_sprite(identificador)

    local = ponto_para_sprite(ponto, instancia, camada)
    if local is None:
        return
    local_x, local_y = local

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
            if colisao_sprite_selecionada == i:
                colisao_sprite_selecionada = None
            elif (
                colisao_sprite_selecionada is not None
                and colisao_sprite_selecionada > i
            ):
                colisao_sprite_selecionada -= 1
            salvar_sprites()
            return

def desenhar_colisoes_sprites(area, escala):
    fator = ESCALA_SPRITES_JOGO

    for camada in CAMADAS_SPRITES:
        for instancia in obter_instancias_sprites(camada):
            identificador = chave_sprite(instancia)
            lista = colisoes_sprites.get(identificador, [])

            for indice, item in enumerate(lista):
                visual = pygame.Rect(
                    area.x + round(
                        (instancia["x"] + item["x"] * fator) * escala
                    ),
                    area.y + round(
                        (instancia["y"] + item["y"] * fator) * escala
                    ),
                    max(1, round(item["largura"] * fator * escala)),
                    max(1, round(item["altura"] * fator * escala))
                )

                selecionada = (
                    identificador == sprite_selecionado
                    and camada == camada_sprite_selecionada
                    and indice == colisao_sprite_selecionada
                )
                cor = COR_SELECAO if selecionada else COR_SPRITE
                pygame.draw.rect(
                    tela, cor, visual, 3 if selecionada else 2
                )

            if (
                identificador == sprite_selecionado
                and camada == camada_sprite_selecionada
            ):
                rect = obter_rect_sprite(instancia, camada=camada)
                if rect:
                    visual = pygame.Rect(
                        area.x + round(instancia["x"] * escala),
                        area.y + round(instancia["y"] * escala),
                        max(1, round(rect.width * escala)),
                        max(1, round(rect.height * escala))
                    )
                    pygame.draw.rect(tela, COR_SELECAO, visual, 1)


def desenhar_sprites_camada(camada, area, escala):
    biblioteca = bibliotecas_sprites.get(camada, {})
    fator = ESCALA_SPRITES_JOGO * escala

    for instancia in obter_instancias_sprites(camada):
        identificador = instancia.get("id")
        imagem = biblioteca.get(identificador)

        if imagem is None:
            continue

        largura, altura = obter_tamanho_sprite(identificador, camada)
        tamanho = (
            max(1, round(largura * fator)),
            max(1, round(altura * fator))
        )

        redimensionada = pygame.transform.scale(imagem, tamanho)
        x = area.x + round(instancia["x"] * escala)
        y = area.y + round(instancia["y"] * escala)

        tela.blit(redimensionada, (x, y))


def desenhar_sprites_terreno(area, escala):
    desenhar_sprites_camada("terreno", area, escala)


def desenhar_sprites_superiores(area, escala):
    desenhar_sprites_camada("superior", area, escala)



def apagar_proximo(posicao):
    if modo == "recursos":
        apagar_retangulo_recurso(posicao)
        return

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
# PAINEL DE RECURSOS E ITENS
# ==========================================================

def obter_layout_previa_recurso(item, posicao=None):
    """Calcula a posição e o tamanho do recurso na área central."""

    if item is None:
        return {"area": None, "escala": 0.0, "sprite": None}

    area, escala = area_imagem()

    largura = max(1, round(int(item["largura_visual"]) * escala))
    altura = max(1, round(int(item["altura_visual"]) * escala))

    if visualizacao_recurso_ativa:
        alvo = posicao if posicao is not None else pygame.mouse.get_pos()
        x = alvo[0] - largura // 2
        y = alvo[1] - altura // 2

        if largura >= area.width:
            x = area.centerx - largura // 2
        else:
            x = max(area.left, min(x, area.right - largura))

        if altura >= area.height:
            y = area.centery - altura // 2
        else:
            y = max(area.top, min(y, area.bottom - altura))
    else:
        x = area.centerx - largura // 2
        y = area.centery - altura // 2

    return {
        "area": area,
        "escala": escala,
        "sprite": pygame.Rect(x, y, largura, altura),
    }


def retangulo_catalogo_para_previa(retangulo, item, sprite):
    """Converte um retângulo do catálogo para coordenadas da tela."""

    escala_x = sprite.width / max(1, int(item["largura_visual"]))
    escala_y = sprite.height / max(1, int(item["altura_visual"]))

    x = sprite.x + round(retangulo["x"] * escala_x)
    y = sprite.y + round(retangulo["y"] * escala_y)
    largura = max(1, round(retangulo["largura"] * escala_x))
    altura = max(1, round(retangulo["altura"] * escala_y))

    return pygame.Rect(x, y, largura, altura)


def ponto_previa_para_recurso(posicao, item, sprite):
    """Converte a posição do mouse para coordenadas locais do recurso."""

    escala_x = sprite.width / max(1, int(item["largura_visual"]))
    escala_y = sprite.height / max(1, int(item["altura_visual"]))

    x = round((posicao[0] - sprite.x) / escala_x)
    y = round((posicao[1] - sprite.y) / escala_y)

    x = max(0, min(x, int(item["largura_visual"])))
    y = max(0, min(y, int(item["altura_visual"])))

    return x, y


def indice_retangulo_recurso(secao, item):
    """Retorna o índice atualmente selecionado na seção."""

    if secao == "colisao":
        indice = colisao_recurso_selecionada
    elif secao == "interacao":
        indice = interacao_recurso_selecionada
    else:
        return None

    if indice is None or not 0 <= indice < len(item.get(secao, [])):
        return None

    return indice


def encontrar_retangulo_recurso(item, secao, posicao, sprite):
    """Localiza o retângulo da seção atingido pelo mouse."""

    for indice in range(len(item.get(secao, [])) - 1, -1, -1):
        retangulo = retangulo_catalogo_para_previa(
            item[secao][indice], item, sprite
        )

        if retangulo.collidepoint(posicao):
            return indice

    return None


def salvar_desenho_previa_recurso():
    """Persiste o retângulo desenhado na seção selecionada."""

    global itens_editor
    global colisao_recurso_selecionada, interacao_recurso_selecionada

    item = catalogo_editor.obter(item_selecionado_id)

    if (
        item is None
        or inicio_previa_recurso is None
        or fim_previa_recurso is None
    ):
        return

    x1, y1 = inicio_previa_recurso
    x2, y2 = fim_previa_recurso

    retangulo = {
        "x": min(x1, x2),
        "y": min(y1, y2),
        "largura": max(1, abs(x2 - x1)),
        "altura": max(1, abs(y2 - y1)),
    }

    secao = ferramenta_recurso
    if secao not in ("colisao", "interacao"):
        secao = "colisao"

    dados = dict(item)
    dados["colisao"] = [dict(r) for r in item.get("colisao", [])]
    dados["interacao"] = [dict(r) for r in item.get("interacao", [])]

    if secao == "colisao":
        retangulo["ativa"] = bool(item.get("solido", True))
        dados["colisao"].append(retangulo)
        colisao_recurso_selecionada = len(dados["colisao"]) - 1
    else:
        dados["interacao"].append(retangulo)
        interacao_recurso_selecionada = len(dados["interacao"]) - 1

    catalogo_editor.atualizar(item_selecionado_id, dados)
    itens_editor = catalogo_editor.listar()


def apagar_retangulo_recurso(posicao):
    """Remove o retângulo atingido na seção atualmente selecionada."""

    global itens_editor
    global colisao_recurso_selecionada, interacao_recurso_selecionada

    item = catalogo_editor.obter(item_selecionado_id)
    if item is None:
        return

    secao = ferramenta_recurso
    if secao not in ("colisao", "interacao"):
        secao = "colisao"

    layout = obter_layout_previa_recurso(item, posicao)
    sprite = layout["sprite"]

    if sprite is None or not sprite.collidepoint(posicao):
        return

    indice = encontrar_retangulo_recurso(item, secao, posicao, sprite)
    if indice is None:
        return

    dados = dict(item)
    dados["colisao"] = [dict(r) for r in item.get("colisao", [])]
    dados["interacao"] = [dict(r) for r in item.get("interacao", [])]

    del dados[secao][indice]

    catalogo_editor.atualizar(item_selecionado_id, dados)
    itens_editor = catalogo_editor.listar()

    if secao == "colisao":
        colisao_recurso_selecionada = None
    else:
        interacao_recurso_selecionada = None


def obter_painel_recursos():
    largura, altura = tela.get_size()

    return pygame.Rect(
        largura - LARGURA_PAINEL_DIREITO,
        ALTURA_CABECALHO,
        LARGURA_PAINEL_DIREITO,
        max(100, altura - ALTURA_CABECALHO - ALTURA_RODAPE)
    )


def obter_lista_recursos():
    altura = tela.get_height()

    return pygame.Rect(
        10,
        ALTURA_CABECALHO + 42,
        LARGURA_PAINEL_ESQUERDO - 20,
        max(70, altura - ALTURA_CABECALHO - ALTURA_RODAPE - 52)
    )


def selecionar_recurso_pelo_mouse(posicao):
    global item_selecionado_id
    global colisao_recurso_selecionada, interacao_recurso_selecionada
    global zoom_recurso
    global visualizacao_recurso_ativa, centro_previa_recurso
    global arrastando_previa_recurso, inicio_previa_recurso, fim_previa_recurso

    lista = obter_lista_recursos()

    if not lista.collidepoint(posicao):
        return

    indice = (
        (posicao[1] - lista.y + rolagem_itens)
        // ALTURA_LINHA_RECURSO
    )

    if 0 <= indice < len(itens_editor):
        novo_id = itens_editor[indice]["id"]

        if novo_id != item_selecionado_id:
            item_selecionado_id = novo_id

            item = catalogo_editor.obter(novo_id)
            if item is not None:
                largura_tela = max(
                    100,
                    tela.get_width()
                    - LARGURA_PAINEL_ESQUERDO
                    - LARGURA_PAINEL_DIREITO
                )
                altura_tela = max(
                    100,
                    tela.get_height()
                    - ALTURA_CABECALHO
                    - ALTURA_RODAPE
                )

                escala_base = min(
                    largura_tela / IMG_LARGURA,
                    altura_tela / IMG_ALTURA
                )

                escala_ajustada = min(
                    largura_tela / max(1, int(item["largura_visual"])),
                    altura_tela / max(1, int(item["altura_visual"]))
                ) * 0.90

                zoom_recurso = max(
                    0.05,
                    min(zoom_maximo, escala_ajustada / escala_base)
                )

            colisao_recurso_selecionada = None
            interacao_recurso_selecionada = None
            visualizacao_recurso_ativa = False
            centro_previa_recurso = None
            arrastando_previa_recurso = False
            inicio_previa_recurso = None
            fim_previa_recurso = None



def ajustar_propriedade_recurso(secao, propriedade, variacao):
    """Atualiza uma propriedade do recurso e persiste no catalogo."""

    global itens_editor

    item = catalogo_editor.obter(item_selecionado_id)

    if item is None:
        return

    dados = dict(item)
    dados["colisao"] = [dict(r) for r in item["colisao"]]
    dados["interacao"] = [dict(r) for r in item["interacao"]]

    if secao == "visual":
        if propriedade not in ("largura_visual", "altura_visual"):
            return

        dados[propriedade] = max(
            1,
            min(512, dados[propriedade] + variacao)
        )

    elif secao in ("colisao", "interacao"):
        if propriedade not in ("x", "y", "largura", "altura"):
            return

        indice = indice_retangulo_recurso(secao, item)

        if indice is None:
            return

        retangulo = dados[secao][indice]

        if propriedade in ("largura", "altura"):
            retangulo[propriedade] = max(
                1,
                retangulo[propriedade] + variacao
            )
        else:
            retangulo[propriedade] += variacao

    else:
        return

    catalogo_editor.atualizar(item_selecionado_id, dados)
    itens_editor = catalogo_editor.listar()


def obter_botoes_recursos():
    """Retorna os controles visiveis do painel de recursos."""

    painel = obter_painel_recursos()
    x = painel.x + 14
    largura = painel.width - 28
    botoes = {}

    def adicionar_dimensao(propriedade, y):
        botoes[("visual", propriedade)] = {
            "-8": pygame.Rect(x + largura - 112, y, 24, 21),
            "-1": pygame.Rect(x + largura - 84, y, 24, 21),
            "+1": pygame.Rect(x + largura - 56, y, 24, 21),
            "+8": pygame.Rect(x + largura - 28, y, 24, 21),
        }

    adicionar_dimensao("largura_visual", ALTURA_CABECALHO + 184)
    adicionar_dimensao("altura_visual", ALTURA_CABECALHO + 213)

    botoes[("ferramenta", "colisao")] = pygame.Rect(
        x, ALTURA_CABECALHO + 385, largura, 30
    )

    return botoes


def obter_botao_visualizar_recurso():
    painel = obter_painel_recursos()
    return pygame.Rect(
        painel.x + 14,
        ALTURA_CABECALHO + 112,
        painel.width - 28,
        38
    )


def desenhar_previa_recurso_central():
    # A previa fica visivel no centro; VISUALIZAR faz acompanhar o mouse.
    item = catalogo_editor.obter(item_selecionado_id)
    if item is None:
        return

    layout = obter_layout_previa_recurso(item)
    sprite = layout["sprite"]
    if sprite is None:
        return

    if item.get("imagem"):
        imagem = obter_imagem(
            item["imagem"],
            (int(item["largura_visual"]), int(item["altura_visual"]))
        )
    else:
        imagem = None

    if imagem is not None:
        tela.blit(pygame.transform.smoothscale(imagem, sprite.size), sprite.topleft)
    else:
        pygame.draw.rect(tela, PAINEL_CLARO, sprite, border_radius=4)
        pygame.draw.rect(tela, COR_DESTAQUE, sprite, 2, border_radius=4)
        identificador = fonte_pequena.render(item["id"], True, COR_TEXTO)
        tela.blit(identificador, identificador.get_rect(center=sprite.center))

    if mostrar_bordas:
        # A colisao e a unica geometria dos recursos.
        for indice, retangulo in enumerate(item.get("colisao", [])):
            visual = retangulo_catalogo_para_previa(
                retangulo, item, sprite
            )
            pygame.draw.rect(
                tela,
                COR_OBSTACULO,
                visual,
                3 if indice == colisao_recurso_selecionada else 2
            )

        # Mostra o retangulo em criacao antes de salvar.
        if arrastando_previa_recurso and inicio_previa_recurso is not None and fim_previa_recurso is not None:
            x1, y1 = inicio_previa_recurso
            x2, y2 = fim_previa_recurso
            visual = retangulo_catalogo_para_previa(
                {"x": min(x1, x2), "y": min(y1, y2),
                 "largura": max(1, abs(x2 - x1)),
                 "altura": max(1, abs(y2 - y1))},
                item, sprite
            )
            cor = COR_OBSTACULO if ferramenta_recurso == "colisao" else COR_INTERACAO
            pygame.draw.rect(tela, cor, visual, 2)


def desenhar_painel_recursos():
    altura = tela.get_height()
    painel = obter_painel_recursos()
    lista = obter_lista_recursos()
    item = catalogo_editor.obter(item_selecionado_id)
    botoes = obter_botoes_recursos()

    painel_esquerdo = pygame.Rect(
        0, ALTURA_CABECALHO, LARGURA_PAINEL_ESQUERDO,
        max(100, altura - ALTURA_CABECALHO - ALTURA_RODAPE)
    )
    pygame.draw.rect(tela, PAINEL, painel_esquerdo)
    pygame.draw.line(tela, PAINEL_CLARO, painel_esquerdo.topright, painel_esquerdo.bottomright, 1)
    tela.blit(fonte.render("RECURSOS E ITENS", True, COR_DESTAQUE), (12, ALTURA_CABECALHO + 12))

    pygame.draw.rect(tela, FUNDO, lista, border_radius=5)
    tela.set_clip(lista)
    for indice, recurso in enumerate(itens_editor):
        y_linha = lista.y + indice * ALTURA_LINHA_RECURSO - rolagem_itens
        linha = pygame.Rect(lista.x + 2, y_linha, lista.width - 4, ALTURA_LINHA_RECURSO - 2)
        selecionado = recurso["id"] == item_selecionado_id
        if selecionado:
            pygame.draw.rect(tela, PAINEL_CLARO, linha, border_radius=4)
            pygame.draw.rect(tela, COR_DESTAQUE, linha, 1, border_radius=4)
        tela.blit(fonte_pequena.render(recurso["nome"], True, COR_TEXTO if selecionado else COR_SECUNDARIA), (linha.x + 7, linha.y + 3))
        tela.blit(fonte_pequena.render(recurso["categoria"].capitalize(), True, COR_DESTAQUE if selecionado else COR_SECUNDARIA), (linha.x + 7, linha.y + 19))
    tela.set_clip(None)

    pygame.draw.rect(tela, PAINEL, painel)
    pygame.draw.line(tela, PAINEL_CLARO, painel.topleft, painel.bottomleft, 1)
    x = painel.x + 14
    tela.blit(fonte.render("PROPRIEDADES", True, COR_DESTAQUE), (x, ALTURA_CABECALHO + 14))
    if item is None:
        tela.blit(fonte_pequena.render("Selecione um recurso.", True, COR_SECUNDARIA), (x, ALTURA_CABECALHO + 52))
        return

    tela.blit(fonte.render(item["nome"], True, COR_TEXTO), (x, ALTURA_CABECALHO + 48))
    tela.blit(fonte_pequena.render(f'{item["categoria"].capitalize()} | ID: {item["id"]}', True, COR_SECUNDARIA), (x, ALTURA_CABECALHO + 74))

    botao_visualizar = obter_botao_visualizar_recurso()
    pygame.draw.rect(tela, COR_DESTAQUE if visualizacao_recurso_ativa else PAINEL_CLARO, botao_visualizar, border_radius=5)
    pygame.draw.rect(tela, COR_DESTAQUE, botao_visualizar, 1, border_radius=5)
    texto = fonte.render("VOLTAR AO MINERIO" if visualizacao_recurso_ativa else "VISUALIZAR NO MAPA", True, COR_TEXTO)
    tela.blit(texto, texto.get_rect(center=botao_visualizar.center))

    y = ALTURA_CABECALHO + 166
    pygame.draw.line(tela, PAINEL_CLARO, (x, y), (painel.right - 14, y), 1)
    tela.blit(
        fonte_pequena.render("DIMENSOES VISUAIS", True, COR_DESTAQUE),
        (x, y + 12)
    )

    def desenhar_controle(rotulo, valor, chave, y_controle):
        tela.blit(
            fonte_pequena.render(f"{rotulo}: {valor} px", True, COR_TEXTO),
            (x + 4, y_controle)
        )

        controles = botoes[chave]
        for sinal, rect in controles.items():
            pygame.draw.rect(tela, PAINEL_CLARO, rect, border_radius=3)
            pygame.draw.rect(tela, COR_DESTAQUE, rect, 1, border_radius=3)
            texto = fonte_pequena.render(sinal, True, COR_TEXTO)
            tela.blit(texto, texto.get_rect(center=rect.center))

    desenhar_controle(
        "Largura", item["largura_visual"],
        ("visual", "largura_visual"), ALTURA_CABECALHO + 190
    )
    desenhar_controle(
        "Altura", item["altura_visual"],
        ("visual", "altura_visual"), ALTURA_CABECALHO + 219
    )

    tela.blit(
        fonte_pequena.render("AREA DE COLISAO", True, COR_DESTAQUE),
        (x, ALTURA_CABECALHO + 339)
    )

    lista_areas = item.get("colisao", [])
    indice = indice_retangulo_recurso("colisao", item)
    tela.blit(
        fonte_pequena.render(f"{len(lista_areas)} colisao(oes)", True, COR_TEXTO),
        (x + 3, ALTURA_CABECALHO + 362)
    )

    rect_ferramenta = botoes[("ferramenta", "colisao")]
    pygame.draw.rect(tela, COR_DESTAQUE, rect_ferramenta, border_radius=4)
    texto_botao = fonte_pequena.render("EDITAR COLISOES", True, COR_TEXTO)
    tela.blit(texto_botao, texto_botao.get_rect(center=rect_ferramenta.center))

    tela.blit(
        fonte_pequena.render("Arraste sobre o recurso para adicionar.", True, COR_SECUNDARIA),
        (x + 3, ALTURA_CABECALHO + 425)
    )
    tela.blit(
        fonte_pequena.render("Botao direito: excluir area.", True, COR_SECUNDARIA),
        (x + 3, ALTURA_CABECALHO + 445)
    )


# INTERFACE UNIFICADA
# ==========================================================

MODOS_EDITOR = [
    ("mapa", "MAPA", pygame.K_1),
    ("interacao", "INTERACAO", pygame.K_2),
    ("sprite", "SPRITES", pygame.K_3),
    ("recursos", "RECURSOS", pygame.K_4),
    ("personagem", "PERSONAGEM", pygame.K_5),
]


def obter_botoes_modos():
    botoes = {}
    x_inicial = 235
    largura = 122
    espacamento = 7

    for identificador, nome, _ in MODOS_EDITOR:
        botoes[identificador] = pygame.Rect(
            x_inicial, 10, largura, 44
        )
        x_inicial += largura + espacamento

    return botoes


def finalizar_edicao_personagem(posicao=None):
    global edicao_personagem

    if edicao_personagem is None:
        return

    if posicao is not None:
        atualizar_edicao_personagem(posicao)

    limitar_colisao_personagem()
    salvar_config_personagem()
    edicao_personagem = None


def selecionar_modo(novo_modo):
    global modo, sprite_selecionado, instancia_selecionada
    global camada_sprite_selecionada
    global colisao_sprite_selecionada
    global colisao_recurso_selecionada, interacao_recurso_selecionada
    global arrastando, inicio, fim, ferramenta_recurso
    global visualizacao_recurso_ativa, centro_previa_recurso
    global visualizacao_personagem_ativa
    global arrastando_previa_recurso, inicio_previa_recurso, fim_previa_recurso
    global edicao_personagem

    finalizar_edicao_personagem()
    if novo_modo != "personagem":
        visualizacao_personagem_ativa = False
    modo = novo_modo
    if novo_modo == "recursos":
        ferramenta_recurso = "colisao"

    if novo_modo != "recursos":
        visualizacao_recurso_ativa = False
        centro_previa_recurso = None
        arrastando_previa_recurso = False
        inicio_previa_recurso = None
        fim_previa_recurso = None
    sprite_selecionado = None
    instancia_selecionada = None
    camada_sprite_selecionada = None
    colisao_sprite_selecionada = None
    colisao_recurso_selecionada = None
    interacao_recurso_selecionada = None
    arrastando = False
    inicio = None
    fim = None


def texto_ajustado(texto, fonte_texto, cor, largura_maxima):
    texto = str(texto)
    superficie = fonte_texto.render(texto, True, cor)

    if superficie.get_width() <= largura_maxima:
        return superficie

    sufixo = "..."
    while texto and fonte_texto.size(texto + sufixo)[0] > largura_maxima:
        texto = texto[:-1]

    return fonte_texto.render(texto + sufixo, True, cor)


def desenhar_paineis_contextuais():
    largura_tela, altura_tela = tela.get_size()
    altura = max(
        100,
        altura_tela - ALTURA_CABECALHO - ALTURA_RODAPE
    )

    esquerdo = pygame.Rect(
        0, ALTURA_CABECALHO,
        LARGURA_PAINEL_ESQUERDO, altura
    )

    direito = pygame.Rect(
        largura_tela - LARGURA_PAINEL_DIREITO,
        ALTURA_CABECALHO,
        LARGURA_PAINEL_DIREITO, altura
    )

    pygame.draw.rect(tela, PAINEL, esquerdo)
    pygame.draw.rect(tela, PAINEL, direito)

    pygame.draw.line(
        tela, PAINEL_CLARO,
        esquerdo.topright, esquerdo.bottomright, 1
    )
    pygame.draw.line(
        tela, PAINEL_CLARO,
        direito.topleft, direito.bottomleft, 1
    )

    x = 14
    y = ALTURA_CABECALHO + 16

    titulos = {
        "mapa": "COLISOES DO MAPA",
        "interacao": "AREAS DE INTERACAO",
        "sprite": "SPRITES",
    }

    titulo = fonte.render(
        titulos[modo], True, COR_DESTAQUE
    )
    tela.blit(titulo, (x, y))

    y += 38

    if modo == "mapa":
        linhas = [
            ("Obstaculos", len(obstaculos)),
            ("Grade", "Ativa" if mostrar_grade else "Inativa"),
            ("Bordas", "Visiveis" if mostrar_bordas else "Ocultas"),
        ]
        instrucoes = [
            "Clique e arraste no mapa",
            "para criar uma colisao.",
            "",
            "Botao direito:",
            "remover colisao.",
        ]

    elif modo == "interacao":
        linhas = [
            ("Areas cadastradas", len(areas_interacao)),
        ]
        instrucoes = [
            "Clique e arraste no mapa",
            "para criar uma area.",
            "",
            "Botao direito:",
            "remover area.",
        ]

    else:
        instancias = obter_instancias_sprites()
        linhas = [
            ("Sprites no mapa", len(instancias)),
            ("Tipos carregados", len(sprites_superiores)),
            (
                "Selecionado",
                sprite_selecionado or "Nenhum"
            ),
        ]
        instrucoes = [
            "Selecione um sprite no mapa.",
            "",
            "Depois, arraste sobre ele",
            "para criar uma colisao.",
            "",
            "Botao direito:",
            "remover colisao.",
        ]

    for rotulo, valor in linhas:
        texto = texto_ajustado(
            f"{rotulo}: {valor}",
            fonte_pequena,
            COR_TEXTO,
            LARGURA_PAINEL_ESQUERDO - 22
        )
        tela.blit(texto, (x + 3, y))
        y += 27

    y += 22

    secao = fonte_pequena.render(
        "COMO UTILIZAR", True, COR_DESTAQUE
    )
    tela.blit(secao, (x, y))
    y += 28

    for linha in instrucoes:
        if linha:
            texto = fonte_pequena.render(
                linha, True, COR_SECUNDARIA
            )
            tela.blit(texto, (x + 3, y))
        y += 21

    # Painel direito: secoes com areas reservadas.
    layout = obter_layout_painel_direito()

    area_informacoes = layout["informacoes"]
    area_visual = layout["visual"]
    area_colisao = layout["colisao"]
    area_ferramentas = layout["ferramentas"]

    for area_secao in (
        area_informacoes,
        area_visual,
        area_colisao,
        area_ferramentas
    ):
        if area_secao is not None and area_secao.height > 0:
            pygame.draw.rect(
                tela,
                FUNDO,
                area_secao,
                border_radius=6
            )
            pygame.draw.rect(
                tela,
                PAINEL_CLARO,
                area_secao,
                1,
                border_radius=6
            )

    x = area_informacoes.x + 10
    y = area_informacoes.y

    titulo_direito = fonte.render(
        "PROPRIEDADES", True, COR_DESTAQUE
    )
    tela.blit(titulo_direito, (x, y))
    y += 42

    dados = {
        "mapa": [
            ("Modo", "Colisao do mapa"),
            ("Elementos", len(obstaculos)),
            ("Cor", "Vermelho"),
        ],
        "interacao": [
            ("Modo", "Area de interacao"),
            ("Elementos", len(areas_interacao)),
            ("Cor", "Azul"),
        ],
        "sprite": [
            ("Modo", "Colisao de sprite"),
            ("Sprite", sprite_selecionado or "Nenhum"),
        ],
    }

    for rotulo, valor in dados[modo]:
        rotulo_render = fonte_pequena.render(
            rotulo.upper(), True, COR_SECUNDARIA
        )
        tela.blit(rotulo_render, (x, y))
        y += 19

        valor_render = texto_ajustado(
            valor,
            fonte,
            COR_TEXTO,
            LARGURA_PAINEL_DIREITO - 28
        )
        tela.blit(valor_render, (x, y))
        y += 38

    if area_visual is not None:
        imagem_sprite = obter_imagem_sprite(
            sprite_selecionado, camada_sprite_selecionada
        )
        if imagem_sprite is not None:
            largura_visual, altura_visual = obter_tamanho_sprite(
                sprite_selecionado, camada_sprite_selecionada
            )

            x_visual = area_visual.x + 10
            y_visual = area_visual.y

            titulo_visual = fonte_pequena.render(
                "TAMANHO VISUAL", True, COR_DESTAQUE
            )
            tela.blit(titulo_visual, (x_visual, y_visual))

            botoes_tamanho = obter_botoes_tamanho_sprite()
            for rotulo, propriedade, valor in (
                ("Largura", "largura", largura_visual),
                ("Altura", "altura", altura_visual),
            ):
                linha_y = botoes_tamanho[propriedade]["menos"].y

                tela.blit(
                    fonte_pequena.render(
                        rotulo, True, COR_SECUNDARIA
                    ),
                    (x_visual, linha_y + 4)
                )
                tela.blit(
                    fonte.render(str(valor), True, COR_TEXTO),
                    (x_visual + 160, linha_y + 2)
                )

                for botao in botoes_tamanho[propriedade].values():
                    pygame.draw.rect(
                        tela, PAINEL_CLARO, botao, border_radius=4
                    )
                    simbolo = "+" if botao.x > x_visual + 230 else "-"
                    texto_botao = fonte_pequena.render(
                        simbolo, True, COR_TEXTO
                    )
                    tela.blit(
                        texto_botao,
                        texto_botao.get_rect(center=botao.center)
                    )

    if area_colisao is not None:
        colisao = obter_colisao_sprite_selecionada()

        if colisao is not None:
            x_colisao = area_colisao.x + 10
            y = area_colisao.y

            secao_colisao = fonte_pequena.render(
                "COLISAO SELECIONADA",
                True,
                COR_DESTAQUE
            )
            tela.blit(secao_colisao, (x_colisao, y))
            y += 28

            botoes = obter_botoes_propriedades_sprite()

            propriedades = [
                ("X", "x"),
                ("Y", "y"),
                ("Largura", "largura"),
                ("Altura", "altura"),
            ]

            for rotulo, propriedade in propriedades:
                linha_y = botoes[propriedade]["menos"].y

                texto_rotulo = fonte_pequena.render(
                    rotulo,
                    True,
                    COR_SECUNDARIA
                )
                tela.blit(texto_rotulo, (x_colisao, linha_y + 4))

                texto_valor = fonte.render(
                    str(colisao[propriedade]),
                    True,
                    COR_TEXTO
                )
                tela.blit(texto_valor, (x_colisao + 160, linha_y + 2))

                for operacao, botao in botoes[propriedade].items():
                    pygame.draw.rect(
                        tela,
                        PAINEL_CLARO,
                        botao,
                        border_radius=4
                    )

                    pygame.draw.rect(
                        tela,
                        COR_DESTAQUE,
                        botao,
                        1,
                        border_radius=4
                    )

                    simbolo = "-" if operacao == "menos" else "+"
                    texto_botao = fonte.render(
                        simbolo,
                        True,
                        COR_TEXTO
                    )

                    texto_rect = texto_botao.get_rect(
                        center=botao.center
                    )
                    tela.blit(texto_botao, texto_rect)

    area_ferramentas = layout["ferramentas"]
    x = area_ferramentas.x + 10
    y = area_ferramentas.y + 10

    ajuda = fonte_pequena.render(
        "FERRAMENTAS", True, COR_DESTAQUE
    )
    tela.blit(ajuda, (x, y))
    y += 28

    dicas = [
        "Scroll: zoom",
        "Botao do meio: mover mapa",
        "Clique direito: remover colisao",
    ] if modo == "sprite" else [
        "Scroll: zoom",
        "Botao do meio: mover mapa",
        "B: mostrar/ocultar bordas",
        "G: mostrar/ocultar grade",
        "Ctrl + S: salvar alteracoes",
    ]

    for dica in dicas:
        texto = fonte_pequena.render(
            dica, True, COR_SECUNDARIA
        )
        tela.blit(texto, (x, y))
        y += 25


def salvar_config_personagem():
    limitar_colisao_personagem()
    CAMINHO_CONFIG_PERSONAGEM.parent.mkdir(parents=True, exist_ok=True)

    with open(CAMINHO_CONFIG_PERSONAGEM, "w", encoding="utf-8") as arquivo:
        json.dump(config_personagem, arquivo, ensure_ascii=False, indent=4)
        arquivo.write("\n")


def obter_botoes_personagem():
    x = tela.get_width() - LARGURA_PAINEL_DIREITO + 14
    y = ALTURA_CABECALHO + 91

    propriedades = (
        ("visual", "largura"),
        ("visual", "altura"),
        ("colisao", "x"),
        ("colisao", "y"),
        ("colisao", "largura"),
        ("colisao", "altura"),
    )

    return {
        chave: {
            "menos": pygame.Rect(x + 202, y + indice * 43, 28, 25),
            "mais": pygame.Rect(x + 236, y + indice * 43, 28, 25),
        }
        for indice, chave in enumerate(propriedades)
    }


def ajustar_personagem(secao, propriedade, variacao):
    atual = config_personagem[secao][propriedade]
    minimo = 1 if propriedade in ("largura", "altura") else 0

    config_personagem[secao][propriedade] = max(
        minimo, atual + variacao
    )

    limitar_colisao_personagem()
    salvar_config_personagem()



def obter_layout_previa_personagem():
    visual = config_personagem["visual"]
    colisao = config_personagem["colisao"]

    if visualizacao_personagem_ativa:
        area, escala = area_imagem()
    else:
        largura_tela, altura_tela = tela.get_size()
        area = pygame.Rect(
            LARGURA_PAINEL_ESQUERDO,
            ALTURA_CABECALHO,
            max(100, largura_tela - LARGURA_PAINEL_ESQUERDO - LARGURA_PAINEL_DIREITO),
            max(100, altura_tela - ALTURA_CABECALHO - ALTURA_RODAPE),
        )

        escala = min(
            (area.width * 0.68) / max(1, visual["largura"]),
            (area.height * 0.72) / max(1, visual["altura"]),
        )

    largura = max(1, round(visual["largura"] * escala))
    altura = max(1, round(visual["altura"] * escala))

    visual_rect = pygame.Rect(0, 0, largura, altura)

    if visualizacao_personagem_ativa:
        visual_rect.center = pygame.mouse.get_pos()
        visual_rect.clamp_ip(area)
    else:
        visual_rect.center = area.center

    hitbox = pygame.Rect(
        visual_rect.x + round(colisao["x"] * escala),
        visual_rect.y + round(colisao["y"] * escala),
        max(1, round(colisao["largura"] * escala)),
        max(1, round(colisao["altura"] * escala)),
    )

    tamanho_alca = 8
    metade = tamanho_alca // 2

    alcas = {
        "n": pygame.Rect(hitbox.centerx - metade, hitbox.top - metade, tamanho_alca, tamanho_alca),
        "s": pygame.Rect(hitbox.centerx - metade, hitbox.bottom - metade, tamanho_alca, tamanho_alca),
        "e": pygame.Rect(hitbox.right - metade, hitbox.centery - metade, tamanho_alca, tamanho_alca),
        "w": pygame.Rect(hitbox.left - metade, hitbox.centery - metade, tamanho_alca, tamanho_alca),
        "ne": pygame.Rect(hitbox.right - metade, hitbox.top - metade, tamanho_alca, tamanho_alca),
        "nw": pygame.Rect(hitbox.left - metade, hitbox.top - metade, tamanho_alca, tamanho_alca),
        "se": pygame.Rect(hitbox.right - metade, hitbox.bottom - metade, tamanho_alca, tamanho_alca),
        "sw": pygame.Rect(hitbox.left - metade, hitbox.bottom - metade, tamanho_alca, tamanho_alca),
    }

    tamanho_alca_visual = 10
    alca_visual = pygame.Rect(
        visual_rect.right - tamanho_alca_visual // 2,
        visual_rect.bottom - tamanho_alca_visual // 2,
        tamanho_alca_visual,
        tamanho_alca_visual,
    )

    return {
        "area": area,
        "escala": escala,
        "visual": visual_rect,
        "colisao": hitbox,
        "alcas": alcas,
        "alca_visual": alca_visual,
    }


def ponto_previa_para_personagem(posicao, layout):
    escala = layout["escala"]
    visual = layout["visual"]

    x = (posicao[0] - visual.x) / escala
    y = (posicao[1] - visual.y) / escala

    return x, y


def atualizar_edicao_personagem(posicao):
    global edicao_personagem

    if edicao_personagem is None:
        return

    estado = edicao_personagem
    ponto = ponto_previa_para_personagem(
        posicao,
        estado["layout"],
    )

    visual = config_personagem["visual"]
    colisao = config_personagem["colisao"]

    if estado["tipo"] == "mover_colisao":
        dx = ponto[0] - estado["inicio"][0]
        dy = ponto[1] - estado["inicio"][1]

        original = estado["original"]

        colisao["x"] = round(original["x"] + dx)
        colisao["y"] = round(original["y"] + dy)

        limitar_colisao_personagem()

    elif estado["tipo"] == "redimensionar_colisao":
        original = estado["original"]
        dx = ponto[0] - estado["inicio"][0]
        dy = ponto[1] - estado["inicio"][1]

        esquerda = original["x"]
        topo = original["y"]
        direita = original["x"] + original["largura"]
        inferior = original["y"] + original["altura"]

        bordas = estado["bordas"]

        if "w" in bordas:
            esquerda = min(
                direita - 1,
                max(0, round(original["x"] + dx))
            )
        if "e" in bordas:
            direita = max(
                esquerda + 1,
                min(visual["largura"], round(
                    original["x"] + original["largura"] + dx
                ))
            )
        if "n" in bordas:
            topo = min(
                inferior - 1,
                max(0, round(original["y"] + dy))
            )
        if "s" in bordas:
            inferior = max(
                topo + 1,
                min(visual["altura"], round(
                    original["y"] + original["altura"] + dy
                ))
            )

        colisao.update({
            "x": esquerda,
            "y": topo,
            "largura": max(1, direita - esquerda),
            "altura": max(1, inferior - topo),
        })

        limitar_colisao_personagem()

    elif estado["tipo"] == "desenhar_colisao":
        inicio = estado["inicio"]

        x1 = max(0, min(visual["largura"], round(inicio[0])))
        y1 = max(0, min(visual["altura"], round(inicio[1])))
        x2 = max(0, min(visual["largura"], round(ponto[0])))
        y2 = max(0, min(visual["altura"], round(ponto[1])))

        esquerda = min(x1, x2)
        topo = min(y1, y2)
        direita = max(x1, x2)
        inferior = max(y1, y2)

        colisao.update({
            "x": esquerda,
            "y": topo,
            "largura": max(1, direita - esquerda),
            "altura": max(1, inferior - topo),
        })

        limitar_colisao_personagem()

    elif estado["tipo"] == "redimensionar_visual":
        dx = ponto[0] - estado["inicio"][0]
        dy = ponto[1] - estado["inicio"][1]

        visual["largura"] = max(
            8,
            min(256, round(estado["largura_inicial"] + dx))
        )
        visual["altura"] = max(
            8,
            min(256, round(estado["altura_inicial"] + dy))
        )

        limitar_colisao_personagem()


def iniciar_edicao_personagem(posicao):
    global edicao_personagem

    layout = obter_layout_previa_personagem()
    visual_rect = layout["visual"]
    hitbox = layout["colisao"]

    ponto = ponto_previa_para_personagem(posicao, layout)

    if layout["alca_visual"].collidepoint(posicao):
        edicao_personagem = {
            "tipo": "redimensionar_visual",
            "layout": layout,
            "inicio": ponto,
            "largura_inicial": config_personagem["visual"]["largura"],
            "altura_inicial": config_personagem["visual"]["altura"],
            "escala_inicial": layout["escala"],
        }
        return

    for alca, rect in layout["alcas"].items():
        if rect.collidepoint(posicao):
            edicao_personagem = {
                "tipo": "redimensionar_colisao",
                "layout": layout,
                "inicio": ponto,
                "original": dict(config_personagem["colisao"]),
                "bordas": alca,
            }
            return

    if hitbox.collidepoint(posicao):
        edicao_personagem = {
            "tipo": "mover_colisao",
            "layout": layout,
            "inicio": ponto,
            "original": dict(config_personagem["colisao"]),
        }
        return

    if visual_rect.collidepoint(posicao):
        edicao_personagem = {
            "tipo": "desenhar_colisao",
            "layout": layout,
            "inicio": ponto,
        }


def desenhar_previa_personagem():
    global sprite_previa_personagem

    if sprite_previa_personagem is None:
        caminho = (
            RAIZ / "assets" / "personagens" / "player" / "playerDown.png"
        )
        imagem = pygame.image.load(str(caminho)).convert_alpha()
        sprite_previa_personagem = imagem.subsurface(
            (0, 0, 32, 40)
        ).copy()

    layout = obter_layout_previa_personagem()
    visual_rect = layout["visual"]
    hitbox = layout["colisao"]

    sprite = pygame.transform.scale(
        sprite_previa_personagem,
        visual_rect.size,
    )
    tela.blit(sprite, visual_rect)

    if mostrar_bordas:
        if not visualizacao_personagem_ativa:
            pygame.draw.rect(tela, COR_DESTAQUE, visual_rect, 1)

        superficie = pygame.Surface(hitbox.size, pygame.SRCALPHA)
        superficie.fill((220, 55, 55, 55))
        tela.blit(superficie, hitbox.topleft)
        pygame.draw.rect(tela, COR_OBSTACULO, hitbox, 2)

        if not visualizacao_personagem_ativa:
            for rect in layout["alcas"].values():
                pygame.draw.rect(tela, COR_TEXTO, rect)
                pygame.draw.rect(tela, COR_OBSTACULO, rect, 1)

            pygame.draw.rect(
                tela,
                COR_DESTAQUE,
                layout["alca_visual"],
                border_radius=2,
            )

    visual = config_personagem["visual"]
    colisao = config_personagem["colisao"]

    legenda = fonte.render(
        f"Visual: {visual['largura']} x {visual['altura']}   |   "
        f"Colisão: {colisao['largura']} x {colisao['altura']}",
        True,
        COR_TEXTO,
    )

    tela.blit(
        legenda,
        legenda.get_rect(
            center=(layout["area"].centerx, layout["area"].bottom - 28)
        ),
    )


def obter_botao_visualizar_personagem():
    return pygame.Rect(
        tela.get_width() - LARGURA_PAINEL_DIREITO + 14,
        ALTURA_CABECALHO + 14,
        LARGURA_PAINEL_DIREITO - 28,
        38,
    )


def desenhar_painel_personagem():
    largura, altura = tela.get_size()

    esquerdo = pygame.Rect(
        0,
        ALTURA_CABECALHO,
        LARGURA_PAINEL_ESQUERDO,
        altura - ALTURA_CABECALHO - ALTURA_RODAPE,
    )

    direito = pygame.Rect(
        largura - LARGURA_PAINEL_DIREITO,
        ALTURA_CABECALHO,
        LARGURA_PAINEL_DIREITO,
        altura - ALTURA_CABECALHO - ALTURA_RODAPE,
    )

    pygame.draw.rect(tela, PAINEL, esquerdo)
    pygame.draw.rect(tela, PAINEL, direito)

    pygame.draw.line(
        tela, PAINEL_CLARO, esquerdo.topright, esquerdo.bottomright, 1
    )
    pygame.draw.line(
        tela, PAINEL_CLARO, direito.topleft, direito.bottomleft, 1
    )

    x = esquerdo.x + 14
    y = esquerdo.y + 18

    tela.blit(
        fonte.render("PERSONAGEM", True, COR_DESTAQUE),
        (x, y),
    )

    instrucoes = [
        "EDICAO COM MOUSE",
        "",
        "Dentro da caixa vermelha:",
        "arraste para mover.",
        "",
        "Nas alcas da caixa:",
        "arraste para redimensionar.",
        "",
        "Fora da caixa vermelha:",
        "arraste para desenhar",
        "uma nova colisao.",
        "",
        "Canto inferior direito:",
        "altere o tamanho visual.",
        "",
        "Botao direito na colisao:",
        "restaura o padrao.",
        "",
        "Salvamento automatico.",
    ]

    y += 42
    for linha in instrucoes:
        if linha:
            tela.blit(
                fonte_pequena.render(linha, True, COR_SECUNDARIA),
                (x + 2, y),
            )
        y += 21

    x = direito.x + 14

    botao = obter_botao_visualizar_personagem()
    pygame.draw.rect(
        tela,
        COR_DESTAQUE if visualizacao_personagem_ativa else PAINEL_CLARO,
        botao,
        border_radius=5,
    )
    pygame.draw.rect(tela, COR_DESTAQUE, botao, 1, border_radius=5)

    rotulo = (
        "VOLTAR AO PERSONAGEM"
        if visualizacao_personagem_ativa
        else "VISUALIZAR NO MAPA"
    )
    texto_botao = fonte_pequena.render(rotulo, True, COR_TEXTO)
    tela.blit(texto_botao, texto_botao.get_rect(center=botao.center))

    y = direito.y + 68
    tela.blit(
        fonte.render("DIMENSOES", True, COR_DESTAQUE),
        (x, y),
    )

    y += 42
    tela.blit(
        fonte_pequena.render("VISUAL", True, COR_SECUNDARIA),
        (x, y),
    )

    y += 27
    visual = config_personagem["visual"]

    for rotulo, valor in (
        ("Largura", visual["largura"]),
        ("Altura", visual["altura"]),
    ):
        tela.blit(
            fonte_pequena.render(rotulo, True, COR_SECUNDARIA),
            (x, y),
        )
        tela.blit(
            fonte.render(str(valor), True, COR_TEXTO),
            (x + 145, y - 3),
        )
        y += 29

    y += 12
    tela.blit(
        fonte_pequena.render("COLISAO", True, COR_SECUNDARIA),
        (x, y),
    )

    y += 27
    colisao = config_personagem["colisao"]

    propriedades = (
        ("Posicao X", colisao["x"]),
        ("Posicao Y", colisao["y"]),
        ("Largura", colisao["largura"]),
        ("Altura", colisao["altura"]),
    )

    for rotulo, valor in propriedades:
        tela.blit(
            fonte_pequena.render(rotulo, True, COR_SECUNDARIA),
            (x, y),
        )
        tela.blit(
            fonte.render(str(valor), True, COR_TEXTO),
            (x + 145, y - 3),
        )
        y += 29


def desenhar_cabecalho():
    largura_tela = tela.get_width()

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

    tela.blit(titulo, (16, 8))
    tela.blit(subtitulo, (16, 37))

    botoes = obter_botoes_modos()

    nomes = {
        identificador: nome
        for identificador, nome, _ in MODOS_EDITOR
    }

    for identificador, botao in botoes.items():
        ativo = modo == identificador

        fundo = PAINEL_CLARO if ativo else FUNDO
        borda = COR_DESTAQUE if ativo else PAINEL_CLARO
        texto_cor = COR_TEXTO if ativo else COR_SECUNDARIA

        pygame.draw.rect(
            tela, fundo, botao, border_radius=7
        )
        pygame.draw.rect(
            tela, borda, botao,
            width=1, border_radius=7
        )

        texto = fonte_pequena.render(
            nomes[identificador], True, texto_cor
        )
        tela.blit(
            texto,
            texto.get_rect(center=botao.center)
        )

    botao_voltar = pygame.Rect(
        largura_tela - 180, 10, 164, 44
    )

    pygame.draw.rect(
        tela, PAINEL_CLARO, botao_voltar,
        border_radius=7
    )
    pygame.draw.rect(
        tela, COR_DESTAQUE, botao_voltar,
        width=1, border_radius=7
    )

    texto_voltar = fonte_pequena.render(
        "< VOLTAR A CENTRAL", True, COR_TEXTO
    )
    tela.blit(
        texto_voltar,
        texto_voltar.get_rect(center=botao_voltar.center)
    )


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

            elif evento.key in (
                pygame.K_1, pygame.K_2,
                pygame.K_3, pygame.K_4, pygame.K_5
            ):
                tecla_modo = {
                    pygame.K_1: "mapa",
                    pygame.K_2: "interacao",
                    pygame.K_3: "sprite",
                    pygame.K_4: "recursos",
                    pygame.K_5: "personagem",
                }
                selecionar_modo(tecla_modo[evento.key])

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

            if modo == "recursos":
                lista = obter_lista_recursos()

                if lista.collidepoint(mouse):
                    altura_conteudo = (
                        len(itens_editor) * ALTURA_LINHA_RECURSO
                    )
                    limite = max(0, altura_conteudo - lista.height)

                    rolagem_itens = max(
                        0,
                        min(
                            limite,
                            rolagem_itens - evento.y * 3
                            * ALTURA_LINHA_RECURSO
                        )
                    )
                    continue

            if (
                mouse[0] < LARGURA_PAINEL_ESQUERDO
                or mouse[0] >= (
                    tela.get_width() - LARGURA_PAINEL_DIREITO
                )
                or mouse[1] < ALTURA_CABECALHO
                or mouse[1] >= tela.get_height() - ALTURA_RODAPE
            ):
                continue

            area, escala_atual = area_imagem()

            if area.collidepoint(mouse):

                altura_util = max(
                    100,
                    tela.get_height() - ALTURA_CABECALHO - ALTURA_RODAPE
                )

                margem_esquerda = LARGURA_PAINEL_ESQUERDO
                margem_direita = LARGURA_PAINEL_DIREITO

                largura_util = max(
                    100,
                    tela.get_width() - margem_esquerda - margem_direita
                )

                escala_base = min(
                    largura_util / IMG_LARGURA,
                    altura_util / IMG_ALTURA
                )

                zoom_isolado = (
                    modo == "recursos"
                    and not visualizacao_recurso_ativa
                )
                zoom_atual = zoom_recurso if zoom_isolado else zoom

                novo_zoom = max(
                    zoom_minimo,
                    min(zoom_maximo, zoom_atual * (1.15 ** evento.y))
                )

                if novo_zoom != zoom_atual:

                    if zoom_isolado:
                        zoom_recurso = novo_zoom
                        pan_x = 0.0
                        pan_y = 0.0
                    else:
                        mundo_x = (mouse[0] - area.x) / escala_atual
                        mundo_y = (mouse[1] - area.y) / escala_atual

                        zoom = novo_zoom
                        nova_escala = escala_base * zoom

                        pan_x = (
                            mouse[0] - mundo_x * nova_escala
                            - margem_esquerda
                            - (largura_util - IMG_LARGURA * nova_escala) / 2
                        )

                        pan_y = (
                            mouse[1] - mundo_y * nova_escala
                            - ALTURA_CABECALHO
                            - (
                                altura_util - IMG_ALTURA * nova_escala
                            ) / 2
                        )

        elif evento.type == pygame.MOUSEBUTTONDOWN:

            if evento.button == 2:
                if modo == "recursos" and not visualizacao_recurso_ativa:
                    continue

                area_atual, _ = area_imagem()
                if area_atual.collidepoint(evento.pos):
                    arrastando_camera = True
                    ultima_posicao_camera = evento.pos

            elif evento.button == 1:
                print(f"[DIAGNOSTICO] Clique esquerdo: {evento.pos}")

                aba_clicada = next(
                    (
                        identificador
                        for identificador, botao
                        in obter_botoes_modos().items()
                        if botao.collidepoint(evento.pos)
                    ),
                    None
                )

                if aba_clicada is not None:
                    selecionar_modo(aba_clicada)
                    continue

                botao_voltar = pygame.Rect(
                    tela.get_width() - 190, 12, 170, 48
                )

                if botao_voltar.collidepoint(evento.pos):
                    executando = False
                    continue

                if modo == "personagem":
                    if obter_botao_visualizar_personagem().collidepoint(evento.pos):
                        if not visualizacao_personagem_ativa:
                            finalizar_edicao_personagem()
                        visualizacao_personagem_ativa = not visualizacao_personagem_ativa
                        continue

                    if not visualizacao_personagem_ativa:
                        layout = obter_layout_previa_personagem()
                        if layout["area"].collidepoint(evento.pos):
                            iniciar_edicao_personagem(evento.pos)
                    continue

                if modo == "recursos":
                    if obter_lista_recursos().collidepoint(evento.pos):
                        selecionar_recurso_pelo_mouse(evento.pos)
                        continue

                    if obter_botao_visualizar_recurso().collidepoint(evento.pos):
                        visualizacao_recurso_ativa = not visualizacao_recurso_ativa
                        if visualizacao_recurso_ativa:
                            pan_x = 0.0
                            pan_y = 0.0
                        centro_previa_recurso = None
                        arrastando_previa_recurso = False
                        inicio_previa_recurso = None
                        fim_previa_recurso = None
                        continue

                    if evento.pos[0] >= tela.get_width() - LARGURA_PAINEL_DIREITO:
                        item = catalogo_editor.obter(item_selecionado_id)
                        if item is not None:
                            botoes = obter_botoes_recursos()
                            ferramenta_clicada = (
                                "colisao"
                                if botoes[("ferramenta", "colisao")].collidepoint(evento.pos)
                                else None
                            )
                            if ferramenta_clicada is not None:
                                ferramenta_recurso = ferramenta_clicada
                                centro_previa_recurso = None
                                arrastando_previa_recurso = False
                                inicio_previa_recurso = None
                                fim_previa_recurso = None
                                continue

                            acao_realizada = False
                            for (secao, propriedade), controles in botoes.items():
                                if secao in ("ferramenta", "config"):
                                    continue

                                for sinal, rect in controles.items():
                                    if rect.collidepoint(evento.pos):
                                        ajustar_propriedade_recurso(
                                            secao, propriedade, int(sinal)
                                        )
                                        acao_realizada = True
                                        break

                                if acao_realizada:
                                    break
                        continue

                    item = catalogo_editor.obter(item_selecionado_id)
                    layout = obter_layout_previa_recurso(
                        item,
                        evento.pos if visualizacao_recurso_ativa else None
                    )
                    sprite_previa = layout["sprite"]
                    area_mapa, _ = area_imagem()

                    if (
                        item is not None
                        and sprite_previa is not None
                        and sprite_previa.collidepoint(evento.pos)
                        and (
                            not visualizacao_recurso_ativa
                            or area_mapa.collidepoint(evento.pos)
                        )
                    ):
                        indice = encontrar_retangulo_recurso(
                            item, "colisao", evento.pos, sprite_previa
                        )

                        if indice is not None:
                            colisao_recurso_selecionada = indice
                        else:
                            colisao_recurso_selecionada = None
                            centro_previa_recurso = (
                                evento.pos if visualizacao_recurso_ativa else None
                            )
                            inicio_previa_recurso = ponto_previa_para_recurso(
                                evento.pos, item, sprite_previa
                            )
                            fim_previa_recurso = inicio_previa_recurso
                            arrastando_previa_recurso = True
                    continue

                # Cliques no painel direito nao devem atingir o mapa.
                if evento.pos[0] >= (
                    tela.get_width() - LARGURA_PAINEL_DIREITO
                ):
                    if modo == "sprite":
                        botoes_tamanho = obter_botoes_tamanho_sprite()

                        for propriedade, controles in botoes_tamanho.items():
                            if controles["menos"].collidepoint(evento.pos):
                                ajustar_tamanho_sprite(propriedade, -1)
                                break
                            if controles["mais"].collidepoint(evento.pos):
                                ajustar_tamanho_sprite(propriedade, 1)
                                break

                        botoes = obter_botoes_propriedades_sprite()
                        for propriedade, controles in botoes.items():
                            if controles["menos"].collidepoint(evento.pos):
                                ajustar_colisao_sprite(propriedade, -1)
                                break
                            if controles["mais"].collidepoint(evento.pos):
                                ajustar_colisao_sprite(propriedade, 1)
                                break

                    continue

                if (
                    evento.pos[0] < LARGURA_PAINEL_ESQUERDO
                    or evento.pos[0] >= (
                        tela.get_width() - LARGURA_PAINEL_DIREITO
                    )
                ):
                    continue

                ponto = mouse_para_imagem(evento.pos)

                if ponto is None:
                    continue

                if modo == "sprite":

                    instancia, camada = encontrar_sprite(ponto)

                    if instancia is None:
                        sprite_selecionado = None
                        instancia_selecionada = None
                        camada_sprite_selecionada = None
                        colisao_sprite_selecionada = None
                        continue

                    identificador = chave_sprite(instancia)

                    # Primeiro clique seleciona o tipo e sua camada.
                    if (
                        sprite_selecionado != identificador
                        or camada_sprite_selecionada != camada
                    ):
                        sprite_selecionado = identificador
                        instancia_selecionada = instancia
                        camada_sprite_selecionada = camada
                        colisao_sprite_selecionada = None
                        continue

                    instancia_selecionada = instancia

                    # Clique em uma colisão existente: seleciona.
                    indice = encontrar_colisao_sprite(
                        instancia, ponto, camada
                    )
                    if indice is not None:
                        colisao_sprite_selecionada = indice
                        continue

                    # Clique em área livre: inicia uma nova colisão.
                    colisao_sprite_selecionada = None
                    inicio = ponto_para_sprite(ponto, instancia, camada)
                    fim = inicio
                    arrastando = True

                else:
                    inicio = ponto
                    fim = ponto
                    arrastando = True

            elif evento.button == 3:
                if modo == "personagem":
                    if visualizacao_personagem_ativa:
                        continue
                    layout = obter_layout_previa_personagem()
                    if layout["colisao"].collidepoint(evento.pos):
                        config_personagem["colisao"] = dict(
                            CONFIG_PERSONAGEM_PADRAO["colisao"]
                        )
                        limitar_colisao_personagem()
                        salvar_config_personagem()
                    continue

                if modo == "recursos":
                    apagar_retangulo_recurso(evento.pos)
                else:
                    apagar_proximo(evento.pos)

        elif evento.type == pygame.MOUSEMOTION:

            if edicao_personagem is not None and modo == "personagem":
                atualizar_edicao_personagem(evento.pos)

            elif arrastando_camera:

                dx = evento.pos[0] - ultima_posicao_camera[0]
                dy = evento.pos[1] - ultima_posicao_camera[1]

                pan_x += dx
                pan_y += dy

                ultima_posicao_camera = evento.pos

            elif arrastando_previa_recurso and modo == "recursos":

                item = catalogo_editor.obter(item_selecionado_id)
                layout_previa = obter_layout_previa_recurso(item)

                if item is not None and layout_previa["sprite"] is not None:
                    fim_previa_recurso = ponto_previa_para_recurso(
                        evento.pos, item, layout_previa["sprite"]
                    )

            elif arrastando:

                ponto = mouse_para_imagem(evento.pos)

                if ponto is not None:

                    if modo == "sprite" and instancia_selecionada:
                        fim = ponto_para_sprite(
                            ponto,
                            instancia_selecionada
                        )
                    else:
                        fim = ponto

        elif evento.type == pygame.MOUSEBUTTONUP:

            if (
                evento.button == 1
                and edicao_personagem is not None
                and modo == "personagem"
            ):
                finalizar_edicao_personagem(evento.pos)

            elif evento.button == 2:
                arrastando_camera = False
                ultima_posicao_camera = None

            elif evento.button == 1 and arrastando_previa_recurso:

                item = catalogo_editor.obter(item_selecionado_id)
                layout_previa = obter_layout_previa_recurso(item)

                if item is not None and layout_previa["sprite"] is not None:
                    fim_previa_recurso = ponto_previa_para_recurso(
                        evento.pos, item, layout_previa["sprite"]
                    )
                    salvar_desenho_previa_recurso()

                arrastando_previa_recurso = False
                inicio_previa_recurso = None
                fim_previa_recurso = None
                centro_previa_recurso = None

            elif evento.button == 1 and arrastando:

                ponto = mouse_para_imagem(evento.pos)

                if ponto is not None:

                    if modo == "sprite" and instancia_selecionada:
                        fim = ponto_para_sprite(
                            ponto,
                            instancia_selecionada
                        )
                    else:
                        fim = ponto

                if inicio is not None and fim is not None:

                    novo = retangulo_arrastado(inicio, fim)

                    if novo.width >= 3 and novo.height >= 3:
                        print(f"[DIAGNOSTICO] Retangulo: {novo}")
                        print(f"[DIAGNOSTICO] Modo: {modo}")

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
    # O mapa fica oculto durante a visualizacao isolada do recurso.
    if (
        modo not in ("recursos", "personagem")
        or (modo == "recursos" and visualizacao_recurso_ativa)
        or (modo == "personagem" and visualizacao_personagem_ativa)
    ):
        tela.fill(FUNDO)

        area, escala = area_imagem()

        imagem = pygame.transform.scale(
            imagem_original,
            (area.width, area.height)
        )

        tela.blit(imagem, area.topleft)

        # Sprites do mapa
        desenhar_sprites_terreno(area, escala)
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
                fator = ESCALA_SPRITES_JOGO

                visual = pygame.Rect(
                    area.x + round(
                        (instancia_selecionada["x"] + r.x * fator) * escala
                    ),
                    area.y + round(
                        (instancia_selecionada["y"] + r.y * fator) * escala
                    ),
                    max(1, round(r.width * fator * escala)),
                    max(1, round(r.height * fator * escala))
                )
            else:
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

    else:
        tela.fill((0, 0, 0) if modo == "personagem" else FUNDO)

    # ======================================================

    if modo == "recursos":
        desenhar_previa_recurso_central()
    elif modo == "personagem":
        desenhar_previa_personagem()

    # PAINEIS LATERAIS E CABECALHO
    # ======================================================

    if modo == "recursos":
        desenhar_painel_recursos()
    elif modo == "personagem":
        desenhar_painel_personagem()
    else:
        desenhar_paineis_contextuais()

    desenhar_cabecalho()

    largura_tela, altura_tela = tela.get_size()

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

    pygame.display.flip()

pygame.quit()

