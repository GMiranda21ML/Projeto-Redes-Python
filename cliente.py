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

    linha = b""
    while True:
        byte = conexao.recv(1)
        if not byte:
            break
        if byte == b"\n":
            break
        linha += byte
    conexao.settimeout(None)
    return linha.decode()

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

def voltarMenu(seg=None):
    input("\nPressione ENTER para voltar ao menu...")

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
        print("[ 1 ] Go-Back-N (GBN)         → ACK em grupo (cumulativo)")
        print("[ 2 ] Repetição Seletiva (SR) → ACK individual")
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

    modo_ack = "GRP" if protocolo == "GBN" else "IND"

    while True:
        print("\n--- Criptografia (XOR simétrico) ---")
        print("[ 1 ] Sem criptografia")
        print("[ 2 ] Com criptografia (XOR)")
        try:
            escolha = int(input("Escolha (1 ou 2): "))
            if escolha == 1:
                usa_cripto = "NAO"
            elif escolha == 2:
                usa_cripto = "SIM"
            else:
                print("Opção inválida!")
                continue
            break
        except ValueError:
            print("Digite um número inteiro.")

    return protocolo, modo_ack, usa_cripto

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

def enviar_gbn(pacotes, janela, conexao, modo_ack, seqs_erro, chave=None):
    base        = 0
    proximo_seq = 0
    n           = len(pacotes)

    seqs_erro_usados = set()

    tentativas = 0

    while base < n:
        enviados_nesta_rodada = []
        while proximo_seq < base + janela and proximo_seq < n:
            seq_real   = proximo_seq + 1
            tem_erro   = (seq_real in seqs_erro) and (seq_real not in seqs_erro_usados)
            pacote_str = montar_pacote(seq_real, pacotes[proximo_seq], simular_erro=tem_erro)
            if tem_erro:
                seqs_erro_usados.add(seq_real)
            enviarMensagemCripto(pacote_str, conexao, chave)
            time.sleep(0.05)
            tag = f"{VERMELHO}[ERRO SIMULADO]{RESET}" if tem_erro else ""
            print(f"  {AZUL}→ ENVIADO{RESET} seq={seq_real} payload='{pacotes[proximo_seq]}' {tag}")
            enviados_nesta_rodada.append(proximo_seq)
            proximo_seq += 1

        esperados    = 1 if modo_ack == "GRP" else (proximo_seq - base)
        confirmados  = 0
        retransmitir = False

        while confirmados < esperados and not retransmitir:
            if tentativas >= MAX_TENTATIVAS:
                print(f"  {VERMELHO}[ABORT]{RESET} Máximo de tentativas atingido.")
                return False
            try:
                raw = receberMensagemCripto(conexao, chave, timeout=TIMEOUT_ACK)
            except socket.timeout:
                print(f"  {AMARELO}[TIMEOUT]{RESET} Sem resposta. Retransmitindo janela (GBN)...")
                proximo_seq  = base
                tentativas  += 1
                retransmitir = True
                break

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
            base       = proximo_seq
            tentativas = 0   

    return True

def enviar_sr(pacotes, janela, conexao, modo_ack, seqs_erro, chave=None):
    n           = len(pacotes)
    base        = 0
    proximo_seq = 0
    confirmados = set()
    pendentes   = {}

    seqs_erro_usados = set()

    while len(confirmados) < n:
        while proximo_seq < base + janela and proximo_seq < n:
            if proximo_seq not in confirmados:
                seq_real  = proximo_seq + 1

                tem_erro  = (seq_real in seqs_erro) and (seq_real not in seqs_erro_usados)
                pacote_str = montar_pacote(seq_real, pacotes[proximo_seq], simular_erro=tem_erro)
                if tem_erro:
                    seqs_erro_usados.add(seq_real)
                enviarMensagemCripto(pacote_str, conexao, chave)
                time.sleep(0.05)
                tag = f"{VERMELHO}[ERRO SIMULADO]{RESET}" if tem_erro else ""
                print(f"  {AZUL}→ ENVIADO{RESET} seq={seq_real} payload='{pacotes[proximo_seq]}' {tag}")
                pendentes[proximo_seq] = pendentes.get(proximo_seq, 0) + 1
            proximo_seq += 1

        try:
            raw = receberMensagemCripto(conexao, chave, timeout=TIMEOUT_ACK)
        except socket.timeout:

            print(f"  {AMARELO}[TIMEOUT SR]{RESET} Sem resposta. Reenviando pacotes não confirmados...")
            for idx in range(base, min(base + janela, n)):
                if idx not in confirmados:
                    seq_real   = idx + 1
                    tentativas_feitas = pendentes.get(idx, 0)
                    if tentativas_feitas >= MAX_TENTATIVAS:
                        print(f"  {VERMELHO}[ABORT SR]{RESET} Máximo de tentativas para seq={seq_real}.")
                        return False

                    pacote_str = montar_pacote(seq_real, pacotes[idx], simular_erro=False)
                    enviarMensagemCripto(pacote_str, conexao, chave)
                    time.sleep(0.05)
                    print(f"  {AMARELO}[REENVIO TIMEOUT]{RESET} seq={seq_real} payload='{pacotes[idx]}'")
                    pendentes[idx] = tentativas_feitas + 1

            continue

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
                pacote_str = montar_pacote(seq_real, pacotes[seq_nak], simular_erro=False)
                enviarMensagemCripto(pacote_str, conexao, chave)
                time.sleep(0.05)
                print(f"  {AMARELO}[REENVIO]{RESET} seq={seq_real} payload='{pacotes[seq_nak]}'")
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

def _xor_cifrar(texto: str, chave: bytes) -> str:
    dados = texto.encode("utf-8")
    return bytes([b ^ chave[i % len(chave)] for i, b in enumerate(dados)]).hex()

def _xor_decifrar(hex_str: str, chave: bytes) -> str:
    cifrado = bytes.fromhex(hex_str)
    return bytes([b ^ chave[i % len(chave)] for i, b in enumerate(cifrado)]).decode("utf-8")

def enviarMensagemCripto(mensagem, conexao, chave):
    if chave:
        mensagem = _xor_cifrar(mensagem, chave)
    enviarMensagem(mensagem, conexao)

def receberMensagemCripto(conexao, chave, timeout=None):
    raw = receberMensagem(conexao, timeout=timeout).strip()
    if chave and raw:
        try:
            return _xor_decifrar(raw, chave)
        except Exception:
            return raw
    return raw

def enviar_mensagem_completa(conexao, protocolo, modo_ack, janela, chave=None):
    while True:
        try:
            tamanho = int(input("Digite o tamanho máximo da mensagem (mín. 30): "))
            break
        except ValueError:
            print("Digite um número inteiro.")

    enviarMensagemCripto(str(tamanho), conexao, chave)
    retorno = receberMensagemCripto(conexao, chave).strip()
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
        sucesso = enviar_gbn(chunks, janela, conexao, modo_ack, seqs_erro, chave)
    else:
        sucesso = enviar_sr(chunks, janela, conexao, modo_ack, seqs_erro, chave)

    if sucesso:
        enviarMensagemCripto("FIM|0|", conexao, chave)
        ack_final = receberMensagemCripto(conexao, chave).strip()
        print(f"\n{VERDE}[METADADO]{RESET} Fim da transmissão: {ack_final}")

        status = receberMensagemCripto(conexao, chave).strip()
        if status != "OK":
            print(f"{VERMELHO}{status}{RESET}")

    voltarMenu()
    return janela

def main():
    protocolo, modo_ack, usa_cripto = configurar_conexao()

    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((HOST, PORTA))
    except Exception as e:
        print(f"{VERMELHO}Erro ao conectar: {e}{RESET}")
        return

    enviarMensagem(f"CONFIG|{protocolo}|{modo_ack}|{usa_cripto}", cliente)
    resposta = receberMensagem(cliente)

    if not resposta.startswith("OK_CONFIG|"):
        print(f"{VERMELHO}Erro na configuração do servidor.{RESET}")
        cliente.close()
        return

    janela = int(resposta.split("|")[1])
    print(f"\n{VERDE}[SISTEMA]{RESET} Conectado! Janela inicial definida pelo servidor: {janela}")

    SENHA_COMPARTILHADA = "redes2026"
    chave = None
    if usa_cripto == "SIM":
        import hashlib as _hl
        chave = _hl.sha256(SENHA_COMPARTILHADA.encode()).digest()
        hello_cifrado = ''.join(format(b ^ chave[i % len(chave)], '02x')
                                for i, b in enumerate("HELLO".encode()))
        enviarMensagem(hello_cifrado, cliente)
        hello_ok = receberMensagem(cliente).strip()
        try:
            raw = bytes.fromhex(hello_ok)
            resp_dec = bytes([b ^ chave[i % len(chave)] for i, b in enumerate(raw)]).decode()
        except Exception:
            resp_dec = hello_ok
        if resp_dec == "HELLO_OK":
            print(f"\n{VERDE}[CRIPTO]{RESET} Canal criptografado ativo.")
        else:
            print(f"\n{VERMELHO}[CRIPTO]{RESET} Falha no handshake. Continuando sem criptografia.")
            chave = None

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
                janela = enviar_mensagem_completa(cliente, protocolo, modo_ack, janela, chave)
            else:
                print("Opção inválida!")
                voltarMenu(2)
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")
    finally:
        cliente.close()

if __name__ == "__main__":
    main()