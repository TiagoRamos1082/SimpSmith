class GerenciadorJogo:
    def __init__(self):
        self.estado = "menu"
        self.partida = None
        self.origem_controles = None
        self.executando = True

    def processar_opcao(self, opcao, criar_partida):
        if self.estado == "menu":
            self._processar_menu(opcao, criar_partida)

        elif self.estado == "pausa":
            self._processar_pausa(opcao)

    def _processar_menu(self, opcao, criar_partida):
        if opcao == "Novo jogo":
            self.partida = criar_partida()
            self.estado = "jogo"

        elif opcao == "Controles":
            self.origem_controles = "menu"
            self.estado = "controles"

        elif opcao == "Sair":
            self.executando = False

    def _processar_pausa(self, opcao):
        if opcao == "Continuar":
            self.estado = "jogo"

        elif opcao == "Controles":
            self.origem_controles = "pausa"
            self.estado = "controles"

        elif opcao == "Menu principal":
            self.partida = None
            self.estado = "menu"

        elif opcao == "Sair do jogo":
            self.executando = False

    def pausar(self):
        if self.estado == "jogo":
            self.estado = "pausa"

    def voltar_dos_controles(self):
        if self.origem_controles is not None:
            self.estado = self.origem_controles
            self.origem_controles = None
