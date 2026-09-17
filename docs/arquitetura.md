## <span>**1.**</span> <span>**Arquitetura**</span> <span>**do**</span> <span>**projeto**</span>

<span>A</span> <span>principal</span> <span>regra</span> <span>será:</span> <span>**cada**</span><span style="color: rgb(13, 13, 13);"> </span><span>**módulo**</span><span style="color: rgb(13, 13, 13);"> </span><span>**cuida**</span><span style="color: rgb(13, 13, 13);"> </span><span>**de**</span><span style="color: rgb(13, 13, 13);"> </span><span>**uma**</span><span style="color: rgb(13, 13, 13);"> </span><span>**responsabilidade**</span><span style="color: rgb(13, 13, 13);"> </span><span>**e**</span><span style="color: rgb(13, 13, 13);"> </span><span>**se**</span><span style="color: rgb(13, 13, 13);"> </span><span>**comunica**</span><span style="color: rgb(13, 13, 13);"> </span><span>**com**</span><span style="color: rgb(13, 13, 13);"> </span><span>**os**</span><span style="color: rgb(13, 13, 13);"> </span><span>**outros**</span><span style="color: rgb(13, 13, 13);"> </span><span>**por**</span><span style="color: rgb(13, 13, 13);"> </span><span>**interfaces**</span><span style="color: rgb(13, 13, 13);"> </span><span>**claras.**</span>

<span style="color: rgb(93, 93, 93);">text</span>

```

pokemon_2d/
├── main.py
├── mapa/
│   ├── __init__.py
│   └── mapa.py
├── personagens/
│   ├── __init__.py
│   ├── personagem.py
│   └── jogador.py
├── acoes/
│   ├── __init__.py
│   ├── movimentacao.py
│   └── colisao.py
└── objetos/
    ├── __init__.py
    ├── objeto.py
    ├── arvore.py
    └── agua.py
```

### <span>**Responsabilidade**</span> <span>**de**</span> <span>**cada**</span> <span>**arquivo**</span>

| <span>**Arquivo**</span> | <span>**Responsabilidade**</span> |
| --- | --- |
| `main.py` | <span>Inicialização,</span> <span>eventos,</span> <span>atualização</span> <span>e</span> <span>desenho</span> |
| `mapa.py` | <span>Grade</span> <span>2D,</span> <span>tiles,</span> <span>terreno</span> <span>e</span> <span>renderização</span> <span>do</span> <span>mapa</span> |
| `personagem.py` | <span>Classe</span> <span>base,</span> <span>posição,</span> <span>direção</span> <span>e</span> <span>desenho</span> |
| `jogador.py` | <span>Controles</span> <span>e</span> <span>especialização</span> <span>do</span> <span>personagem</span> <span>jogável</span> |
| `movimentacao.py` | <span>Velocidade,</span> <span>direção</span> <span>e</span> <span>deslocamento</span> |
| `colisao.py` | <span>Verificação</span> <span>de</span> <span>limites</span> <span>e</span> <span>obstáculos</span> |
| `objeto.py` | <span>Classe</span> <span>base</span> <span>dos</span> <span>objetos</span> <span>do</span> <span>cenário</span> |
| `arvore.py` | <span>Aparência</span> <span>e</span> <span>colisão</span> <span>das</span> <span>árvores</span> |
| `agua.py` | <span>Aparência</span> <span>e</span> <span>bloqueio</span> <span>da</span> <span>água</span> |
