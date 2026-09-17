# SimpSmith

## Sobre o projeto

**SimpSmith** é um jogo desenvolvido em Python utilizando a biblioteca Pygame. O projeto apresenta mecânicas de exploração, coleta de recursos, gerenciamento de inventário e criação de itens por meio de um sistema de crafting.

O jogador pode explorar o mapa, coletar minérios e plantas, armazenar recursos e utilizar ingredientes para produzir materiais e novos itens.

O projeto utiliza uma arquitetura modular, separando as responsabilidades em diferentes sistemas e diretórios.

## Tecnologias utilizadas

- Python 3.13

- Pygame 2.6.1

- JSON para armazenamento de dados do jogo

- Git e GitHub para versionamento

## Requisitos

Antes de executar o projeto, é necessário ter instalado:

- Python 3.13

- pip

- Git (caso queira clonar o repositório)

## Instalação

### 1. Clonar o repositório

```
git clone URL_DO_REPOSITORIO
```

Entre na pasta do projeto:

```
cd SimpSmith
```

Também é possível baixar o projeto pelo GitHub, utilizando a opção **Code &gt; Download ZIP**.

### 2. Criar o ambiente virtual

Na raiz do projeto, execute:

```
python -m venv venv
```

### 3. Ativar o ambiente virtual

No Windows, utilizando PowerShell:

```
.\venv\Scripts\Activate.ps1
```

#### Problema: execução de scripts desabilitada

Caso o PowerShell apresente uma mensagem informando que a execução de scripts está desabilitada, execute:

```
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Confirme a alteração quando solicitado e tente ativar novamente:

```
.\venv\Scripts\Activate.ps1
```

Essa configuração permite executar scripts locais para o usuário atual do Windows.

No Linux ou macOS, utilize:

```
source venv/bin/activate
```

### 4. Instalar as dependências

Com o ambiente virtual ativado:

```
python -m pip install -r docs/requirements.txt
```

### 5. Executar o jogo

Na raiz do projeto:

```
python main.py
```

## Controles

Os controles devem ser consultados na versão atual do jogo. A tabela abaixo deve ser atualizada conforme as teclas efetivamente implementadas.

| Ação | Tecla |
| --- | --- |
| Movimentar para cima | A confirmar |
| Movimentar para baixo | A confirmar |
| Movimentar para esquerda | A confirmar |
| Movimentar para direita | A confirmar |
| Interagir e coletar recursos | A confirmar |
| Abrir inventário | A confirmar |
| Acessar crafting | A confirmar |

## Mecânicas do jogo

### Exploração

O jogador pode percorrer o mapa e explorar as áreas disponíveis, respeitando os obstáculos e limites definidos pelo sistema de colisões.

### Coleta de recursos

O jogo possui diferentes tipos de recursos naturais:

- **Minérios:** recursos utilizados como ingredientes na produção de materiais.

- **Plantas:** recursos naturais que podem ser coletados e armazenados no inventário.

### Inventário

Responsável por armazenar e apresentar os recursos e itens obtidos durante a partida.

### Crafting

Permite utilizar ingredientes para produzir novos materiais e itens. As receitas são definidas em arquivos JSON.

### Progressão

A progressão está relacionada à exploração, coleta de recursos e utilização dos ingredientes disponíveis para produzir novos elementos.

As condições de vitória e derrota dependem das funcionalidades implementadas na versão atual.

## Estrutura do projeto

```
SimpSmith/
│
├── acoes/
├── assets/
├── dados/
├── docs/
├── editores/
├── imagens/
├── interface/
├── inventario/
├── mapa/
├── objetos/
├── personagens/
├── sistemas/
│
├── main.py
├── README.md
└── .gitignore
```

### Responsabilidades dos diretórios

| Diretório | Responsabilidade |
| --- | --- |
| `acoes/` | Mecânicas de movimentação, colisão, coleta, spawn e crafting. |
| `assets/` | Imagens e recursos visuais do jogo. |
| `dados/` | Dados dos itens e receitas em JSON. |
| `docs/` | Documentação técnica e orientações do projeto. |
| `editores/` | Ferramentas auxiliares para edição de dados. |
| `interface/` | Elementos da interface do jogo. |
| `inventario/` | Gerenciamento e interfaces do inventário e crafting. |
| `mapa/` | Mapa, áreas de recursos e sistema de colisões. |
| `objetos/` | Classes que representam objetos e recursos. |
| `personagens/` | Classes e comportamentos dos personagens. |
| `sistemas/` | Catálogos, gerenciamento do jogo e tutorial. |
| `main.py` | Ponto de entrada da aplicação. |

## Documentação complementar

A documentação técnica está disponível no diretório `docs/`:

- `arquitetura.md`: organização e arquitetura do projeto.

- `instalacao-e-execucao.md`: orientações de instalação e execução.

- `mapa-e-colisoes.md`: funcionamento do mapa e das colisões.

- `edtor-de-colisoes.md`: documentação do editor de colisões.

### Game Design Document (GDD)

O GDD apresenta a proposta do jogo, suas mecânicas, regras, objetivos e características de design.

**Localização:** \[Inserir link ou caminho do GDD atualizado.\]

## Limitações e funcionalidades futuras

O SimpSmith encontra-se em desenvolvimento. Algumas funcionalidades podem estar incompletas ou sujeitas a alterações.

Possíveis melhorias incluem:

- Expansão das áreas exploráveis.

- Adição de novos recursos naturais.

- Ampliação das receitas e dos itens disponíveis.

- Aprimoramento das mecânicas de coleta e interação.

- Implementação de um tutorial integrado.

- Melhorias na interface e na experiência do jogador.

- Expansão das mecânicas de progressão.

## Repositório

**GitHub:** \[<https://github.com/TiagoRamos1082/SimpSmith>\]

---

Desenvolvido como projeto acadêmico de desenvolvimento de jogos.