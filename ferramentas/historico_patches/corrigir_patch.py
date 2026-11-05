from pathlib import Path
import re

arquivo = Path("patch_editor_mapa.py")
codigo = arquivo.read_text(encoding="utf-8")

padrao = r'marcador \+ "\\\s*self\.desenhar_botao_central\(\)"'

substituicao = r'marcador + "\n        self.desenhar_botao_central()"'

codigo_novo, quantidade = re.subn(
    padrao,
    lambda _: substituicao,
    codigo,
    count=1
)

if quantidade != 1:
    raise SystemExit("Não encontrei o trecho esperado. Nenhuma alteração feita.")

arquivo.write_text(codigo_novo, encoding="utf-8")

print("Trecho corrigido!")
