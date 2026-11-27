class Camera:
    def __init__(self, largura_tela, altura_tela):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela

        self.x = 0
        self.y = 0

    def redimensionar(self, largura_tela, altura_tela):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela

    def atualizar(self, alvo, largura_mundo, altura_mundo):
        self.x = alvo.centerx - self.largura_tela // 2
        self.y = alvo.centery - self.altura_tela // 2

        if self.largura_tela >= largura_mundo:
            self.x = (largura_mundo - self.largura_tela) // 2
        else:
            limite_x = largura_mundo - self.largura_tela
            self.x = max(0, min(self.x, limite_x))

        if self.altura_tela >= altura_mundo:
            self.y = (altura_mundo - self.altura_tela) // 2
        else:
            limite_y = altura_mundo - self.altura_tela
            self.y = max(0, min(self.y, limite_y))

    def aplicar(self, posicao):
        x, y = posicao

        return (
            round(x - self.x),
            round(y - self.y)
        )

    def aplicar_rect(self, rect):
        return rect.move(-self.x, -self.y)
