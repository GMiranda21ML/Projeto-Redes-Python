import socket
import os
import time
import hashlib

HOST  = "127.0.0.1"
PORTA = 8080

TIMEOUT_ACK    = 5.0   
MAX_TENTATIVAS = 5     

RESET   = "\033[0m"
NEGRITO = "\033[1m"
VERMELHO= "\033[1;31m"
VERDE   = "\033[1;32m"
ROXO    = "\033[1;35m"
AMARELO = "\033[1;33m"
AZUL    = "\033[1;34m"

def calcular_checksum(dados: str) -> str:
    return hashlib.sha256(dados.encode()).hexdigest()[:8]

def receberMensagem(conexao, timeout=None):
    if timeout is not None:
        conexao.settimeout(timeout)
    else:
        conexao.settimeout(None)
    dado = conexao.recv(4096).decode()
    conexao.settimeout(None)
    return dado

def enviarMensagem(mensagem, conexao):
    conexao.sendall((mensagem + "\n").encode())

def exibirCabecalho(host, porta):
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
    print(f"┃  {ROXO}ALVO: {host:<15}{RESET}  {ROXO}PORTA: {porta:<15}{RESET}      ┃")
    print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n")

def desenharMenu():
    os.system("cls" if os.name == "nt" else "clear")
    exibirCabecalho(HOST, PORTA)
    print("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print("┃                MENU DE COMUNICAÇÃO                  ┃")
    print("┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫")
    print("┃                                                     ┃")
    print(f"┃  {VERDE}[ 1 ]{RESET} Enviar mensagem ao servidor                  ┃")
    print(f"┃  {VERMELHO}[ 0 ]{RESET} Encerrar conexão e sair                      ┃")
    print("┃                                                     ┃")
    print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n")

def voltarMenu(seg=5):
    for i in range(seg, 0, -1):
        print(f"\rVoltando ao menu em {i}...", end="", flush=True)
        time.sleep(1)
    print()

def montar_pacote(seq: int, payload: str, simular_erro: bool = False) -> str:
    tamanho  = len(payload)
    conteudo = f"{seq}|{tamanho}|{payload}"
    checksum = calcular_checksum(conteudo)
    if simular_erro:
        checksum = checksum[:-2] + checksum[-2:][::-1]
    return f"{conteudo}|{checksum}"

def configurar_conexao():
    while True:
        print("\n--- Configuração Inicial da Conexão ---")
        print("[ 1 ] Go-Back-N (GBN)")
        print("[ 2 ] Repetição Seletiva (SR)")
        try:
            escolha = int(input("Escolha o protocolo (1 ou 2): "))
            if escolha == 1:
                protocolo = "GBN"
            elif escolha == 2:
                protocolo = "SR"
            else:
                print("Opção inválida!")
                continue
            break
        except ValueError:
            print("Digite um número inteiro.")

    while True:
        print("\n--- Modo de Confirmação (ACK) ---")
        print("[ 1 ] Individual (confirma cada pacote separadamente)")
        print("[ 2 ] Grupo      (confirma o lote inteiro ao final)")
        try:
            escolha = int(input("Escolha o modo (1 ou 2): "))
            if escolha == 1:
                modo_ack = "IND"
            elif escolha == 2:
                modo_ack = "GRP"
            else:
                print("Opção inválida!")
                continue
            break
        except ValueError:
            print("Digite um número inteiro.")

    return protocolo, modo_ack

def configurar_erro():
    print("\n--- Simulação de Erros (opcional) ---")
    resp = input("Deseja simular erro em algum pacote? (s/N): ").strip().lower()
    if resp != "s":
        return set()
    seqs_str = input("Informe os números de sequência com erro (ex: 2,5): ").strip()
    try:
        return {int(s) for s in seqs_str.split(",") if s.strip().isdigit()}
    except Exception:
        return set()

def parse_respostas(raw: str):
    linhas = [l.strip() for l in raw.split("\n") if l.strip()]
    tokens_finais = []
    for linha in linhas:
        tokens = linha.replace("ACK|", "\nACK|").replace("NAK|", "\nNAK|") \
                      .replace("ERRO|", "\nERRO|").strip().split("\n")
        tokens_finais.extend([t.strip() for t in tokens if t.strip()])
    return tokens_finais

def enviar_gbn(pacotes, janela, conexao, modo_ack, seqs_erro):
    base        = 0
    proximo_seq = 0
    n           = len(pacotes)

    while base < n:
        enviados_nesta_rodada = []
        while proximo_seq < base + janela and proximo_seq < n:
            seq_real    = proximo_seq + 1
            tem_erro    = seq_real in seqs_erro
            pacote_str  = montar_pacote(seq_real, pacotes[proximo_seq], simular_erro=tem_erro)
            enviarMensagem(pacote_str, conexao)
            time.sleep(0.05)
            tag = f"{VERMELHO}[ERRO SIMULADO]{RESET}" if tem_erro else ""
            print(f"  {AZUL}→ ENVIADO{RESET} seq={seq_real} payload='{pacotes[proximo_seq]}' {tag}")
            enviados_nesta_rodada.append(proximo_seq)
            proximo_seq += 1

        esperados    = proximo_seq - base
        confirmados  = 0
        retransmitir = False
        tentativas   = 0

        while confirmados < esperados and not retransmitir:
            if tentativas >= MAX_TENTATIVAS:
                print(f"  {VERMELHO}[ABORT]{RESET} Máximo de tentativas atingido.")
                return False
            try:
                raw = receberMensagem(conexao, timeout=TIMEOUT_ACK)
            except socket.timeout:
                print(f"  {AMARELO}[TIMEOUT]{RESET} Sem resposta. Retransmitindo janela (GBN)...")
                proximo_seq = base
                tentativas += 1
                retransmitir = True
                break

            # CORREÇÃO: Variável ack_bruto substituída por raw
            if raw and "ERRO|LIMITE" in raw:
                print(f"  {VERMELHO}[ERRO]{RESET} Servidor: limite de caracteres excedido.")
                return False

            tokens = parse_respostas(raw)
            for tok in tokens:
                tok = tok.strip()
                if not tok:
                    continue

                if tok.startswith("NAK|"):
                    seq_nak = tok.split("|")[1]
                    print(f"  {VERMELHO}[NAK]{RESET} Servidor pediu reenvio do seq={seq_nak}. Retransmitindo...")
                    proximo_seq  = base
                    retransmitir = True
                    tentativas  += 1
                    break

                if tok.startswith("ACK|"):
                    partes = tok.split("|")
                    if partes[1] == "FIM":
                        return True
                    seq_conf  = partes[1]
                    nova_jan  = int(partes[2]) if len(partes) > 2 else janela
                    if nova_jan != janela:
                        print(f"  {VERDE}[JANELA]{RESET} Servidor alterou janela: {janela} → {nova_jan}")
                        janela = nova_jan
                    print(f"  {VERDE}[ACK]{RESET} Confirmado seq={seq_conf} | janela={nova_jan}")
                    confirmados += 1

        if not retransmitir:
            base = proximo_seq

    return True

def enviar_sr(pacotes, janela, conexao, modo_ack, seqs_erro):
    n           = len(pacotes)
    base        = 0
    proximo_seq = 0
    confirmados = set()
    pendentes   = {}

    while len(confirmados) < n:
        while proximo_seq < base + janela and proximo_seq < n:
            if proximo_seq not in confirmados:
                seq_real   = proximo_seq + 1
                tem_erro   = seq_real in seqs_erro
                pacote_str = montar_pacote(seq_real, pacotes[proximo_seq], simular_erro=tem_erro)
                enviarMensagem(pacote_str, conexao)
                time.sleep(0.05)
                tag = f"{VERMELHO}[ERRO SIMULADO]{RESET}" if tem_erro else ""
                print(f"  {AZUL}→ ENVIADO{RESET} seq={seq_real} payload='{pacotes[proximo_seq]}' {tag}")
                pendentes[proximo_seq] = pendentes.get(proximo_seq, 0) + 1
            proximo_seq += 1

        try:
            raw = receberMensagem(conexao, timeout=TIMEOUT_ACK)
        except socket.timeout:
            print(f"  {AMARELO}[TIMEOUT SR]{RESET} Sem resposta. Reenviando pacotes pendentes...")
            proximo_seq = base
            continue

        # CORREÇÃO: Variável ack_bruto substituída por raw
        if raw and "ERRO|LIMITE" in raw:
            print(f"  {VERMELHO}[ERRO]{RESET} Servidor: limite de caracteres excedido.")
            return False

        tokens = parse_respostas(raw)
        for tok in tokens:
            tok = tok.strip()
            if not tok:
                continue

            if tok.startswith("NAK|"):
                seq_nak  = int(tok.split("|")[1]) - 1 
                tentativas_feitas = pendentes.get(seq_nak, 0)
                if tentativas_feitas >= MAX_TENTATIVAS:
                    print(f"  {VERMELHO}[ABORT SR]{RESET} Máximo de tentativas para seq={seq_nak+1}.")
                    return False
                seq_real   = seq_nak + 1
                tem_erro   = seq_real in seqs_erro
                pacote_str = montar_pacote(seq_real, pacotes[seq_nak], simular_erro=tem_erro)
                enviarMensagem(pacote_str, conexao)
                time.sleep(0.05)
                tag = f"{VERMELHO}[REENVIO c/ ERRO]{RESET}" if tem_erro else f"{AMARELO}[REENVIO]{RESET}"
                print(f"  {tag} seq={seq_real} payload='{pacotes[seq_nak]}'")
                pendentes[seq_nak] = tentativas_feitas + 1
                continue

            if tok.startswith("ACK|"):
                partes = tok.split("|")
                if partes[1] == "FIM":
                    return True
                seq_conf  = int(partes[1]) - 1
                nova_jan  = int(partes[2]) if len(partes) > 2 else janela
                if nova_jan != janela:
                    print(f"  {VERDE}[JANELA]{RESET} Servidor alterou janela: {janela} → {nova_jan}")
                    janela = nova_jan
                confirmados.add(seq_conf)
                print(f"  {VERDE}[ACK]{RESET} Confirmado seq={seq_conf+1} | janela={nova_jan}")
                while base in confirmados:
                    base += 1

    return True

def enviar_mensagem_completa(conexao, protocolo, modo_ack, janela):
    while True:
        try:
            tamanho = int(input("Digite o tamanho máximo da mensagem (mín. 30): "))
            break
        except ValueError:
            print("Digite um número inteiro.")

    enviarMensagem(str(tamanho), conexao)
    retorno = receberMensagem(conexao).strip()
    if retorno != "OK":
        print(f"{VERMELHO}{retorno}{RESET}")
        voltarMenu()
        return janela

    mensagem = input("Digite a mensagem a ser enviada: ")
    if not mensagem:
        print("Mensagem vazia. Cancelando.")
        voltarMenu(2)
        return janela

    chunks = [mensagem[i:i+4] for i in range(0, len(mensagem), 4)]
    print(f"\n{NEGRITO}Mensagem fragmentada em {len(chunks)} pacote(s).{RESET}")

    seqs_erro = configurar_erro()

    print(f"\n{NEGRITO}--- Iniciando envio "
          f"(Protocolo: {protocolo} | ACK: {modo_ack} | Janela: {janela}) ---{RESET}")

    if protocolo == "GBN":
        sucesso = enviar_gbn(chunks, janela, conexao, modo_ack, seqs_erro)
    else:
        sucesso = enviar_sr(chunks, janela, conexao, modo_ack, seqs_erro)

    if sucesso:
        enviarMensagem("FIM|0|", conexao)
        ack_final = receberMensagem(conexao).strip()
        print(f"\n{VERDE}[METADADO]{RESET} Fim da transmissão: {ack_final}")

        status = receberMensagem(conexao).strip()
        if status != "OK":
            print(f"{VERMELHO}{status}{RESET}")

    voltarMenu()
    return janela

def main():
    protocolo, modo_ack = configurar_conexao()

    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((HOST, PORTA))
    except Exception as e:
        print(f"{VERMELHO}Erro ao conectar: {e}{RESET}")
        return

    enviarMensagem(f"CONFIG|{protocolo}|{modo_ack}", cliente)
    resposta = receberMensagem(cliente)

    if not resposta.startswith("OK_CONFIG|"):
        print(f"{VERMELHO}Erro na configuração do servidor.{RESET}")
        cliente.close()
        return

    janela = int(resposta.split("|")[1])
    print(f"\n{VERDE}[SISTEMA]{RESET} Conectado! Janela inicial definida pelo servidor: {janela}")

    try:
        while True:
            desenharMenu()
            try:
                op = int(input(f"\033[1;34mSelecione uma opção > \033[0m"))
            except ValueError:
                print("Digite um número inteiro.")
                voltarMenu(2)
                continue

            if op == 0:
                enviarMensagem("0", cliente)
                break
            elif op == 1:
                janela = enviar_mensagem_completa(cliente, protocolo, modo_ack, janela)
            else:
                print("Opção inválida!")
                voltarMenu(2)
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")
    finally:
        cliente.close()

if __name__ == "__main__":
    main()