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

while True:    
    print("\n--- Configuração Inicial da Conexão ---")
    print("[ 1 ] Go-Back-N (GBN)")
    print("[ 2 ] Repetição Seletiva (SR)")
    try:
        escolhaProt = int(input("Escolha o protocolo (1 ou 2): "))
        if escolhaProt == 1:
            protocolo = "GBN"
        elif escolhaProt == 2:
            protocolo = "SR"
        else:
            os.system("cls" if os.name == "nt" else "clear")
            print("Opção invalida! Por favor, digite novamente")
            continue
        break
    except Exception as e:
        os.system("cls" if os.name == "nt" else "clear")
        print(f"Erro, digite um número inteiro: {e}")
        continue

try:
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PORTA))
    # cliente.connect((host, porta))

    enviarMensagem(f"CONFIG|{protocolo}", cliente)

    respostaConfig = receberMensagem(cliente)
    if respostaConfig.startswith("OK_CONFIG|"):
        tamanhoJanela = int(respostaConfig.split("|")[1])
        print(f"\n[SISTEMA] Conectado! O servidor definiu a janela inicial para: {tamanhoJanela}")
    else:
        print("Erro ao configurar a conexão com o servidor.")
        cliente.close()
        exit()
    
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

            pacotes = []
            seq = 1
            for i in range(0, len(mensagem), 4):
                pedaco = mensagem[i : i + 4]
                pacotes.append(f"{seq}|{len(pedaco)}|{pedaco}")
                seq += 1
            
            base = 0
            proximoSeq = 0
            houveErro = False
            
            while base < len(pacotes):
                print(f"\n--- Enviando lote (Modo: {protocolo}, Janela Atual: {tamanhoJanela}) ---")


                while proximoSeq < base + tamanhoJanela and proximoSeq < len(pacotes):
                    enviarMensagem(pacotes[proximoSeq], cliente)
                    time.sleep(0.05)
                    proximoSeq += 1

                pacotesEsperadosAck = proximoSeq - base
                acksRecebidos = 0
                
                while acksRecebidos < pacotesEsperadosAck:
                    ackBruto = receberMensagem(cliente)
                    
                    listaAcks = ackBruto.replace("ACK|", " ACK|").replace("ERRO|", " ERRO|").split()
                    
                    for ack in listaAcks:
                        if ack == "ERRO|LIMITE":
                            print(f"\n[ERRO] O servidor interrompeu a conexão: Limite excedido!")
                            houveErro = True
                            break
                            
                        if ack.startswith("ACK|"):
                            partesAck = ack.split("|")
                            if len(partesAck) == 3:
                                seqConfirmado = partesAck[1]
                                novaJanela = int(partesAck[2])
                                
                                if novaJanela != tamanhoJanela:
                                    tamanhoJanela = novaJanela
                                    print(f"[SISTEMA] O servidor alterou o tamanho da janela para: {tamanhoJanela}")
                                    
                            print(f"[METADADO] Confirmação processada: {ack}")
                            acksRecebidos += 1
                
                if houveErro:
                    break
                    
                base = proximoSeq

            if not houveErro:
                enviarMensagem("FIM|0|", cliente)
                ackFinal = receberMensagem(cliente)
                print(f"[METADADO] Fim da transmissão: {ackFinal}\n")

                statusTamanho = receberMensagem(cliente)
                if statusTamanho != "OK":
                    print(statusTamanho)

            voltarMenu()

        else:
            print("Opção invalida! Por favor, digite novamente")
            voltarMenu(2)

except Exception as e:
    print(f"Erro ao estabelecer conexão: {e}")

cliente.close()
