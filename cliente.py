import socket
import os

HOST = "127.0.0.1"
PORTA = 8080


def receberMensagem(conexao):
    return conexao.recv(1024).decode()


def enviarMensagem(mensagem, conexao):
    conexao.sendall(mensagem.encode())


def desenharMenu():
    print("""
Digite 1 para mandar mensagem
Digite 0 para encerrar a comunicação
    """)


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
        op = int(input("Digite a sua opção: "))

        if op == 0:
            enviarMensagem("0", cliente)
            cliente.close()
            break
        elif op == 1:
            mensagem = input("Mande alguma mensagem para o servidor: ")
            enviarMensagem(mensagem, cliente)
        else:
            print("Opção invalida! Por favor, digite novamente")

except Exception as e:
    print(f"Erro ao estabelecer conexão: {e}")

cliente.close()
