
import json
import os
import pygame

pygame.init()

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CAMINHO_IMAGEM = os.path.join(
    RAIZ, "assets", "mapas", "mapaPrincipal.png"
)

CAMINHO_COLISOES = os.path.join(
    RAIZ, "mapa", "colisoes.json"
)

if not os.path.isfile(CAMINHO_IMAGEM):
    raise FileNotFoundError(CAMINHO_IMAGEM)

tela = pygame.display.set_mode((1024, 576), pygame.RESIZABLE)
pygame.display.set_caption("SimpSmith - Editor de Mapa")

imagem_original = pygame.image.load(CAMINHO_IMAGEM).convert()
IMG_LARGURA, IMG_ALTURA = imagem_original.get_size()

relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("arial", 17)
fonte_pequena = pygame.font.SysFont("arial", 14)

COR_OBSTACULO = (255, 40, 40)
COR_INTERACAO = (30, 150, 255)
COR_SELECAO = (255, 230, 0)
COR_TEXTO = (255, 255, 255)

mostrar_bordas = True
modo = "obstaculos"

arrastando = False
inicio = None
fim = None

obstaculos = []
areas_interacao = []

# ==========================================================
# CARREGAR DADOS
# ==========================================================

if os.path.isfile(CAMINHO_COLISOES):
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

    areas_interacao = dados.get("areas_interacao", [])


# ==========================================================
# SALVAR
# ==========================================================

def salvar():
    dados = {
        "largura_imagem": IMG_LARGURA,
        "altura_imagem": IMG_ALTURA,
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

    print("Mapa salvo com sucesso!")


# ==========================================================
# CONVERSÕES DE COORDENADAS
# ==========================================================

def area_imagem():
    largura, altura = tela.get_size()

    escala = min(
        largura / IMG_LARGURA,
        altura / IMG_ALTURA
    )

    w = round(IMG_LARGURA * escala)
    h = round(IMG_ALTURA * escala)

    x = (largura - w) // 2
    y = (altura - h) // 2

    return pygame.Rect(x, y, w, h), escala


def mouse_para_imagem(pos):
    area, escala = area_imagem()

    if not area.collidepoint(pos):
        return None

    x = round((pos[0] - area.x) / escala)
    y = round((pos[1] - area.y) / escala)

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
# EXCLUSÃO
# ==========================================================

def apagar_proximo(pos):
    ponto = mouse_para_imagem(pos)

    if ponto is None:
        return

    px, py = ponto

    if modo == "obstaculos":
        for i in range(len(obstaculos) - 1, -1, -1):
            if obstaculos[i].collidepoint(px, py):
                del obstaculos[i]
                salvar()
                return

    else:
        for i in range(len(areas_interacao) - 1, -1, -1):
            area = areas_interacao[i]

            rect = pygame.Rect(
                area["x"],
                area["y"],
                area["largura"],
                area["altura"]
            )

            if rect.collidepoint(px, py):
                del areas_interacao[i]
                salvar()
                return


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
                modo = "obstaculos"

            elif evento.key == pygame.K_2:
                modo = "interacao"

            elif evento.key == pygame.K_b:
                mostrar_bordas = not mostrar_bordas

            elif evento.key == pygame.K_s and (
                pygame.key.get_mods() & pygame.KMOD_CTRL
            ):
                salvar()

        elif evento.type == pygame.MOUSEBUTTONDOWN:

            if evento.button == 1:
                ponto = mouse_para_imagem(evento.pos)

                if ponto is not None:
                    inicio = ponto
                    fim = ponto
                    arrastando = True

            elif evento.button == 3:
                apagar_proximo(evento.pos)

        elif evento.type == pygame.MOUSEMOTION:
            if arrastando:
                ponto = mouse_para_imagem(evento.pos)

                if ponto is not None:
                    fim = ponto

        elif evento.type == pygame.MOUSEBUTTONUP:
            if evento.button == 1 and arrastando:

                ponto = mouse_para_imagem(evento.pos)

                if ponto is not None:
                    fim = ponto

                if inicio is not None and fim is not None:
                    novo = retangulo_arrastado(inicio, fim)

                    if novo.width >= 3 and novo.height >= 3:

                        if modo == "obstaculos":
                            obstaculos.append(novo)

                        else:
                            numero = len(areas_interacao) + 1

                            areas_interacao.append({
                                "id": f"area_{numero}",
                                "x": novo.x,
                                "y": novo.y,
                                "largura": novo.width,
                                "altura": novo.height,
                                "tipo": "crafting"
                            })

                        salvar()

                arrastando = False
                inicio = None
                fim = None

    # ======================================================
    # DESENHO
    # ======================================================

    tela.fill((35, 35, 35))

    area, escala = area_imagem()

    imagem = pygame.transform.scale(
        imagem_original,
        (area.width, area.height)
    )

    tela.blit(imagem, area.topleft)

    if mostrar_bordas:

        # Obstáculos
        for indice, obstaculo in enumerate(obstaculos):

            visual = pygame.Rect(
                area.x + round(obstaculo.x * escala),
                area.y + round(obstaculo.y * escala),
                max(1, round(obstaculo.width * escala)),
                max(1, round(obstaculo.height * escala))
            )

            pygame.draw.rect(tela, COR_OBSTACULO, visual, 2)

        # Áreas de interação
        for indice, item in enumerate(areas_interacao):

            visual = pygame.Rect(
                area.x + round(item["x"] * escala),
                area.y + round(item["y"] * escala),
                max(1, round(item["largura"] * escala)),
                max(1, round(item["altura"] * escala))
            )

            pygame.draw.rect(tela, COR_INTERACAO, visual, 2)

            numero = fonte_pequena.render(
                item["id"],
                True,
                COR_TEXTO
            )

            tela.blit(numero, (visual.x + 2, visual.y + 2))

    # Retângulo em criação
    if arrastando and inicio is not None and fim is not None:

        r = retangulo_arrastado(inicio, fim)

        visual = pygame.Rect(
            area.x + round(r.x * escala),
            area.y + round(r.y * escala),
            max(1, round(r.width * escala)),
            max(1, round(r.height * escala))
        )

        cor = COR_OBSTACULO if modo == "obstaculos" else COR_INTERACAO

        pygame.draw.rect(tela, cor, visual, 2)

    # Barra de instruções
    pygame.draw.rect(
        tela,
        (25, 25, 25),
        (0, 0, tela.get_width(), 32)
    )

    nome_modo = (
        "OBSTACULOS" if modo == "obstaculos"
        else "AREAS DE INTERACAO"
    )

    instrucoes = (
        f"1: Obstaculos | 2: Areas | "
        f"Modo: {nome_modo} | "
        f"Esquerdo: criar | Direito: apagar | "
        f"B: bordas | Ctrl+S: salvar | ESC: sair"
    )

    texto = fonte.render(instrucoes, True, COR_TEXTO)
    tela.blit(texto, (8, 7))

    pygame.display.flip()

pygame.quit()
