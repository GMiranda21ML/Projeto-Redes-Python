import socket
import os
import time

HOST = "127.0.0.1"
PORTA = 8080


def receberMensagem(conexao):
    return conexao.recv(1024).decode()


def enviarMensagem(mensagem, conexao):
    conexao.sendall(mensagem.encode())


def titulo():
    print("""
                                                                  
 _____     _                 _      _____           _         _   
|   | |___| |_ _ _ _ ___ ___| |_   |  _  |___ ___  |_|___ ___| |_ 
| | | | -_|  _| | | | . |  _| '_|  |   __|  _| . | | | -_|  _|  _|
|_|___|___|_| |_____|___|_| |_,_|  |__|  |_| |___|_| |___|___|_|  
                                                 |___|            
""")


def desenharMenu():
    os.system("cls" if os.name == "nt" else "clear")

    titulo()

    print("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print("┃                 MENU DE COMUNICAÇÃO                 ┃")
    print("┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫")
    print("┃                                                     ┃")
    print("┃  \033[1;32m[ 1 ]\033[0m Enviar uma nova mensagem ao servidor         ┃")
    print("┃  \033[1;31m[ 0 ]\033[0m Encerrar conexão e sair                      ┃")
    print("┃                                                     ┃")
    print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
    print("\n")


def voltarMenu():
    for i in range(5, 0, -1):
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
        op = int(input("\033[1;34mSelecione uma opção > \033[0m"))

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
