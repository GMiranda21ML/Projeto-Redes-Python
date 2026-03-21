import socket
import os
import time

HOST = "127.0.0.1"
PORTA = 8080

RESET = "\033[0m"
NEGRITO = "\033[1m"
VERMELHO = "\033[1;31m"
VERDE = "\033[1;32m"
ROXO = "\033[1;35m"


def receberMensagem(conexao):
    return conexao.recv(1024).decode()


def enviarMensagem(mensagem, conexao):
    conexao.sendall(mensagem.encode())


def exibirCabecalho():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"{ROXO}{NEGRITO}")
    print("   ________    _____________________________")
    print("  / ____/ /   /  _/ ____/ | / /_  __/ ____/")
    print(" / /   / /    / // __/ /  |/ / / / / __/   ")
    print("/ /___/ /____/ // /___/ /|  / / / / /___   ")
    print("\\____/_____/___/_____/_/ |_/ /_/ /_____/   ")
    print(f"{RESET}")
    print("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print(f"┃  {VERDE}STATUS: Conectado, Aguardando Comandos{RESET}             ┃")
    print(f"┃  {ROXO}ALVO: {HOST:<15}{RESET}  {ROXO}PORTA: {PORTA:<15}{RESET}      ┃")
    print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n")


def desenharMenu():
    os.system("cls" if os.name == "nt" else "clear")

    exibirCabecalho()

    print("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print("┃                 MENU DE COMUNICAÇÃO                 ┃")
    print("┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫")
    print("┃                                                     ┃")
    print(f"┃  {VERDE}[ 1 ]{RESET} Enviar uma nova mensagem ao servidor         ┃")
    print(f"┃  {VERMELHO}[ 0 ]{RESET} Encerrar conexão e sair                      ┃")
    print("┃                                                     ┃")
    print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
    print("\n")


def voltarMenu(seg=5):
    for i in range(seg, 0, -1):
        print(f"\rVoltando ao menu em {i}...", end="", flush=True)
        time.sleep(1)


# host = input("Digite o host do servidor (EX.: 127.0.0.1): ")
# porta = int(input("Digite a porta do servidor: "))

try:
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PORTA))
    # cliente.connect((host, porta))

    while True:
        desenharMenu()
        # op = int(input("Digite a sua opção: "))
        try:
            op = int(input("\033[1;34mSelecione uma opção > \033[0m"))
        except Exception as e:
            print(f"Erro, digite um número inteiro: {e}")
            voltarMenu(3)
            continue

        if op == 0:
            enviarMensagem("0", cliente)
            cliente.close()
            break
        elif op == 1:
            tamanho = int(input("Digite o tamanho da mensagem: "))
            enviarMensagem(str(tamanho), cliente)
            retorno = receberMensagem(cliente)

            if retorno != "OK":
                print(retorno)
                voltarMenu()
                continue

            mensagem = input("Mande alguma mensagem para o servidor: ")

            print("\n--- A enviar pacotes ---")
            seq = 1
            for i in range(0, len(mensagem), 4):
                pedaco = mensagem[i : i + 4]

                pacote = f"{seq}|{len(pedaco)}|{pedaco}"

                enviarMensagem(pacote, cliente)

                ack = receberMensagem(cliente)

                print(f"[METADADO] Confirmação recebida do servidor: {ack}")

                seq += 1

            enviarMensagem("FIM|0|", cliente)
            ackFinal = receberMensagem(cliente)
            print(f"[METADADO] Fim da transmissão: {ackFinal}\n")

            statusTamanho = receberMensagem(cliente)
            if statusTamanho != "OK":
                print(statusTamanho)

            voltarMenu()

        else:
            print("Opção invalida! Por favor, digite novamente")

except Exception as e:
    print(f"Erro ao estabelecer conexão: {e}")

cliente.close()
