class Camera:
    def __init__(self, largura_tela, altura_tela):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela

        self.x = 0
        self.y = 0

    def atualizar(self, alvo, largura_mundo, altura_mundo):
        # Centraliza a câmera no alvo.
        self.x = alvo.centerx - self.largura_tela // 2
        self.y = alvo.centery - self.altura_tela // 2

        # Limita a câmera às bordas do mundo.
        limite_x = max(0, largura_mundo - self.largura_tela)
        limite_y = max(0, altura_mundo - self.altura_tela)

        self.x = max(0, min(self.x, limite_x))
        self.y = max(0, min(self.y, limite_y))

    def aplicar(self, posicao):
        x, y = posicao

        return (
            round(x - self.x),
            round(y - self.y)
        )
