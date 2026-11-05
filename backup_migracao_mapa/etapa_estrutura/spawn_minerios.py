import json
import os
import random
import pygame

from objetos.recurso import Recurso
from sistemas.catalogo_itens import CatalogoItens


class SpawnMinerios:
    TAMANHO_MINERIO = 32
    TENTATIVAS_SPAWN = 30

    def __init__(self, mapa):
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.caminho_areas = os.path.join(raiz, "mapa", "areas_minerios.json")
        self.catalogo = CatalogoItens()
        self.mapa = mapa
        self.areas = []
        self.minerios = []
        self.tempos_respawn = []
        self.inicializado = False
        self._carregar_areas()

    def _carregar_areas(self):
        if not os.path.isfile(self.caminho_areas):
            raise FileNotFoundError(f"Arquivo de áreas não encontrado: {self.caminho_areas}")

        with open(self.caminho_areas, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        self.areas = dados.get("areas", [])

        for area in self.areas:
            item = self.catalogo.obter(area["tipo"])
            if item is None or item["categoria"] not in {"minerio", "planta"}:
                raise ValueError(
                    f"'{area['tipo']}' não existe no catálogo como recurso (minerio ou planta). "
                    "Confira dados/itens.json e mapa/areas_minerios.json."
                )

            if area["largura"] < self.TAMANHO_MINERIO:
                raise ValueError("Área muito estreita para um minério.")
            if area["altura"] < self.TAMANHO_MINERIO:
                raise ValueError("Área muito baixa para um minério.")

            maximo = int(area.get("maximo", 3))
            inicial = int(area.get("inicial", min(3, maximo)))
            respawn = float(area.get("respawn", 20.0))

            if maximo < 1 or not 0 <= inicial <= maximo:
                raise ValueError("Configuração de quantidade inválida.")
            if respawn <= 0:
                raise ValueError("O tempo de respawn deve ser maior que zero.")

            area["_maximo"] = maximo
            area["_inicial"] = inicial
            area["_respawn"] = respawn
            area["_pode_respawn"] = bool(item.get("respawn", True))

        self.tempos_respawn = [0.0] * len(self.areas)

    def atualizar(self, dt, jogador):
        if not self.inicializado:
            for indice, area in enumerate(self.areas):
                for _ in range(area["_inicial"]):
                    minerio = self._criar_minerio(indice, jogador)
                    if minerio is None:
                        break
                    self.minerios.append(minerio)
            self.inicializado = True
            return

        for indice, area in enumerate(self.areas):
            if not area["_pode_respawn"]:
                continue

            existentes = self._minerios_da_area(indice)
            if len(existentes) < area["_maximo"]:
                self.tempos_respawn[indice] += dt
                if self.tempos_respawn[indice] >= area["_respawn"]:
                    minerio = self._criar_minerio(indice, jogador)
                    if minerio is not None:
                        self.minerios.append(minerio)
                        self.tempos_respawn[indice] = 0.0
            else:
                self.tempos_respawn[indice] = 0.0

    def _area_na_tela(self, area):
        tela = pygame.display.get_surface()
        sx = tela.get_width() / self.mapa.largura_referencia
        sy = tela.get_height() / self.mapa.altura_referencia
        return pygame.Rect(
            round(area["x"] * sx),
            round(area["y"] * sy),
            round(area["largura"] * sx),
            round(area["altura"] * sy),
        )

    def _minerios_da_area(self, indice):
        area = self._area_na_tela(self.areas[indice])
        return [
            minerio for minerio in self.minerios
            if minerio.area_indice == indice and area.contains(minerio.rect)
        ]

    def _criar_minerio(self, indice, jogador):
        area = self._area_na_tela(self.areas[indice])
        tamanho = self.TAMANHO_MINERIO
        if area.width < tamanho or area.height < tamanho:
            return None

        max_x = area.right - tamanho
        max_y = area.bottom - tamanho

        for _ in range(self.TENTATIVAS_SPAWN):
            x = random.randint(area.left, max_x)
            y = random.randint(area.top, max_y)
            candidato = pygame.Rect(x, y, tamanho, tamanho)

            if candidato.colliderect(jogador.rect):
                continue
            if any(candidato.colliderect(m.rect) for m in self.minerios):
                continue
            if self.mapa.colide_com_obstaculo(candidato):
                continue

            minerio = Recurso(x, y, self.areas[indice]["tipo"], tamanho, self.catalogo)
            minerio.area_indice = indice
            return minerio

        return None

    def minerar(self, minerio):
        if minerio in self.minerios:
            indice = minerio.area_indice
            self.minerios.remove(minerio)
            self.tempos_respawn[indice] = 0.0

    def desenhar(self, tela):
        for minerio in self.minerios:
            minerio.desenhar(tela)
