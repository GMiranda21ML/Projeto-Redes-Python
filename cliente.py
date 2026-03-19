import socket

HOST = "127.0.0.1"
PORTA = 8080

def receberMensagem(conexao):
    return conexao.recv(1024).decode()

def enviarMensagem(mensagem, conexao):
    conexao.sendall(mensagem.encode())

# host = input("Digite o host do servidor (EX.: 127.0.0.1): ")
# porta = int(input("Digite a porta do servidor: "))

try:
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PORTA))
    # cliente.connect((host, porta))

    enviarMensagem("Olá, servidor!", cliente)

    mensagem = input("Mande alguma mensagem para o servidor: ")
    enviarMensagem(mensagem, cliente)

except:
    print("Erro ao estabelecer conexão")

cliente.close()