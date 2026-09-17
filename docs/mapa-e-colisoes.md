# Mapas e Colisões

## 1. Mapa principal

A imagem utilizada atualmente é:

`assets/mapa/mapaPrincipal.png`

O arquivo `mapa/mapa.py` carrega a imagem e a desenha na janela do jogo, ajustando-a às dimensões atuais da tela.

## 2. Arquivo de colisões

As colisões do mapa principal são armazenadas em:

`mapa/colisoes.json`

Esse arquivo contém uma lista de retângulos que representam as regiões bloqueadas.

Cada retângulo possui quatro propriedades:

| Propriedade | Descrição |
| --- | --- |
| `x` | Posição horizontal. |
| `y` | Posição vertical. |
| `largura` | Dimensão horizontal. |
| `altura` | Dimensão vertical. |

Exemplo:

```
{
    "largura_imagem": 1024,
    "altura_imagem": 576,
    "obstaculos": [
        {
            "x": 350,
            "y": 170,
            "largura": 60,
            "altura": 75
        }
    ]
}
```

As coordenadas são relativas à imagem original do mapa.

## 3. Funcionamento das colisões

O mapa verifica se o retângulo de colisão do jogador se sobrepõe a algum obstáculo.

Quando existe sobreposição, o movimento é bloqueado.

Os obstáculos podem representar:

- Casas.
- Árvores.
- Cercas.
- Pedras.
- Água.
- Outras regiões que não podem ser atravessadas.

## 4. Escala

A imagem é redimensionada para preencher a janela.

As coordenadas e dimensões dos obstáculos precisam ser convertidas proporcionalmente para corresponder ao tamanho atual da tela.

Essa conversão deve ser aplicada tanto na renderização das bordas de depuração quanto na verificação das colisões.

## 5. Visualização das bordas

As bordas coloridas são ferramentas de depuração do editor.

Elas devem permanecer visíveis no editor, mas não precisam ser desenhadas durante a execução normal do jogo.

A renderização do cenário não deve ser confundida com a lógica de colisão: ocultar as bordas não deve desativar os obstáculos.

## 6. Adição de outros mapas

Para adicionar novos cenários, recomenda-se manter uma imagem e um arquivo de colisões para cada mapa.

Exemplo de organização futura:

```
assets/mapa/
├── mapaPrincipal.png
├── floresta.png
└── caverna.png

mapa/colisoes/
├── mapaPrincipal.json
├── floresta.json
└── caverna.json
```

O código precisará selecionar o arquivo de colisões correspondente ao cenário ativo.