from pathlib import Path
import py_compile
import shutil

arquivo = Path("editores/mapas/editor_mapa.py")
backup = Path("backups/editor_mapa_antes_modernizacao.py")

codigo = arquivo.read_text(encoding="utf-8")

# Evita aplicar o mesmo patch duas vezes.
if "def alternar_tela_cheia(self):" in codigo:
    raise SystemExit("Patch já aplicado. Nenhuma alteração realizada.")

# 1. Janela redimensionável.
antigo = '''        self.tela = pygame.display.set_mode(
            (self.largura_janela, self.altura_janela)
        )
        pygame.display.set_caption("SimpSmith - Editor de Mapas")'''

novo = '''        self.tela_cheia = False
        self.tela = pygame.display.set_mode(
            (self.largura_janela, self.altura_janela),
            pygame.RESIZABLE
        )
        pygame.display.set_caption("SimpSmith - Editor de Mapas")'''

assert antigo in codigo, "Inicialização da janela não encontrada."
codigo = codigo.replace(antigo, novo, 1)

# 2. Métodos de controle da janela.
marcador = "    def tratar_eventos(self):"

metodos = '''    def alternar_tela_cheia(self):
        if self.tela_cheia:
            self.tela_cheia = False
            self.tela = pygame.display.set_mode(
                (self.largura_janela, self.altura_janela),
                pygame.RESIZABLE
            )
        else:
            self.largura_janela = self.tela.get_width()
            self.altura_janela = self.tela.get_height()

            self.tela_cheia = True
            self.tela = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN
            )

        self.largura_janela, self.altura_janela = self.tela.get_size()
        self.painel_x = self.largura_janela - self.painel_largura

    def voltar_central(self):
        self.executando = False

    def desenhar_botao_central(self):
        rect = pygame.Rect(
            self.painel_x + 20, 108, 280, 28
        )

        pygame.draw.rect(self.tela, (52, 61, 76), rect, border_radius=5)
        pygame.draw.rect(self.tela, (100, 130, 175), rect, 1, border_radius=5)

        texto = self.fonte_pequena.render(
            "VOLTAR À CENTRAL", True, (241, 241, 241)
        )
        self.tela.blit(
            texto,
            texto.get_rect(center=rect.center)
        )

'''

assert marcador in codigo, "Método tratar_eventos não encontrado."
codigo = codigo.replace(marcador, metodos + marcador, 1)

# 3. Botão visual no painel.
marcador = '''        self.desenhar_texto("EDITOR DE MAPAS", self.painel_x + 20, 25)'''

assert marcador in codigo, "Cabeçalho do painel não encontrado."
codigo = codigo.replace(
    marcador,
    marcador + "\n        self.desenhar_botao_central()",
    1
)

# 4. F11.
marcador = '''                if evento.key == pygame.K_ESCAPE:
                    self.executando = False

                elif evento.key == pygame.K_RETURN:'''

novo = '''                if evento.key == pygame.K_ESCAPE:
                    self.executando = False

                elif evento.key == pygame.K_F11:
                    self.alternar_tela_cheia()

                elif evento.key == pygame.K_RETURN:'''

assert marcador in codigo, "Bloco de teclas não encontrado."
codigo = codigo.replace(marcador, novo, 1)

# 5. Clique no botão e redimensionamento.
marcador = '''                elif evento.button == 1:
                    self.tratar_clique(evento.pos)'''

novo = '''                elif evento.button == 1:
                    botao_central = pygame.Rect(
                        self.painel_x + 20, 108, 280, 28
                    )

                    if botao_central.collidepoint(evento.pos):
                        self.voltar_central()
                    else:
                        self.tratar_clique(evento.pos)'''

assert marcador in codigo, "Bloco de clique esquerdo não encontrado."
codigo = codigo.replace(marcador, novo, 1)

marcador = '''            elif evento.type == pygame.MOUSEBUTTONUP:
                if evento.button == 2:'''

novo = '''            elif evento.type == pygame.VIDEORESIZE:
                if not self.tela_cheia:
                    self.largura_janela = max(800, evento.w)
                    self.altura_janela = max(600, evento.h)

                    self.tela = pygame.display.set_mode(
                        (self.largura_janela, self.altura_janela),
                        pygame.RESIZABLE
                    )

                    self.largura_janela, self.altura_janela = (
                        self.tela.get_size()
                    )
                    self.painel_x = (
                        self.largura_janela - self.painel_largura
                    )

            elif evento.type == pygame.MOUSEBUTTONUP:
                if evento.button == 2:'''

assert marcador in codigo, "Bloco de finalização do clique não encontrado."
codigo = codigo.replace(marcador, novo, 1)

# 6. Backup e validação antes de substituir.
backup.parent.mkdir(parents=True, exist_ok=True)

temporario = arquivo.with_name("editor_mapa_temp.py")
temporario.write_text(codigo, encoding="utf-8")

try:
    py_compile.compile(str(temporario), doraise=True)
except Exception:
    temporario.unlink(missing_ok=True)
    raise

shutil.copy2(arquivo, backup)
temporario.replace(arquivo)

print("Patch aplicado com sucesso!")
print("Backup original preservado.")
print("Janela redimensionável, F11 e retorno à Central adicionados.")
