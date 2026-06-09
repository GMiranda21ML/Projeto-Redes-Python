import socket
import os
import time
import random
import hashlib

HOST  = "0.0.0.0"
PORTA = 8080

RESET   = "\033[0m"
NEGRITO = "\033[1m"
VERDE   = "\033[1;32m"
AZUL    = "\033[1;34m"
CIANO   = "\033[1;36m"
AMARELO = "\033[1;33m"
VERMELHO= "\033[1;31m"

def derivar_chave(senha: str) -> bytes:
    return hashlib.sha256(senha.encode()).digest()

def cripto_xor(texto: str, chave: bytes) -> str:
    dados = texto.encode("utf-8")
    cifrado = bytes([b ^ chave[i % len(chave)] for i, b in enumerate(dados)])
    return cifrado.hex()

def decripto_xor(hex_str: str, chave: bytes) -> str:
    cifrado = bytes.fromhex(hex_str)
    dados = bytes([b ^ chave[i % len(chave)] for i, b in enumerate(cifrado)])
    return dados.decode("utf-8")

def calcular_checksum(dados: str) -> str:
    return hashlib.sha256(dados.encode()).hexdigest()[:8]

def verificar_checksum(dados: str, checksum_recebido: str) -> bool:
    return calcular_checksum(dados) == checksum_recebido

def pegarTempo(): return time.strftime("%H:%M:%S")
def limparTerminal(): os.system("cls" if os.name == "nt" else "clear")

def exibirCabecalho():
    limparTerminal()
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
    print(f"Aguardando conexões em {HOST}:{PORTA}\n")

def exibirTempoEndereco(endereco):
    print(f"[{pegarTempo()}] Conectado por {endereco}")

def receberMensagem(conexao, timeout=None):
    if timeout is not None: conexao.settimeout(timeout)
    else: conexao.settimeout(None)
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

def receberDescriptografado(conexao, chave, timeout=None):
    raw = receberMensagem(conexao, timeout=timeout)
    if raw: raw = raw.strip()
    if chave and raw:
        try: return decripto_xor(raw, chave)
        except Exception: return raw
    return raw

def enviarCriptografado(mensagem, conexao, chave):
    if chave: mensagem = cripto_xor(mensagem, chave)
    enviarMensagem(mensagem, conexao)

SENHA_COMPARTILHADA = "redes2026"

def receberConfiguracaoCliente(conn):
    dados = receberMensagem(conn)
    if dados: dados = dados.strip()
    if not dados or not dados.startswith("CONFIG|"):
        return "GBN", "IND", 5, None

    partes = dados.split("|")
    protocolo = partes[1] if len(partes) > 1 else "GBN"
    modo_ack = partes[2] if len(partes) > 2 else "IND"
    usa_cripto = partes[3] if len(partes) > 3 else "NAO"
    janela_ini = 5

    print(f"[{pegarTempo()}] {CIANO}[HANDSHAKE]{RESET} Protocolo: {protocolo} | ACK: {modo_ack} | Cripto: {usa_cripto} | Janela: {janela_ini}")
    enviarMensagem(f"OK_CONFIG|{janela_ini}", conn)

    chave = None
    if usa_cripto == "SIM":
        chave = derivar_chave(SENHA_COMPARTILHADA)
        try:
            hello = receberDescriptografado(conn, chave, timeout=5)
            if hello == "HELLO":
                enviarCriptografado("HELLO_OK", conn, chave)
                print(f"[{pegarTempo()}] {VERDE}[CRIPTO]{RESET} Chave verificada. Canal criptografado ativo.")
            else:
                print(f"[{pegarTempo()}] {VERMELHO}[CRIPTO]{RESET} Falha na verificação. Usando texto puro.")
                chave = None
        except socket.timeout:
            print(f"[{pegarTempo()}] {VERMELHO}[CRIPTO]{RESET} Timeout no handshake.")
            chave = None

    return protocolo, modo_ack, janela_ini, chave

def processar_pacote(dados_pacote, chave):
    if chave:
        try: dados_pacote = decripto_xor(dados_pacote, chave)
        except Exception: return None

    partes = dados_pacote.split("|", 3)
    if len(partes) < 4: return None
    try:
        seq, tamanho, payload, checksum_recv = int(partes[0]), int(partes[1]), partes[2], partes[3]
        checksum_ok = verificar_checksum(f"{seq}|{tamanho}|{payload}", checksum_recv)
        return seq, tamanho, payload, checksum_ok
    except (ValueError, IndexError):
        return None
    
def receber_janela(conn, protocolo, modo_ack, seq_esperado,
                   tamanho_max, tamanho_acumulado,
                   mensagem_completa, buffer_sr, janela_cliente, chave):

    TIMEOUT_PACOTE = 10.0
    encerrar = erro = False

    while True:
        try:
            dados_brutos = receberMensagem(conn, timeout=TIMEOUT_PACOTE)
        except socket.timeout:
            print(f"[{pegarTempo()}] {AMARELO}[TIMEOUT]{RESET} Sem pacote em {TIMEOUT_PACOTE}s. Aguardando...")
            continue

        if not dados_brutos:
            print(f"[{pegarTempo()}] {VERMELHO}[ERRO]{RESET} Cliente desconectou.")
            encerrar = erro = True
            break

        pacotes_separados = [p for p in dados_brutos.split("\n") if p.strip()]
        ultimo_seq_grp = None
        nova_janela_grp = janela_cliente

        for pacote_bruto in pacotes_separados:
            dados_para_checar = pacote_bruto
            if chave:
                try: dados_para_checar = decripto_xor(pacote_bruto, chave)
                except Exception: dados_para_checar = pacote_bruto

            if dados_para_checar.startswith("FIM|"):
                ack_fim = "ACK|FIM"
                if chave: ack_fim = cripto_xor(ack_fim, chave)
                enviarMensagem(ack_fim, conn)
                encerrar = True
                break

            resultado = processar_pacote(pacote_bruto, chave)
            if resultado is None:
                continue

            seq, tamanho_payload, payload, checksum_ok = resultado

            if not checksum_ok:
                print(f"[{pegarTempo()}] {VERMELHO}[CHECKSUM INVÁLIDO]{RESET} seq={seq}. Enviando NAK.")
                nak = f"NAK|{seq}"
                if chave: nak = cripto_xor(nak, chave)
                enviarMensagem(nak, conn)
                continue

            if tamanho_acumulado + tamanho_payload > tamanho_max:
                err_msg = "ERRO|LIMITE"
                if chave: err_msg = cripto_xor(err_msg, chave)
                enviarMensagem(err_msg, conn)
                print(f"[{pegarTempo()}] {VERMELHO}[LIMITE]{RESET} Excedeu {tamanho_max} chars. Abortando.")
                erro = True
                break

            nova_janela = random.randint(1, 5)
            cripto_tag = f"{CIANO}[CIFRADO]{RESET} " if chave else ""
            print(f"[{pegarTempo()}] {VERDE}[METADADO]{RESET} {cripto_tag}"
                  f"Seq: {seq} | Bytes: {tamanho_payload} | Payload: '{payload}' | Checksum: OK | Janela→{nova_janela}")

            if protocolo == "GBN":
                if seq == seq_esperado:
                    mensagem_completa += payload
                    tamanho_acumulado += tamanho_payload
                    seq_esperado += 1
                    if modo_ack == "IND":
                        ack = f"ACK|{seq}|{nova_janela}"
                        if chave: ack = cripto_xor(ack, chave)
                        enviarMensagem(ack, conn)
                    else:
                        ultimo_seq_grp = seq
                        nova_janela_grp = nova_janela
                else:
                    print(f"[{pegarTempo()}] {AMARELO}[DESCARTADO GBN]{RESET} Esperado {seq_esperado}, recebido {seq}. NAK.")
                    nak = f"NAK|{seq}"
                    if chave: nak = cripto_xor(nak, chave)
                    enviarMensagem(nak, conn)
                    continue

            elif protocolo == "SR":
                if seq not in buffer_sr:
                    buffer_sr[seq] = payload
                    tamanho_acumulado += tamanho_payload
                while seq_esperado in buffer_sr:
                    mensagem_completa += buffer_sr.pop(seq_esperado)
                    seq_esperado += 1
                
                if modo_ack == "IND":
                    ack = f"ACK|{seq}|{nova_janela}"
                    if chave: ack = cripto_xor(ack, chave)
                    enviarMensagem(ack, conn)
                else:
                    ultimo_seq_grp = seq
                    nova_janela_grp = nova_janela

            janela_cliente = nova_janela
        
        if erro or encerrar:
            break
            
        if modo_ack == "GRP" and ultimo_seq_grp is not None:
            ack_grp = f"ACK|{ultimo_seq_grp}|{nova_janela_grp}"
            if chave: ack_grp = cripto_xor(ack_grp, chave)
            enviarMensagem(ack_grp, conn)
            print(f"[{pegarTempo()}] {VERDE}[ACK GRP]{RESET} Lote confirmado até seq={ultimo_seq_grp} | janela={nova_janela_grp}")

    return (mensagem_completa, tamanho_acumulado, seq_esperado, buffer_sr, janela_cliente, encerrar, erro)

def tratar_conexao(conn, addr):
    exibirTempoEndereco(addr)
    protocolo, modo_ack, janela_cliente, chave = receberConfiguracaoCliente(conn)

    while True:
        try: data = receberMensagem(conn)
        except Exception: break
        
        if data: data = data.strip()
        if chave and data:
            try: data = decripto_xor(data, chave)
            except Exception: pass

        if not data or data == "0":
            print(f"[{pegarTempo()}] Cliente desconectou.")
            break

        if data.isdigit():
            tamanho_max = int(data)
            if tamanho_max < 30:
                msg = "ERRO: O tamanho mínimo é de 30 caracteres"
                if chave: msg = cripto_xor(msg, chave)
                enviarMensagem(msg, conn)
                continue

            ok_msg = "OK"
            if chave: ok_msg = cripto_xor(ok_msg, chave)
            enviarMensagem(ok_msg, conn)

            mensagem_completa = ""
            tamanho_acumulado = 0
            seq_esperado = 1
            buffer_sr = {}

            cripto_info = f"| {CIANO}Cripto: SIM{RESET}" if chave else ""
            print(f"\n{'─'*55}")
            print(f"[{pegarTempo()}] {CIANO}[NOVO BLOCO]{RESET} Modo: {protocolo} | ACK: {modo_ack} | Limite: {tamanho_max} chars {cripto_info}")
            print(f"{'─'*55}")

            (mensagem_completa, tamanho_acumulado, seq_esperado,
             buffer_sr, janela_cliente, encerrar, erro) = receber_janela(
                conn, protocolo, modo_ack, seq_esperado,
                tamanho_max, tamanho_acumulado,
                mensagem_completa, buffer_sr, janela_cliente, chave
            )

            if not erro:
                print(f"\n{VERDE}{NEGRITO}[COMUNICAÇÃO COMPLETA]{RESET} Mensagem: \"{mensagem_completa}\"")
                ok_final = "OK"
                if chave: ok_final = cripto_xor(ok_final, chave)
                enviarMensagem(ok_final, conn)
            continue

def main():
    exibirCabecalho()
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORTA))
    servidor.listen()
    try:
        while True:
            conn, addr = servidor.accept()
            tratar_conexao(conn, addr)
            conn.close()
            print(f"\n[{pegarTempo()}] Conexão encerrada. Aguardando nova...\n")
    except KeyboardInterrupt:
        print(f"\n[{pegarTempo()}] Servidor encerrado pelo usuário.")
    finally:
        servidor.close()

if __name__ == "__main__":
    main()