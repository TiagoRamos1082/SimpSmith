
import json
import os
import sys
import pygame

pygame.init()

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from sistemas.catalogo_itens import CatalogoItens

CAMINHO_IMAGEM = os.path.join(RAIZ, "assets", "mapas", "mapaPrincipal.png")
CAMINHO_AREAS = os.path.join(RAIZ, "mapa", "areas_minerios.json")

if not os.path.isfile(CAMINHO_IMAGEM):
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

imagem_original = pygame.image.load(CAMINHO_IMAGEM).convert()
IMG_LARGURA, IMG_ALTURA = imagem_original.get_size()

relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("arial", 16)
fonte_pequena = pygame.font.SysFont("arial", 13)

COR_TEXTO = (255, 255, 255)
COR_FUNDO = (25, 25, 25)
COR_SELECAO = (0, 255, 255)

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

        for item in dados.get("areas", []):
            tipo = item["tipo"]

            if tipo not in RECURSOS:
                raise ValueError(
                    f"O tipo '{tipo}' das Ã¡reas nÃ£o existe no catÃ¡logo "
                    "como recurso (minerio ou planta). "
                    "Cadastre-o em dados/itens.json ou corrija a Ã¡rea."
                )

            x = int(item["x"])
            y = int(item["y"])
            largura = int(item["largura"])
            altura = int(item["altura"])
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


def area_imagem():
    largura, altura = tela.get_size()

    escala_x = largura / IMG_LARGURA
    escala_y = altura / IMG_ALTURA

    return pygame.Rect(0, 0, largura, altura), escala_x, escala_y

def mouse_para_imagem(pos):
    area, escala_x, escala_y = area_imagem()

    if escala_x <= 0 or escala_y <= 0 or not area.collidepoint(pos):
        return None

    x = round(pos[0] / escala_x)
    y = round(pos[1] / escala_y)

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
        abs(y2 - y1),
    )


def area_para_tela(retangulo, area, escala_x, escala_y):
    return pygame.Rect(
        area.x + round(retangulo.x * escala_x),
        area.y + round(retangulo.y * escala_y),
        max(1, round(retangulo.width * escala_x)),
        max(1, round(retangulo.height * escala_y)),
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

        elif evento.type == pygame.MOUSEMOTION and arrastando:
            ponto = mouse_para_imagem(evento.pos)

            if ponto is not None:
                fim = ponto

        elif evento.type == pygame.MOUSEBUTTONUP:
            if evento.button == 1 and arrastando:
                ponto = mouse_para_imagem(evento.pos)

                if ponto is not None:
                    fim = ponto

                if inicio is not None and fim is not None:
                    criar_area(retangulo_arrastado(inicio, fim))

                arrastando = False
                inicio = None
                fim = None

    tela.fill((35, 35, 35))

    area, escala_x, escala_y = area_imagem()
    imagem = pygame.transform.scale(
        imagem_original,
        (area.width, area.height),
    )

    tela.blit(imagem, area.topleft)

    for indice, item in enumerate(areas):
        rect = obter_rect(item)
        visual = area_para_tela(rect, area, escala_x, escala_y)
        cor = RECURSOS[item["tipo"]]["cor"]

        if mostrar_bordas:
            pygame.draw.rect(tela, cor, visual, 2)

            desenhar_texto(
                f"{indice + 1}: {RECURSOS[item['tipo']]['nome']}",
                visual.x + 3,
                visual.y + 3,
                cor,
            )

        if indice == area_selecionada:
            pygame.draw.rect(tela, COR_SELECAO, visual, 3)

    if arrastando and inicio is not None and fim is not None:
        rect = retangulo_arrastado(inicio, fim)
        visual = area_para_tela(rect, area, escala_x, escala_y)

        pygame.draw.rect(
            tela,
            RECURSOS[tipo_atual]["cor"],
            visual,
            2,
        )

    pygame.draw.rect(
        tela,
        COR_FUNDO,
        (0, 0, tela.get_width(), 112),
    )

    desenhar_texto(
        "ESQUERDO: desenhar/selecionar | DIREITO: remover | "
        "B: bordas | CTRL+S: salvar | ESC: sair",
        8, 5, pequena=True,
    )

    legendas = []

    for indice, tipo in enumerate(tipos_disponiveis[:9]):
        legendas.append(f"{indice + 1}: {RECURSOS[tipo]['nome']}")

    desenhar_texto(
        "Recursos: " + " | ".join(legendas) + " | TAB: prÃ³ximo recurso",
        8, 26, pequena=True,
    )

    desenhar_texto(
        "Setas cima/baixo: limite | Esquerda/direita: respawn | "
        "PageUp/PageDown: inicial | Delete: remover",
        8, 46, pequena=True,
    )

    if area_selecionada is not None:
        item = areas[area_selecionada]
        nome = RECURSOS[item["tipo"]]["nome"]

        desenhar_texto(
            f"Selecionada: {nome} | MÃ¡ximo: {item['maximo']} | "
            f"Inicial: {item['inicial']} | Respawn: {item['respawn']:.0f}s",
            8, 68, pequena=True,
        )

    else:
        desenhar_texto(
            f"Tipo atual: {RECURSOS[tipo_atual]['nome']} | "
            f"Ãreas: {len(areas)}",
            8, 68, pequena=True,
        )

    if pygame.time.get_ticks() < tempo_mensagem:
        largura_texto = fonte.size(mensagem)[0] + 20

        pygame.draw.rect(
            tela,
            COR_FUNDO,
            (8, tela.get_height() - 32, largura_texto, 26),
        )

        desenhar_texto(
            mensagem,
            16,
            tela.get_height() - 28,
        )

    pygame.display.flip()

pygame.quit()


