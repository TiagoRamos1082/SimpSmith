class GerenciadorInteracoes:
    def __init__(self, mapa):
        self.mapa = mapa
        self.acoes = {}

    def registrar_acao(self, tipo, acao):
        if not isinstance(tipo, str) or not tipo:
            raise ValueError("Tipo de intera??o inv?lido.")

        if not callable(acao):
            raise TypeError("A a??o precisa ser uma fun??o execut?vel.")

        self.acoes[tipo] = acao

    def obter_interacoes(self, rect):
        return [
            area
            for area in self.mapa.retangulos_interacao
            if rect.colliderect(area["rect"])
        ]

    def interagir(self, rect):
        areas = self.obter_interacoes(rect)
        executadas = []

        for area in areas:
            acao = self.acoes.get(area["tipo"])

            if acao is None:
                continue

            acao(area)
            executadas.append(area)

        return executadas
