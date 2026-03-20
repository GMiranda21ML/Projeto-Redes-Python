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
    os.system("clear")

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
    for i in range(3, 0, -1):
        print(f"\rVoltando ao menu em {i}...", end="", flush=True)
        time.sleep(1)


# host = input("Digite o host do servidor (EX.: 127.0.0.1): ")
# porta = int(input("Digite a porta do servidor: "))

os.system("clear")
try:
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PORTA))
    # cliente.connect((host, porta))

    enviarMensagem("Olá, servidor!", cliente)

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
            if not "OK" in retorno:
                print(retorno)
                voltarMenu()
                continue

            mensagem = input("Mande alguma mensagem para o servidor: ")
            enviarMensagem(mensagem, cliente)
        else:
            print("Opção invalida! Por favor, digite novamente")

except Exception as e:
    print(f"Erro ao estabelecer conexão: {e}")

cliente.close()
