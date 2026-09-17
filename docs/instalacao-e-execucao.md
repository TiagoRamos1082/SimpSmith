# Instalação e Execução

## 1. Requisitos

- Python instalado.
- Pygame instalado.
- Arquivos do projeto organizados nas pastas esperadas.

## 2. Instalar o Pygame

No terminal, execute:

```
python -m pip install pygame
```

## 3. Executar o jogo

Na raiz do projeto:

```
python main.py
```

## 4. Executar o editor de colisões

Na raiz do projeto:

```
python mapa/editor_colisoes.py
```

## 5. Problemas comuns

### Imagem não encontrada

Confira se o arquivo existe no caminho esperado:

`assets/mapa/mapaPrincipal.png`

Verifique também se o nome e a extensão estão corretos.

### Erro `No video mode has been set`

Esse erro pode ocorrer quando `.convert()` é chamado antes de criar uma janela do Pygame.

Inicialize o Pygame e crie a janela antes de carregar a imagem com `.convert()`.

### Colisões desalinhadas

Verifique se as coordenadas foram criadas em relação à imagem original e se a conversão de escala é aplicada corretamente no jogo.

### Bordas vermelhas aparecendo durante o jogo

As bordas de depuração devem ser desenhadas somente no editor ou quando um modo de depuração estiver explicitamente habilitado.

Ocultar as bordas não deve remover as colisões.

## 6. Execução recomendada

Durante o desenvolvimento:

1. Edite as colisões.
2. Teste o jogo.
3. Corrija as áreas incorretas.
4. Confirme que as bordas de depuração estão ocultas no jogo.
5. Salve as alterações e mantenha uma cópia de segurança dos arquivos importantes.