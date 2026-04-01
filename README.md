# Projeto de Redes com Python (Cliente-Servidor via Socket)

## Descrição

Este projeto implementa uma aplicação de comunicação entre cliente e servidor utilizando sockets em Python. A proposta é demonstrar, na prática, conceitos fundamentais de redes de computadores, como conexão, troca de dados e sincronização entre aplicações.

Antes da troca de mensagens, é realizado um handshake inicial entre cliente e servidor, no qual são definidos parâmetros importantes da comunicação.

## Objetivo

- Implementar comunicação via sockets em Python
- Aplicar o modelo cliente-servidor
- Realizar handshake inicial entre as aplicações
- Controlar o envio de dados com base em parâmetros definidos

## Handshake

No início da conexão, cliente e servidor trocam informações para definir:
- Modo de operação
- Tamanho máximo das mensagens

Esse processo garante que ambos operem com as mesmas regras durante a comunicação.

## Tecnologias utilizadas

- Python 3
- Biblioteca socket (nativa do Python)

## Estrutura do projeto

```
Projeto-Redes-Python/
│
├── cliente.py
├── servidor.py
└── README.md
```

## Como executar

### Pré-requisitos

- Python 3 instalado

### Passo a passo

1. Clone o repositório:

```
git clone https://github.com/GMiranda21ML/Projeto-Redes-Python.git
cd Projeto-Redes-Python
```

2. Execute o servidor:

```
python servidor.py
```

O servidor ficará aguardando conexões.

3. Em outro terminal, execute o cliente:

```
python cliente.py
```

4. Utilize o sistema conforme as opções disponíveis no terminal.

## Funcionamento

Fluxo básico da aplicação:

```
Cliente conecta ao servidor
Handshake (modo de operação e tamanho máximo)
Comunicação entre cliente e servidor
Encerramento da conexão
```

## Uso de Inteligência Artificial

Foi utilizada Inteligência Artificial de forma auxiliar durante o desenvolvimento, especificamente para:
- Organização do menu da aplicação
- Correção de pequenos erros no código
- Sugestões de melhoria na legibilidade

A lógica principal da aplicação, incluindo a implementação da comunicação via socket e do handshake, foi desenvolvida pelo grupo.

## Considerações finais

O projeto tem como foco a aplicação prática dos conceitos de redes, especialmente comunicação cliente-servidor e uso de sockets, servindo como base para sistemas distribuídos mais complexos.
