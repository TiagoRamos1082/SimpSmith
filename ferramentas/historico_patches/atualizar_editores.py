from pathlib import Path
from datetime import datetime
import py_compile
import shutil
import re
import sys

arquivos = {
    "itens": Path("editores/itens/editor_itens.py"),
    "mapas": Path("editores/mapas/editor_mapa.py"),
    "sprites": Path("editores/tiles/editor_sprites.py"),
    "tiles": Path("editores/tiles/importador.py"),
}

codigos = {}

for nome, caminho in arquivos.items():
    if not caminho.exists():
        raise SystemExit(f"Arquivo não encontrado: {caminho}")
    codigos[nome] = caminho.read_text(encoding="utf-8")

# --------------------------------------------------
# 1. EDITOR DE ITENS
# Remove a abertura de uma segunda Central.
# --------------------------------------------------

codigo = codigos["itens"]

padrao = (
    r"    def _voltar_central\(self\):\n"
    r".*?(?=    def _montar_interface\(self\):)"
)

novo_metodo = '''    def _voltar_central(self):
        # A Central original permanece aberta em segundo plano.
        self.janela.destroy()

'''

codigo, quantidade = re.subn(
    padrao, novo_metodo, codigo, count=1, flags=re.S
)

if quantidade != 1:
    raise SystemExit("Não foi possível localizar o retorno do Editor de Itens.")

codigo = codigo.replace(
    '        self.janela.geometry("900x560")',
    '''        self.janela.geometry("900x560")
        self.janela.after(
            100, lambda: self.janela.state("zoomed")
        )''',
    1
)

codigos["itens"] = codigo

# --------------------------------------------------
# 2. FUNÇÃO DE MAXIMIZAÇÃO PARA OS EDITORES PYGAME
# --------------------------------------------------

def maximizar_pygame(codigo, legenda):
    if "import ctypes" not in codigo:
        if "import pygame" not in codigo:
            raise SystemExit(
                f"Não encontrei import pygame no editor {legenda}."
            )
        codigo = codigo.replace(
            "import pygame",
            "import pygame\nimport ctypes",
            1
        )

    marcador = (
        f'pygame.display.set_caption("{legenda}")'
    )

    if marcador not in codigo:
        raise SystemExit(
            f"Não encontrei o título da janela: {legenda}"
        )

    bloco = marcador + '''

        # Maximiza a janela mantendo bordas e barra de tarefas.
        try:
            pygame.display.flip()
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 3)
        except (AttributeError, OSError):
            pass
'''

    return codigo.replace(marcador, bloco, 1)

# --------------------------------------------------
# 3. EDITOR DE MAPAS
# --------------------------------------------------

codigos["mapas"] = maximizar_pygame(
    codigos["mapas"],
    "SimpSmith - Editor de Mapas"
)

# --------------------------------------------------
# 4. EDITOR DE SPRITES
# --------------------------------------------------

codigos["sprites"] = maximizar_pygame(
    codigos["sprites"],
    "SimpSmith - Editor de Sprites"
)

# --------------------------------------------------
# 5. IMPORTADOR DE TILES
# Maximiza a janela Tkinter.
# --------------------------------------------------

codigo = codigos["tiles"]

marcador = '        self.janela.minsize(900, 650)'

if marcador not in codigo:
    raise SystemExit(
        "Não encontrei a configuração de tamanho mínimo do Importador."
    )

codigo = codigo.replace(
    marcador,
    marcador + '''

        self.janela.after(
            100, lambda: self.janela.state("zoomed")
        )''',
    1
)

codigos["tiles"] = codigo

# --------------------------------------------------
# 6. VALIDAR TODOS OS ARQUIVOS ANTES DE SUBSTITUIR
# --------------------------------------------------

temporarios = []

try:
    for nome, caminho in arquivos.items():
        temporario = caminho.with_name(
            caminho.stem + "_temp.py"
        )

        temporario.write_text(
            codigos[nome],
            encoding="utf-8"
        )

        py_compile.compile(
            str(temporario),
            doraise=True
        )

        temporarios.append((nome, caminho, temporario))

except Exception as erro:
    for _, _, temporario in temporarios:
        temporario.unlink(missing_ok=True)

    raise SystemExit(
        f"Validação falhou. Nenhum original foi substituído:\n{erro}"
    )

# --------------------------------------------------
# 7. BACKUP E SUBSTITUIÇÃO
# --------------------------------------------------

pasta_backup = Path("backups")
pasta_backup.mkdir(exist_ok=True)

identificador = datetime.now().strftime("%Y%m%d_%H%M%S")

for nome, caminho, temporario in temporarios:
    backup = pasta_backup / (
        f"{caminho.stem}_antes_maximizacao_{identificador}.py"
    )

    shutil.copy2(caminho, backup)
    temporario.replace(caminho)

    print(f"Atualizado: {caminho}")
    print(f"Backup: {backup}")

print("\nTodas as alterações foram aplicadas!")
print("Os quatro arquivos passaram na validação de sintaxe.")
