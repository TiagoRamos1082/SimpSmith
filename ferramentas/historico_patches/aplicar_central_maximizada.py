from pathlib import Path
import py_compile
import shutil

arquivo = Path("editores/editor_geral.py")
codigo = arquivo.read_text(encoding="utf-8")

original = codigo

# Maximizar a Central sem usar tela cheia.
codigo = codigo.replace(
    '        self.janela.geometry("1050x760")\n',
    '        self.janela.geometry("1050x760")\n'
    '        self.janela.after(100, lambda: self.janela.state("zoomed"))\n',
    1
)

# Estado para acumular movimentos pequenos do scroll.
codigo = codigo.replace(
    '        self.processos = []\n',
    '        self.processos = []\n'
    '        self._scroll_resto = 0\n',
    1
)

# Remover ativações temporárias do scroll por Enter/Leave.
codigo = codigo.replace(
    '''        self.canvas.bind("<Enter>", self._ativar_scroll)
        self.canvas.bind("<Leave>", self._desativar_scroll)
        self.area.bind("<Enter>", self._ativar_scroll)
        self.area.bind("<Leave>", self._desativar_scroll)
''',
    '''        # Scroll global: a função verifica se o ponteiro está sobre a área.
        self.janela.bind_all("<MouseWheel>", self._rolar_mouse)
''',
    1
)

# Substituir os métodos antigos de scroll.
inicio = codigo.index('    def _ativar_scroll(self, evento=None):')
fim = codigo.index('    def criar_categoria(', inicio)

metodos = '''    def _rolar_mouse(self, evento):
        # Ignora a rolagem quando o mouse está fora da área de conteúdo.
        mouse_x, mouse_y = self.janela.winfo_pointerxy()

        esquerda = self.canvas.winfo_rootx()
        topo = self.canvas.winfo_rooty()
        direita = esquerda + self.canvas.winfo_width()
        base = topo + self.canvas.winfo_height()

        if not (esquerda <= mouse_x <= direita and topo <= mouse_y <= base):
            return

        self._scroll_resto += evento.delta
        passos = int(self._scroll_resto / 120)

        if passos:
            self.canvas.yview_scroll(-passos, "units")
            self._scroll_resto -= passos * 120

'''
codigo = codigo[:inicio] + metodos + codigo[fim:]

if codigo == original:
    raise SystemExit("Nenhuma alteração foi aplicada. Verifique se o arquivo mudou.")

temporario = arquivo.with_name("editor_geral_temp.py")
temporario.write_text(codigo, encoding="utf-8")
py_compile.compile(str(temporario), doraise=True)

backup = Path("backups/editor_geral_antes_maximizado_scroll.py")
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(arquivo, backup)

temporario.replace(arquivo)

print("Central atualizada e sintaxe validada!")
print(f"Backup: {backup}")
