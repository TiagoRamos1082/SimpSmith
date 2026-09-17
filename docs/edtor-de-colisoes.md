# Editor Visual de Colisões

## 1. Objetivo

O editor visual permite definir os obstáculos do mapa usando o mouse, sem precisar editar coordenadas manualmente no código Python.

Arquivo: `mapa/editor_colisoes.py`

## 2. Como abrir

Na raiz do projeto, execute:

```
python mapa/editor_colisoes.py
```

O editor abre a imagem principal e mostra os obstáculos já salvos.

## 3. Controles

| Controle | Ação |
| --- | --- |
| Botão esquerdo | Criar um retângulo arrastando o mouse. |
| Botão direito | Remover o obstáculo clicado. |
| `B` | Mostrar ou ocultar as bordas. |
| `Ctrl + S` | Salvar as alterações. |
| `Delete` | Remover o último obstáculo. |
| `Esc` | Fechar o editor. |

As alterações realizadas são salvas automaticamente após a criação ou remoção de obstáculos.

## 4. Arquivo de saída

Por padrão, o editor salva os dados em:

`mapa/colisoes.json`

Esse arquivo é utilizado pelo sistema de colisões do jogo.

## 5. Recomendações de uso

1. Abra o editor.
2. Localize as casas, árvores, cercas e outros objetos.
3. Desenhe retângulos sobre as áreas que devem bloquear o jogador.
4. Remova retângulos incorretos com o botão direito.
5. Execute o jogo para testar as colisões.
6. Reabra o editor e faça os ajustes necessários.

## 6. Limitações

O editor utiliza retângulos como áreas de colisão.

Para objetos irregulares, pode ser necessário criar vários retângulos menores.

A ferramenta não identifica automaticamente os objetos da imagem: as áreas bloqueadas são definidas manualmente pelo usuário.

## 7. Boas práticas

- Evite retângulos excessivamente grandes.
- Não bloqueie caminhos que devem permanecer acessíveis.
- Teste o movimento do jogador após alterações.
- Faça cópias de segurança do JSON antes de mudanças significativas.