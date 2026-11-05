from pathlib import Path
import py_compile
import shutil

arquivo = Path("editores/mapas/editor_colisoes.py")
codigo = arquivo.read_text(encoding="utf-8")
original = codigo

# Adiciona a detecção do clique no botão.
antigo_evento = '''            elif evento.button == 1:

                ponto = mouse_para_imagem(evento.pos)
'''

novo_evento = '''            elif evento.button == 1:

                botao_voltar = pygame.Rect(
                    tela.get_width() - 190, 12, 170, 48
                )

                if botao_voltar.collidepoint(evento.pos):
                    executando = False
                    continue

                ponto = mouse_para_imagem(evento.pos)
'''

if antigo_evento not in codigo:
    raise SystemExit("Não encontrei o trecho do clique esquerdo.")

codigo = codigo.replace(antigo_evento, novo_evento, 1)

# Desenha o botão no cabeçalho.
antigo_render = '''    tela.blit(texto_atalhos, (220, 43))

    if modo == "sprite":
'''

novo_render = '''    tela.blit(texto_atalhos, (220, 43))

    botao_voltar = pygame.Rect(
        largura_tela - 190, 12, 170, 48
    )

    pygame.draw.rect(
        tela, PAINEL_CLARO, botao_voltar, border_radius=7
    )
    pygame.draw.rect(
        tela, COR_DESTAQUE, botao_voltar,
        width=1, border_radius=7
    )

    texto_voltar = fonte_pequena.render(
        "< VOLTAR À CENTRAL", True, COR_TEXTO
    )
    tela.blit(
        texto_voltar,
        texto_voltar.get_rect(center=botao_voltar.center)
    )

    if modo == "sprite":
'''

if antigo_render not in codigo:
    raise SystemExit("Não encontrei o trecho do cabeçalho.")

codigo = codigo.replace(antigo_render, novo_render, 1)

if codigo == original:
    raise SystemExit("Nenhuma alteração foi aplicada.")

temporario = arquivo.with_name("editor_colisoes_temp.py")
temporario.write_text(codigo, encoding="utf-8")
py_compile.compile(str(temporario), doraise=True)

backup = Path("backups/editor_colisoes_antes_botao_voltar.py")
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(arquivo, backup)

temporario.replace(arquivo)

print("Botão de retorno adicionado!")
print(f"Backup: {backup}")
