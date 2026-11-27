
from pathlib import Path
import shutil
import py_compile
import sys

RAIZ = Path(__file__).resolve().parent

ARQUIVOS = [
    RAIZ / "editores" / "mapas" / "editor_colisoes.py",
    RAIZ / "editores" / "mapas" / "editor_mapa.py",
    RAIZ / "editores" / "tiles" / "editor_sprites.py",
]

BACKUP = RAIZ / "backups_camera"
originais = {}

def substituir(conteudo, antigo, novo, arquivo):
    quantidade = conteudo.count(antigo)
    if quantidade != 1:
        raise RuntimeError(
            f"{arquivo.name}: trecho esperado encontrado {quantidade} vezes."
        )
    return conteudo.replace(antigo, novo, 1)


def atualizar_colisoes(c):
    # Estado da câmera
    c = substituir(
        c,
        'mostrar_bordas = True\nmodo = "obstaculos"',
        '''mostrar_bordas = True
modo = "obstaculos"

zoom = 1.0
zoom_minimo = 0.25
zoom_maximo = 5.0
pan_x = 0.0
pan_y = 0.0
arrastando_camera = False
ultima_posicao_camera = None''',
        ARQUIVOS[0]
    )

    # Conversão de coordenadas e enquadramento
    inicio = c.index("def area_imagem():")
    fim = c.index("\n\ndef retangulo_arrastado", inicio)

    c = c[:inicio] + '''def area_imagem():
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

    x = round((pos[0] - area.x) / escala)
    y = round((pos[1] - area.y) / escala)

    x = max(0, min(IMG_LARGURA - 1, x))
    y = max(0, min(IMG_ALTURA - 1, y))

    return x, y
''' + c[fim:]

    # Eventos de câmera
    c = substituir(
        c,
        '''        elif evento.type == pygame.MOUSEBUTTONDOWN:

            if evento.button == 1:''',
        '''        elif evento.type == pygame.MOUSEWHEEL:
            mouse = pygame.mouse.get_pos()
            area, escala_atual = area_imagem()

            escala_base = min(
                tela.get_width() / IMG_LARGURA,
                tela.get_height() / IMG_ALTURA
            )

            zoom_anterior = zoom
            novo_zoom = max(
                zoom_minimo,
                min(zoom_maximo, zoom * (1.15 ** evento.y))
            )

            if novo_zoom != zoom_anterior:
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

            elif evento.button == 1:''',
        ARQUIVOS[0]
    )

    c = substituir(
        c,
        '''        elif evento.type == pygame.MOUSEMOTION:
            if arrastando:''',
        '''        elif evento.type == pygame.MOUSEMOTION:
            if arrastando_camera:
                dx = evento.pos[0] - ultima_posicao_camera[0]
                dy = evento.pos[1] - ultima_posicao_camera[1]
                pan_x += dx
                pan_y += dy
                ultima_posicao_camera = evento.pos

            elif arrastando:''',
        ARQUIVOS[0]
    )

    c = substituir(
        c,
        '''        elif evento.type == pygame.MOUSEBUTTONUP:
            if evento.button == 1 and arrastando:''',
        '''        elif evento.type == pygame.MOUSEBUTTONUP:
            if evento.button == 2:
                arrastando_camera = False
                ultima_posicao_camera = None

            elif evento.button == 1 and arrastando:''',
        ARQUIVOS[0]
    )

    return c


def atualizar_mapa(c):
    c = substituir(
        c,
        '''        self.painel_x = self.largura_janela - self.painel_largura''',
        '''        self.painel_x = self.largura_janela - self.painel_largura

        self.zoom_minimo = 1
        self.zoom_maximo = 40
        self.arrastando_camera = False
        self.ultima_posicao_camera = None''',
        ARQUIVOS[1]
    )

    # Zoom ancorado no cursor
    c = substituir(
        c,
        '''            elif evento.type == pygame.MOUSEWHEEL:
                if (
                    self.modo == "sprites"
                    and pygame.mouse.get_pos()[0] >= self.painel_x
                ):
                    self.sprite_scroll = max(
                        0,
                        min(
                            max(0, len(self.sprites) - 4),
                            self.sprite_scroll - evento.y
                        )
                    )''',
        '''            elif evento.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                if mouse_x >= self.painel_x:
                    if self.modo == "sprites":
                        self.sprite_scroll = max(
                            0,
                            min(
                                max(0, len(self.sprites) - 4),
                                self.sprite_scroll - evento.y
                            )
                        )

                else:
                    zoom_anterior = self.escala
                    novo_zoom = max(
                        self.zoom_minimo,
                        min(self.zoom_maximo,
                            round(self.escala * (1.15 ** evento.y)))
                    )

                    if novo_zoom != zoom_anterior:
                        fator = novo_zoom / zoom_anterior

                        self.posicao_mapa_x = round(
                            mouse_x - (mouse_x - self.posicao_mapa_x) * fator
                        )
                        self.posicao_mapa_y = round(
                            mouse_y - (mouse_y - self.posicao_mapa_y) * fator
                        )
                        self.escala = novo_zoom''',
        ARQUIVOS[1]
    )

    c = substituir(
        c,
        '''            elif evento.type == pygame.MOUSEBUTTONDOWN:

                if evento.button == 1:''',
        '''            elif evento.type == pygame.MOUSEBUTTONDOWN:

                if evento.button == 2:
                    self.arrastando_camera = True
                    self.ultima_posicao_camera = evento.pos

                elif evento.button == 1:''',
        ARQUIVOS[1]
    )

    c = substituir(
        c,
        '''            elif evento.type == pygame.MOUSEMOTION:

                if pygame.mouse.get_pressed()[0]:''',
        '''            elif evento.type == pygame.MOUSEMOTION:

                if self.arrastando_camera:
                    dx = evento.pos[0] - self.ultima_posicao_camera[0]
                    dy = evento.pos[1] - self.ultima_posicao_camera[1]

                    self.posicao_mapa_x += dx
                    self.posicao_mapa_y += dy
                    self.ultima_posicao_camera = evento.pos

                elif pygame.mouse.get_pressed()[0]:''',
        ARQUIVOS[1]
    )

    c = substituir(
        c,
        '''            elif evento.type == pygame.MOUSEMOTION:''',
        '''            elif evento.type == pygame.MOUSEMOTION:''',
        ARQUIVOS[1]
    )

    # Finalização do pan pelo botão do meio
    c = substituir(
        c,
        '''            elif evento.type == pygame.MOUSEMOTION:

                if self.arrastando_camera:''',
        '''            elif evento.type == pygame.MOUSEBUTTONUP:
                if evento.button == 2:
                    self.arrastando_camera = False
                    self.ultima_posicao_camera = None

            elif evento.type == pygame.MOUSEMOTION:

                if self.arrastando_camera:''',
        ARQUIVOS[1]
    )

    return c


def atualizar_sprites(c):
    # Câmera e viewport independente do painel
    c = substituir(
        c,
        '''        self.origem_x = 20
        self.origem_y = 65''',
        '''        self.origem_x = 20
        self.origem_y = 65

        self.zoom_minimo = 0.25
        self.zoom_maximo = 5.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.arrastando_camera = False
        self.ultima_posicao_camera = None

        self.largura_painel = 250
        self.limite_visual = self.largura - self.largura_painel - 35''',
        ARQUIVOS[2]
    )

    c = substituir(
        c,
        '''        x = (mx - self.origem_x) / (TAMANHO_CELULA * self.escala)
        y = (my - self.origem_y) / (TAMANHO_CELULA * self.escala)''',
        '''        if mx >= self.largura - self.largura_painel:
            return None

        x = (
            mx - self.origem_x - self.pan_x
        ) / (TAMANHO_CELULA * self.escala)

        y = (
            my - self.origem_y - self.pan_y
        ) / (TAMANHO_CELULA * self.escala)''',
        ARQUIVOS[2]
    )

    c = substituir(
        c,
        '''            px = self.origem_x + int(x * tamanho)''',
        '''            px = self.origem_x + round(self.pan_x) + int(x * tamanho)''',
        ARQUIVOS[2]
    )

    c = substituir(
        c,
        '''                (px, self.origem_y),
                (px, self.origem_y + self.visual_altura)''',
        '''                (px, self.origem_y + round(self.pan_y)),
                (px, self.origem_y + round(self.pan_y) + self.visual_altura)''',
        ARQUIVOS[2]
    )

    c = substituir(
        c,
        '''            py = self.origem_y + int(y * tamanho)''',
        '''            py = self.origem_y + round(self.pan_y) + int(y * tamanho)''',
        ARQUIVOS[2]
    )

    c = substituir(
        c,
        '''                (self.origem_x, py),
                (self.origem_x + self.visual_largura, py)''',
        '''                (self.origem_x + round(self.pan_x), py),
                (self.origem_x + round(self.pan_x) + self.visual_largura, py)''',
        ARQUIVOS[2]
    )

    c = substituir(
        c,
        '''            self.origem_x + int(x1 * tamanho),
            self.origem_y + int(y1 * tamanho),''',
        '''            self.origem_x + round(self.pan_x) + int(x1 * tamanho),
            self.origem_y + round(self.pan_y) + int(y1 * tamanho),''',
        ARQUIVOS[2]
    )

    c = substituir(
        c,
        '''        painel_x = self.origem_x + self.visual_largura + 25''',
        '''        painel_x = self.largura - self.largura_painel''',
        ARQUIVOS[2]
    )

    c = substituir(
        c,
        '''            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:''',
        '''            elif evento.type == pygame.MOUSEWHEEL:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                if mouse_x < self.largura - self.largura_painel:
                    zoom_anterior = self.escala
                    novo_zoom = max(
                        self.zoom_minimo,
                        min(self.zoom_maximo,
                            self.escala * (1.15 ** evento.y))
                    )

                    fator = novo_zoom / zoom_anterior

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

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 2:
                    self.arrastando_camera = True
                    self.ultima_posicao_camera = evento.pos

                elif evento.button == 1:''',
        ARQUIVOS[2]
    )

    c = substituir(
        c,
        '''            elif evento.type == pygame.MOUSEMOTION:
                if self.selecionando:''',
        '''            elif evento.type == pygame.MOUSEMOTION:
                if self.arrastando_camera:
                    dx = evento.pos[0] - self.ultima_posicao_camera[0]
                    dy = evento.pos[1] - self.ultima_posicao_camera[1]
                    self.pan_x += dx
                    self.pan_y += dy
                    self.ultima_posicao_camera = evento.pos

                elif self.selecionando:''',
        ARQUIVOS[2]
    )

    c = substituir(
        c,
        '''            elif evento.type == pygame.MOUSEBUTTONUP:
                if evento.button == 1:
                    self.selecionando = False''',
        '''            elif evento.type == pygame.MOUSEBUTTONUP:
                if evento.button == 2:
                    self.arrastando_camera = False
                    self.ultima_posicao_camera = None

                elif evento.button == 1:
                    self.selecionando = False''',
        ARQUIVOS[2]
    )

    c = substituir(
        c,
        '''                (self.origem_x, self.origem_y)
            )''',
        '''                (
                    self.origem_x + round(self.pan_x),
                    self.origem_y + round(self.pan_y)
                )
            )''',
        ARQUIVOS[2]
    )

    return c


def main():
    BACKUP.mkdir(exist_ok=True)

    for arquivo in ARQUIVOS:
        if not arquivo.is_file():
            raise FileNotFoundError(arquivo)

        originais[arquivo] = arquivo.read_text(encoding="utf-8")

    try:
        atualizados = [
            atualizar_colisoes(originais[ARQUIVOS[0]]),
            atualizar_mapa(originais[ARQUIVOS[1]]),
            atualizar_sprites(originais[ARQUIVOS[2]]),
        ]

        for arquivo, conteudo in zip(ARQUIVOS, originais.values()):
            destino = BACKUP / arquivo.name
            shutil.copy2(arquivo, destino)

        for arquivo, conteudo in zip(ARQUIVOS, atualizados):
            arquivo.write_text(conteudo, encoding="utf-8")

        for arquivo in ARQUIVOS:
            py_compile.compile(str(arquivo), doraise=True)

        print("\nAtualização aplicada e sintaxe validada!")
        print(f"Backups disponíveis em: {BACKUP}")

    except Exception as erro:
        print(f"\nFalha: {erro}")
        print("Restaurando arquivos originais...")

        for arquivo, conteudo in originais.items():
            arquivo.write_text(conteudo, encoding="utf-8")

        print("Restauração concluída.")
        sys.exit(1)


if __name__ == "__main__":
    main()
