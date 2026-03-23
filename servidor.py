import socket
import os
import time

HOST = "127.0.0.1"
PORTA = 8080


RESET = "\033[0m"
NEGRITO = "\033[1m"
VERDE = "\033[1;32m"
AZUL = "\033[1;34m"
CIANO = "\033[1;36m"


def exibirCabecalho():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"{AZUL}{NEGRITO}")
    print("   _____ ______________    ____________  ____  ____")
    print("  / ___// ____/ __ \\| |  / /  _/ __ \\/ __ \\/ __ \\")
    print("  \\__ \\/ __/ / /_/ /| | / // // / / / / / / /_/ /")
    print(" ___/ / /___/ _, _/ | |/ // // /_/ / /_/ / _, _/ ")
    print("/____/_____/_/ |_|  |___/___/_____/\\____/_/ |_|  ")
    print(f"{RESET}")
    print("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print(f"┃  {VERDE}STATUS: Ativo e Operante{RESET}                           ┃")
    print(f"┃  {CIANO}HOST: {HOST:<15}{RESET}  {CIANO}PORTA: {PORTA:<15}{RESET}      ┃")
    print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n")
    print(f"Servidor aguardando conexão em {HOST}:{PORTA}")


def receberMensagem(conexao):
    return conexao.recv(1024).decode()


def enviarMensagem(mensagem, conexao):
    conexao.sendall(mensagem.encode())


def pegarTempo():
    return time.ctime()


def limparTerminal():
    os.system("cls" if os.name == "nt" else "clear")


def tempoVoltar():
    for i in range(3, 0, -1):
        print(f"\rLimpando dados, voltando em {i}...", end="", flush=True)
        time.sleep(1)


def exibirTempoEndereco(endereco):
    print(pegarTempo())
    print(f"Conectado por {endereco}")


limparTerminal()

exibirCabecalho()

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind((HOST, PORTA))
servidor.listen()

conexao, endereco = servidor.accept()

exibirTempoEndereco(endereco)

while True:
    data = conexao.recv(1024)

    if not data or data.decode() == "0":
        print("Cliente desconectou")
        print("Aguardando nova conexão...")
        tempoVoltar()
        limparTerminal()
        exibirCabecalho()
        conexao, endereco = servidor.accept()
        exibirTempoEndereco(endereco)
        continue

    mensagem = data.decode()

    if mensagem.isdigit():
        tamanho = int(mensagem)

        if tamanho < 30:
            enviarMensagem("ERRO: O tamanho minimo é de 30 caracteres", conexao)
            continue

        enviarMensagem("OK", conexao)

        mensagemCompleta = ""
        tamanhoAcumulado = 0
        print("\n--- A receber novos pacotes ---")

        while True:
            dadosPacote = receberMensagem(conexao)

            if not dadosPacote:
                print("Cliente desconectou inesperadamente.")
                break

            partes = dadosPacote.split("|", 2)

            if partes[0] == "FIM":
                enviarMensagem("ACK|FIM", conexao)
                break

            seq = partes[0]
            tamanhoPayload = int(partes[1])
            payload = partes[2]

            tamanhoAcumulado += tamanhoPayload

            if tamanhoAcumulado > tamanho:
                enviarMensagem("ERRO|LIMITE", conexao)
                print(
                    f"[ERRO] A mensagem ultrapassou o limite de {tamanho} caracteres. Abortando recebimento."
                )
                break

            print(
                f"[{pegarTempo()}] [METADADO] Pacote Seq: {seq} | Tamanho recebido: {tamanhoPayload} bytes | Payload: {payload}"
            )

            mensagemCompleta += payload

            enviarMensagem(f"ACK|{seq}", conexao)

        if tamanhoAcumulado <= tamanho:
            enviarMensagem("OK", conexao)
            print(f"\n[COMUNICAÇÃO COMPLETA] O cliente enviou: {mensagemCompleta}")


print("Encerrando Servidor")
conexao.close()
servidor.close()
