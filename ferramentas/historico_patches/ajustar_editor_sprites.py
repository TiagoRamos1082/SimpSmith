from pathlib import Path
import shutil
import re
import py_compile
import sys

arquivo = Path("editores/tiles/editor_sprites.py")
codigo = arquivo.read_text(encoding="utf-8-sig")

if "def alternar_tela_cheia(self):" not in codigo:
    sys.exit("Metodo de tela cheia nao encontrado. Nada alterado.")

# Backup de seguranca
backup = arquivo.with_name("editor_sprites.py.backup_visual2")

if backup.exists():
    sys.exit(f"Backup ja existe: {backup}. Nada alterado.")

novo = codigo

# Remover metodo de alternancia.
inicio = novo.index("    def alternar_tela_cheia(self):")
fim = novo.index("    def desenhar_texto(", inicio)
novo = novo[:inicio] + novo[fim:]

# Remover atalho F11.
novo = novo.replace(
    '''                if evento.key == pygame.K_F11:
                    self.alternar_tela_cheia()

                elif evento.key == pygame.K_ESCAPE:
''',
    '''                if evento.key == pygame.K_ESCAPE:
''',
    1
)

# Reduzir fonte pequena para evitar linhas encostadas.
novo = novo.replace(
    "self.fonte_pequena = pygame.font.Font(None, 20)",
    "self.fonte_pequena = pygame.font.Font(None, 18)",
    1
)

# Remover indicacao de F11 do cabecalho.
novo = novo.replace(
    '        estado = "TELA CHEIA" if self.tela_cheia else "JANELA"\n'
    '        self.desenhar_texto(\n'
    '            f"{estado} | F11: alternar",\n'
    '            max(300, self.largura - 230), 25,\n'
    '            self.fonte_pequena, azul\n'
    '        )\n',
    '        self.desenhar_texto(\n'
    '            "MODO TELA CHEIA",\n'
    '            max(300, self.largura - 230), 25,\n'
    '            self.fonte_pequena, azul\n'
    '        )\n',
    1
)

# Remover F11 da lista de atalhos.
novo = novo.replace(
    '            "[F11] Tela cheia",\n',
    '',
    1
)

if novo == codigo:
    sys.exit("Nenhuma alteracao identificada. Original preservado.")

# Validar antes de substituir.
temporario = arquivo.with_name("editor_sprites.tmp")
temporario.write_text(novo, encoding="utf-8")

try:
    py_compile.compile(str(temporario), doraise=True)
except Exception as erro:
    temporario.unlink(missing_ok=True)
    sys.exit(f"Erro de sintaxe: {erro}")

shutil.copy2(arquivo, backup)
temporario.replace(arquivo)

print("Atualizacao aplicada com sucesso!")
print(f"Backup criado: {backup}")
