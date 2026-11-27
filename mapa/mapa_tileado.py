
import json
import pygame

from mapa.tile import Tile


class MapaTileado:
    def __init__(self, caminho):
        self.caminho = caminho

        self.tile_size = 32
        self.largura = 0
        self.altura = 0

        self.tiles = {}
        self.camadas = {}
        self.areas_interacao = []
        self.retangulos_interacao = []

        self.carregar()

    def carregar(self):
        with open(self.caminho, "r", encoding="utf-8-sig") as arquivo:
            dados = json.load(arquivo)

        self.tile_size = dados["tile_size"]
        self.largura = dados["largura"]
        self.altura = dados["altura"]

        self.tiles = {
            identificador: Tile(
                identificador,
                informacoes["cor"],
                informacoes.get("solido", False)
            )
            for identificador, informacoes
            in dados["tiles"].items()
        }

        self.camadas = dados["camadas"]
        self.areas_interacao = dados.get("areas_interacao", [])

        self._validar()

    def _validar(self):
        if self.tile_size != 32:
            raise ValueError("O tamanho dos tiles deve ser 32x32.")

        if self.largura <= 0 or self.altura <= 0:
            raise ValueError("As dimensÃµes do mapa devem ser positivas.")

        ids_interacao = set()
        self.retangulos_interacao = []

        for area in self.areas_interacao:
            campos = ("id", "tipo", "x", "y", "largura", "altura")

            if not all(campo in area for campo in campos):
                raise ValueError("?rea de intera??o com campos ausentes.")

            identificador = area["id"]

            if not isinstance(identificador, str) or not identificador:
                raise ValueError("ID de intera??o inv?lido.")

            if identificador in ids_interacao:
                raise ValueError(f"ID de intera??o duplicado: {identificador}")

            ids_interacao.add(identificador)

            if not isinstance(area["tipo"], str) or not area["tipo"]:
                raise ValueError(f"Tipo inv?lido na ?rea: {identificador}")

            x = area["x"]
            y = area["y"]
            largura = area["largura"]
            altura = area["altura"]

            valores = (x, y, largura, altura)

            if any(type(valor) is not int for valor in valores):
                raise ValueError(f"Coordenadas inv?lidas na ?rea: {identificador}")

            if largura <= 0 or altura <= 0:
                raise ValueError(f"Dimens?es inv?lidas na ?rea: {identificador}")

            if (
                x < 0
                or y < 0
                or x + largura > self.largura * self.tile_size
                or y + altura > self.altura * self.tile_size
            ):
                raise ValueError(f"?rea fora dos limites do mapa: {identificador}")

            self.retangulos_interacao.append({
                "id": identificador,
                "tipo": area["tipo"],
                "rect": pygame.Rect(x, y, largura, altura)
            })

        for nome, grade in self.camadas.items():
            if len(grade) != self.altura:
                raise ValueError(
                    f"A camada '{nome}' possui altura invÃ¡lida."
                )

            for linha in grade:
                if len(linha) != self.largura:
                    raise ValueError(
                        f"A camada '{nome}' possui largura invÃ¡lida."
                    )

                for identificador in linha:
                    if identificador is not None and identificador not in self.tiles:
                        raise ValueError(
                            f"Tile inexistente: {identificador}"
                        )

    def desenhar(self, tela, camera=None):
        # Define a área visível do mundo.
        if camera is None:
            inicio_x = 0
            inicio_y = 0
            fim_x = self.largura
            fim_y = self.altura
            offset_x = 0
            offset_y = 0
        else:
            inicio_x = max(0, camera.x // self.tile_size)
            inicio_y = max(0, camera.y // self.tile_size)

            fim_x = min(
                self.largura,
                (camera.x + camera.largura_tela + self.tile_size - 1)
                // self.tile_size
            )

            fim_y = min(
                self.altura,
                (camera.y + camera.altura_tela + self.tile_size - 1)
                // self.tile_size
            )

            offset_x = camera.x
            offset_y = camera.y

        # Desenha as camadas na ordem definida no JSON.
        for grade in self.camadas.values():
            for y in range(inicio_y, fim_y):
                for x in range(inicio_x, fim_x):
                    identificador = grade[y][x]

                    if identificador is None:
                        continue

                    tile = self.tiles[identificador]

                    tile.desenhar(
                        tela,
                        x * self.tile_size - offset_x,
                        y * self.tile_size - offset_y,
                        self.tile_size
                    )

    def colide_com_obstaculo(self, rect):
        # Hitboxes inválidas não geram colisão.
        if rect.width <= 0 or rect.height <= 0:
            return False

        largura_mundo = self.largura * self.tile_size
        altura_mundo = self.altura * self.tile_size

        # Impede que a hitbox ultrapasse os limites do mapa.
        if (
            rect.left < 0
            or rect.top < 0
            or rect.right > largura_mundo
            or rect.bottom > altura_mundo
        ):
            return True

        # Identifica os tiles ocupados pela hitbox.
        inicio_x = rect.left // self.tile_size
        inicio_y = rect.top // self.tile_size

        fim_x = (rect.right - 1) // self.tile_size
        fim_y = (rect.bottom - 1) // self.tile_size

        # Verifica todas as camadas do mapa.
        for grade in self.camadas.values():
            for y in range(inicio_y, fim_y + 1):
                for x in range(inicio_x, fim_x + 1):
                    identificador = grade[y][x]

                    if identificador is None:
                        continue

                    tile = self.tiles[identificador]

                    if tile.solido:
                        return True

        return False
