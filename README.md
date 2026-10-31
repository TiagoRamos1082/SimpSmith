# ⚒️ SimpSmith

SimpSmith é um jogo de simulação e crafting em pixel art 2D, desenvolvido em Python utilizando a biblioteca Pygame.

O jogador assume o papel de um jovem ferreiro que herda uma pequena oficina após a morte de seu mestre. Sem recursos financeiros, prestígio ou equipamentos avançados, deverá reconstruir o negócio por meio da exploração, coleta de recursos, produção de itens e administração da oficina.

## Sobre o projeto

O jogo apresenta mecânicas de exploração, coleta de recursos, gerenciamento de inventário e criação de itens por meio de um sistema de crafting.

O jogador pode explorar o mapa, coletar minérios e plantas, armazenar recursos e utilizar ingredientes para produzir materiais e novos itens.

O projeto utiliza uma arquitetura modular, separando as responsabilidades em diferentes sistemas e diretórios.

## Conceito do jogo

A experiência de SimpSmith gira em torno de um ciclo de exploração, produção, comércio e evolução.

Cada melhoria conquistada permite fabricar itens mais sofisticados, acessar novas regiões e aumentar a reputação da oficina dentro do reino.

Em vez de utilizar combates como principal forma de evolução, o jogo coloca a administração eficiente de recursos e a tomada de decisões econômicas no centro da experiência.

### Diferencial

O projeto busca integrar conceitos matemáticos diretamente às mecânicas do jogo, sem interromper a experiência com exercícios ou questionários.

Esses conceitos aparecem em atividades como:

- Divisão de barras metálicas em frações para fabricar equipamentos.
- Cálculo de porcentagens de qualidade durante a produção.
- Administração de custos e lucros da oficina.
- Análise da variação de preços para decidir quando vender.
- Investimento de recursos limitados.
- Gerenciamento do espaço de armazenamento.
- Otimização do uso de matérias-primas.

## Tecnologias utilizadas

- Python 3.13
- Pygame 2.6.1
- JSON para armazenamento de dados do jogo.
- Git e GitHub para versionamento.

## Requisitos

Antes de executar o projeto, é necessário ter instalado:

- Python 3.13
- pip
- Git (caso queira clonar o repositório).

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/TiagoRamos1082/SimpSmith.git
```

Entre na pasta do projeto:

```bash
cd SimpSmith
```

Também é possível baixar o projeto pelo GitHub, utilizando a opção **Code > Download ZIP**.

### 2. Criar o ambiente virtual

Na raiz do projeto, execute:

```bash
python -m venv venv
```

### 3. Ativar o ambiente virtual

No Windows, utilizando PowerShell:

```powershell
.\\venv\\Scripts\\Activate.ps1
```

**Problema: execução de scripts desabilitada**

Caso o PowerShell apresente uma mensagem informando que a execução de scripts está desabilitada, execute:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Confirme a alteração quando solicitado e tente ativar novamente:

```powershell
.\\venv\\Scripts\\Activate.ps1
```

Essa configuração permite executar scripts locais para o usuário atual do Windows.

No Linux ou macOS, utilize:

```bash
source venv/bin/activate
```

### 4. Instalar as dependências

Com o ambiente virtual ativado:

```bash
python -m pip install -r docs/requirements.txt
```

### 5. Executar o jogo

Na raiz do projeto:

```bash
python main.py
```

## Controles

| Ação | Tecla |
|---|---|
| Movimentar para cima | W |
| Movimentar para baixo | S |
| Movimentar para esquerda | A |
| Movimentar para direita | D |
| Interagir e coletar recursos | E |
| Abrir ou fechar inventário | I |
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

O sistema também controla a quantidade de itens, o limite de pilhas e a capacidade de peso do personagem.

### Crafting

Permite utilizar ingredientes para produzir novos materiais e itens. As receitas são definidas em arquivos JSON.

### Progressão

A progressão está relacionada à exploração, coleta de recursos e utilização dos ingredientes disponíveis para produzir novos elementos.

As condições de vitória e derrota dependem das funcionalidades implementadas na versão atual.

## Estrutura do projeto

```text
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

| Diretório/Arquivo | Responsabilidade |
|---|---|
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

- [Arquitetura](docs/arquitetura.md): organização e arquitetura do projeto.
- [Instalação e execução](docs/instalacao-e-execucao.md): orientações de instalação e execução.
- [Mapa e colisões](docs/mapa-e-colisoes.md): funcionamento do mapa e das colisões.
- [Editor de colisões](docs/edtor-de-colisoes.md): documentação do editor de colisões.

## Game Design Document (GDD)

O GDD apresenta a proposta do jogo, suas mecânicas, regras, objetivos e características de design.

**Localização:** inserir o caminho ou link do GDD atualizado.

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

GitHub: [TiagoRamos1082/SimpSmith](https://github.com/TiagoRamos1082/SimpSmith)

---

Desenvolvido como projeto acadêmico de desenvolvimento de jogos.
