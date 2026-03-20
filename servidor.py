import socket
import os

HOST = "127.0.0.1"
PORTA = 8080


def receberMensagem(conexao):
    return conexao.recv(1024).decode()


def enviarMensagem(mensagem, conexao):
    conexao.sendall(mensagem.encode())


os.system("clear")

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((HOST, PORTA))
servidor.listen()

print(f"Servidor aguardando conexão em {HOST}:{PORTA}")

conexao, endereco = servidor.accept()
print(f"Conectado por {endereco}")

while True:
    data = conexao.recv(1024)

    if not data or data.decode() == "0":
        print("Cliente desconectou")
        break

    mensagem = data.decode()

    if mensagem == "Olá, servidor!":
        print(f"Mensagem do Cliente: {mensagem}")
        continue

    if mensagem.isdigit():
        tamanho = int(mensagem)

        if tamanho < 30:
            enviarMensagem("ERRO: O tamanho minimo é de 30 caracteres", conexao)
            continue

        enviarMensagem("OK", conexao)
        novaMensagem = receberMensagem(conexao)

        print(f"O cliente enviou: {novaMensagem}")


print("Encerrando Servidor")
conexao.close()
servidor.close()
