
from personagens.personagem import Personagem


class Jogador(Personagem):
    def __init__(self, x, y):
        super().__init__(x, y, velocidade=150)
