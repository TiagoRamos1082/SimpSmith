from pathlib import Path
import py_compile
import shutil

arquivo = Path("editores/mapas/editor_mapa.py")
codigo = arquivo.read_text(encoding="utf-8")

# Remove as dimensões do cabeçalho, que estavam sobrepondo o botão.
bloco = '''        self.desenhar_texto(
            f"{self.largura} x {self.altura} tiles",
            self.painel_x + 20, 101, self.fonte_pequena
        )
'''

if bloco not in codigo:
    raise SystemExit("Não encontrei o bloco das dimensões. Nada foi alterado.")

codigo = codigo.replace(bloco, "", 1)

# Adiciona as dimensões dentro da área rolável.
marcador = '''        # Camada.
        secao("CAMADA ATUAL", y)'''

novo = '''        # Informações do mapa.
        texto(
            f"Dimensões: {self.largura} x {self.altura} tiles",
            y, self.fonte_pequena, (170, 176, 188)
        )
        y += 32

        # Camada.
        secao("CAMADA ATUAL", y)'''

if marcador not in codigo:
    raise SystemExit("Não encontrei o início do conteúdo rolável.")

codigo = codigo.replace(marcador, novo, 1)

temporario = arquivo.with_name("editor_mapa_temp.py")
temporario.write_text(codigo, encoding="utf-8")

py_compile.compile(str(temporario), doraise=True)

backup = Path("backups/editor_mapa_antes_correcao_botao.py")
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(arquivo, backup)

temporario.replace(arquivo)

print("Cabeçalho reorganizado e código validado!")
