from pathlib import Path
import re
import py_compile
import shutil

arquivo = Path("editores/mapas/editor_recursos.py")

if not arquivo.exists():
    raise SystemExit("Arquivo editor_recursos.py não encontrado.")

codigo = arquivo.read_text(encoding="utf-8")
original = codigo

# 1. Aumentar a altura do rodapé para acomodar os controles.
padrao_altura = r"ALTURA_RODAPE\s*=\s*\d+"
codigo, alteracoes = re.subn(
    padrao_altura,
    "ALTURA_RODAPE = 112",
    codigo,
    count=1
)

if alteracoes != 1:
    raise SystemExit("Não encontrei a configuração ALTURA_RODAPE.")

# 2. Adicionar função que calcula a posição dos botões.
marcador = '''def desenhar_texto(texto, x, y, cor=COR_TEXTO, pequena=False):
    fonte_usada = fonte_pequena if pequena else fonte
    superficie = fonte_usada.render(texto, True, cor)
    tela.blit(superficie, (x, y))
'''

funcao = marcador + '''

def obter_botoes_propriedades(largura, y):
    botoes = {}
    largura_coluna = largura // 3

    for indice, campo in enumerate(
        ("maximo", "inicial", "respawn")
    ):
        x = indice * largura_coluna

        botoes[campo] = {
            "menos": pygame.Rect(
                x + largura_coluna - 105, y + 57, 34, 30
            ),
            "mais": pygame.Rect(
                x + largura_coluna - 55, y + 57, 34, 30
            ),
        }

    return botoes
'''

if marcador not in codigo:
    raise SystemExit("Não encontrei a função desenhar_texto.")

codigo = codigo.replace(marcador, funcao, 1)

# 3. Inserir tratamento dos cliques nos botões.
evento_antigo = '''            elif evento.button == 1:
                indice = selecionar_area(evento.pos)
'''

evento_novo = '''            elif evento.button == 1:
                y_painel = tela.get_height() - ALTURA_RODAPE
                botoes = obter_botoes_propriedades(
                    tela.get_width(), y_painel
                )

                if (
                    area_selecionada is not None
                    and y_painel <= evento.pos[1]
                ):
                    for campo, controles in botoes.items():
                        if controles["menos"].collidepoint(evento.pos):
                            alterar_configuracao(campo, -1)
                            break

                        if controles["mais"].collidepoint(evento.pos):
                            alterar_configuracao(campo, 1)
                            break

                    continue

                indice = selecionar_area(evento.pos)
'''

if evento_antigo not in codigo:
    raise SystemExit("Não encontrei o bloco de clique esquerdo.")

codigo = codigo.replace(evento_antigo, evento_novo, 1)

# 4. Substituir o rodapé visual pelo painel de propriedades.
inicio = codigo.find("    # Rodapé\n")
fim = codigo.find(
    "    if pygame.time.get_ticks() < tempo_mensagem:",
    inicio
)

if inicio == -1 or fim == -1:
    raise SystemExit("Não encontrei os limites do rodapé.")

painel = '''    # Painel de propriedades
    y_rodape = altura_tela - ALTURA_RODAPE

    pygame.draw.rect(
        tela,
        COR_PAINEL,
        (0, y_rodape, largura_tela, ALTURA_RODAPE)
    )

    pygame.draw.line(
        tela,
        COR_PAINEL_CLARO,
        (0, y_rodape),
        (largura_tela, y_rodape),
        1
    )

    desenhar_texto(
        "PROPRIEDADES DA ÁREA",
        20, y_rodape + 10,
        COR_DESTAQUE,
        pequena=True
    )

    botoes = obter_botoes_propriedades(
        largura_tela, y_rodape
    )

    if area_selecionada is not None:
        item = areas[area_selecionada]

        propriedades = [
            ("maximo", "Quantidade máxima", str(item["maximo"])),
            ("inicial", "Quantidade inicial", str(item["inicial"])),
            ("respawn", "Tempo de respawn", f"{item['respawn']:.0f} s"),
        ]

        largura_coluna = largura_tela // 3

        for indice, (campo, rotulo, valor) in enumerate(propriedades):
            x = indice * largura_coluna

            desenhar_texto(
                rotulo,
                x + 12,
                y_rodape + 39,
                COR_SECUNDARIA,
                pequena=True
            )

            for acao in ("menos", "mais"):
                botao = botoes[campo][acao]

                pygame.draw.rect(
                    tela,
                    COR_PAINEL_CLARO,
                    botao,
                    border_radius=5
                )

                pygame.draw.rect(
                    tela,
                    COR_DESTAQUE,
                    botao,
                    width=1,
                    border_radius=5
                )

                simbolo = "-" if acao == "menos" else "+"

                superficie = fonte.render(
                    simbolo, True, COR_TEXTO
                )

                tela.blit(
                    superficie,
                    superficie.get_rect(center=botao.center)
                )

            superficie_valor = fonte_pequena.render(
                valor, True, COR_TEXTO
            )

            posicao_valor = (
                botoes[campo]["menos"].left - 12,
                botoes[campo]["menos"].centery
            )

            tela.blit(
                superficie_valor,
                superficie_valor.get_rect(
                    midright=posicao_valor
                )
            )

        desenhar_texto(
            "Clique nos botões para alterar. As mudanças são salvas automaticamente.",
            20,
            y_rodape + 91,
            COR_SECUNDARIA,
            pequena=True
        )

    else:
        desenhar_texto(
            "Selecione uma área no mapa para editar suas propriedades.",
            20,
            y_rodape + 54,
            COR_SECUNDARIA,
            pequena=True
        )

'''

codigo = codigo[:inicio] + painel + codigo[fim:]

if codigo == original:
    raise SystemExit("Nenhuma alteração foi realizada.")

# 5. Validar antes de substituir o arquivo original.
temporario = arquivo.with_name("editor_recursos_temp.py")
temporario.write_text(codigo, encoding="utf-8")

try:
    py_compile.compile(str(temporario), doraise=True)
except py_compile.PyCompileError as erro:
    temporario.unlink(missing_ok=True)
    raise SystemExit(f"Erro de sintaxe. Original preservado:\n{erro}")

# 6. Criar backup e aplicar.
backup = Path(
    "backups/editor_recursos_antes_painel_propriedades.py"
)
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(arquivo, backup)

temporario.replace(arquivo)

print("Painel de propriedades instalado com sucesso!")
print(f"Backup: {backup}")
print("Sintaxe Python validada.")

