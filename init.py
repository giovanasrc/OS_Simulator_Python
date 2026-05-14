# imports
import time
import sys
import random

# ==========================================
# ESTRUTURAS DE DADOS DO KERNEL
# ==========================================

# Tabela global de processos (Nossa "RAM")
tabela_processos = []
pid_counter = 1000  # PIDs na vida real começam em 1000

# NÍVEL 5/6 - Tabela de recursos/semáforos
# Cada recurso tem: dono (PID ou None) e fila de espera
recursos = {
    "impressora": {"dono": None, "fila": []},
    "disco":      {"dono": None, "fila": []},
}

# NÍVEL SUPREMO - Memória compartilhada para IPC
memoria_compartilhada = {}  # { chave: {"valor": ..., "escritor_pid": ...} }

# NÍVEL 4 - Limite de memória
MAX_PROCESSOS = 5


class PCB:
    """Bloco Descritor de Processo (Process Control Block)"""
    def __init__(self, nome, prioridade=1, pai_pid=None):
        global pid_counter
        self.pid = pid_counter
        self.nome = nome
        # Estados possíveis: PRONTO, EXECUTANDO, TERMINADO, BLOQUEADO, ZUMBI
        self.estado = "PRONTO"
        self.ciclos_restantes = random.randint(2, 6)
        # NÍVEL 4 - Prioridade: quanto maior, mais urgente (1=baixa, 2=média, 3=alta)
        self.prioridade = prioridade
        # NÍVEL 8 - fork(): referência ao processo pai
        self.pai_pid = pai_pid
        # NÍVEL 6 - Recurso que este processo está aguardando (para detectar deadlock)
        self.aguardando_recurso = None
        pid_counter += 1


# ==========================================
# FUNÇÕES DO KERNEL E ESCALONADOR
# ==========================================

def boot():
    """Simula a inicialização do Sistema Operacional"""
    print("Iniciando PyOS Kernel v2.0...")
    time.sleep(1)
    print("Carregando módulos de memória [OK]")
    time.sleep(0.5)
    print("Iniciando escalonador de processos [OK]")
    time.sleep(0.5)
    print("Carregando semáforos e IPC [OK]")
    time.sleep(0.5)
    print("Bem-vindo ao terminal. Digite 'help' para comandos.\n")


def spawn_process(nome, prioridade=1, pai_pid=None):
    """Cria um novo processo e adiciona na tabela (RAM)"""

    # NÍVEL 1 - OOM: limite de 5 processos simultâneos
    ativos = [p for p in tabela_processos if p.estado not in ("TERMINADO", "ZUMBI")]
    if len(ativos) >= MAX_PROCESSOS:
        print(f"[Kernel] ERRO: Out of Memory! Limite de {MAX_PROCESSOS} processos atingido.")
        return None

    novo_processo = PCB(nome, prioridade=prioridade, pai_pid=pai_pid)
    tabela_processos.append(novo_processo)
    pai_info = f" (filho de PID {pai_pid})" if pai_pid else ""
    print(f"[Kernel] Processo '{nome}' criado com PID {novo_processo.pid} | Prioridade: {prioridade}{pai_info}")
    return novo_processo


def escalonador_tick():
    """Simula um ciclo (quantum) do processador — Round Robin com Prioridade"""

    # NÍVEL 4 - Ordena os prontos por prioridade (maior prioridade primeiro)
    prontos = sorted(
        [p for p in tabela_processos if p.estado == "PRONTO"],
        key=lambda p: p.prioridade,
        reverse=True
    )

    if not prontos:
        print("[CPU] Ociosa (Idle). Nenhum processo na fila de prontos.")
        return

    processo_atual = prontos[0]

    # CHAVEAMENTO DE CONTEXTO: Entrando na CPU
    processo_atual.estado = "EXECUTANDO"
    print(f"\n[CPU] Executando PID {processo_atual.pid} ({processo_atual.nome}) | Prioridade: {processo_atual.prioridade}...")
    time.sleep(1)

    processo_atual.ciclos_restantes -= 1

    if processo_atual.ciclos_restantes <= 0:
        # NÍVEL 7 - Zumbi: processo terminado fica na RAM como ZUMBI
        processo_atual.estado = "ZUMBI"
        print(f"[Kernel] PID {processo_atual.pid} finalizou. Estado: ZUMBI (aguardando wait).")
    else:
        # CHAVEAMENTO DE CONTEXTO: preempção — vai pro fim da fila
        processo_atual.estado = "PRONTO"
        tabela_processos.remove(processo_atual)
        tabela_processos.append(processo_atual)
        print(f"[Kernel] Chaveamento de contexto. PID {processo_atual.pid} pausado e movido para o fim da fila.")


# NÍVEL 2 - Comando run: executa ticks até RAM esvaziar
def run_automatico():
    """Executa o escalonador em loop até não restar processos prontos"""
    print("[Kernel] Modo automático iniciado (Timer Interrupt)...")
    while True:
        prontos = [p for p in tabela_processos if p.estado == "PRONTO"]
        if not prontos:
            print("[Kernel] Nenhum processo pronto. Loop encerrado.")
            break
        escalonador_tick()


# NÍVEL 3 - Bloquear/Desbloquear processo (simula espera de E/S)
def bloquear_processo(pid):
    """Coloca um processo no estado BLOQUEADO (ex: aguardando I/O)"""
    for p in tabela_processos:
        if p.pid == pid:
            if p.estado == "PRONTO":
                p.estado = "BLOQUEADO"
                print(f"[Kernel] PID {pid} bloqueado. Aguardando evento de E/S.")
            else:
                print(f"[Kernel] PID {pid} não está PRONTO (estado atual: {p.estado}).")
            return
    print(f"[Kernel] PID {pid} não encontrado.")


def desbloquear_processo(pid):
    """Retorna um processo BLOQUEADO para PRONTO"""
    for p in tabela_processos:
        if p.pid == pid:
            if p.estado == "BLOQUEADO":
                p.estado = "PRONTO"
                print(f"[Kernel] PID {pid} desbloqueado. Retornando à fila de prontos.")
            else:
                print(f"[Kernel] PID {pid} não está BLOQUEADO (estado atual: {p.estado}).")
            return
    print(f"[Kernel] PID {pid} não encontrado.")


# NÍVEL 5 - Semáforo (Mutex): solicitar recurso compartilhado
def lock_recurso(pid, nome_recurso="impressora"):
    """Solicita acesso exclusivo a um recurso via semáforo"""
    if nome_recurso not in recursos:
        print(f"[Kernel] Recurso '{nome_recurso}' não existe. Recursos disponíveis: {list(recursos.keys())}")
        return

    recurso = recursos[nome_recurso]
    processo = next((p for p in tabela_processos if p.pid == pid), None)

    if not processo:
        print(f"[Kernel] PID {pid} não encontrado.")
        return

    if recurso["dono"] is None:
        # Recurso livre: concede acesso
        recurso["dono"] = pid
        print(f"[Kernel] Semáforo LOCK: PID {pid} obteve acesso exclusivo à '{nome_recurso}'.")
    else:
        # Recurso ocupado: bloqueia o processo e coloca na fila
        processo.estado = "BLOQUEADO"
        processo.aguardando_recurso = nome_recurso
        recurso["fila"].append(pid)
        print(f"[Kernel] Recurso '{nome_recurso}' ocupado por PID {recurso['dono']}. PID {pid} bloqueado na fila.")

        # NÍVEL 6 - Detectar deadlock (espera circular)
        detectar_deadlock()


def unlock_recurso(pid, nome_recurso="impressora"):
    """Libera um recurso e acorda o próximo processo na fila"""
    if nome_recurso not in recursos:
        print(f"[Kernel] Recurso '{nome_recurso}' não existe.")
        return

    recurso = recursos[nome_recurso]

    if recurso["dono"] != pid:
        print(f"[Kernel] PID {pid} não é o dono de '{nome_recurso}'.")
        return

    # Libera o recurso
    recurso["dono"] = None
    print(f"[Kernel] Semáforo UNLOCK: PID {pid} liberou '{nome_recurso}'.")

    # Acorda o próximo na fila (se houver)
    if recurso["fila"]:
        proximo_pid = recurso["fila"].pop(0)
        proximo = next((p for p in tabela_processos if p.pid == proximo_pid), None)
        if proximo:
            recurso["dono"] = proximo_pid
            proximo.estado = "PRONTO"
            proximo.aguardando_recurso = None
            print(f"[Kernel] PID {proximo_pid} acordado e obteve acesso a '{nome_recurso}'.")


# NÍVEL 6 - Detecção de Deadlock (espera circular)
def detectar_deadlock():
    """Verifica se existe espera circular entre processos (deadlock)"""
    # Monta um grafo de dependências: pid -> pid_do_dono_do_recurso_que_ele_espera
    grafo = {}
    for p in tabela_processos:
        if p.aguardando_recurso and p.estado == "BLOQUEADO":
            dono = recursos[p.aguardando_recurso]["dono"]
            if dono:
                grafo[p.pid] = dono

    # Detecta ciclo no grafo usando DFS
    def tem_ciclo(inicio):
        visitados = set()
        atual = inicio
        while atual in grafo:
            if atual in visitados:
                return True  # Ciclo encontrado!
            visitados.add(atual)
            atual = grafo[atual]
        return False

    deadlocks = [pid for pid in grafo if tem_ciclo(pid)]
    if deadlocks:
        print(f"\n[KERNEL PANIC] ⚠️  DEADLOCK DETECTADO! PIDs em espera circular: {deadlocks}")
        print("[Kernel] Sistema em impasse. Use 'kill [PID]' para resolver.")


# NÍVEL 7 - wait: coleta processos zumbi (garbage collection)
def wait_zumbi(pid=None):
    """Coleta (remove) processos ZUMBI da RAM"""
    global tabela_processos
    if pid:
        alvo = next((p for p in tabela_processos if p.pid == pid and p.estado == "ZUMBI"), None)
        if alvo:
            tabela_processos.remove(alvo)
            print(f"[Kernel] PID {alvo.pid} ({alvo.nome}) coletado da memória.")
        else:
            print(f"[Kernel] PID {pid} não é um processo ZUMBI ou não existe.")
    else:
        zumbis = [p for p in tabela_processos if p.estado == "ZUMBI"]
        if not zumbis:
            print("[Kernel] Nenhum processo ZUMBI na memória.")
            return
        for z in zumbis:
            tabela_processos.remove(z)
            print(f"[Kernel] PID {z.pid} ({z.nome}) coletado da memória.")


# NÍVEL 8 - fork(): clona um processo pai
def fork_processo(pai_pid):
    """Clona um processo pai, criando um filho com o mesmo contexto"""
    pai = next((p for p in tabela_processos if p.pid == pai_pid), None)

    if not pai:
        print(f"[Kernel] PID {pai_pid} não encontrado para fork().")
        return

    if pai.estado == "ZUMBI":
        print(f"[Kernel] Não é possível fazer fork() de um processo ZUMBI.")
        return

    filho = spawn_process(
        nome=f"{pai.nome}_fork",
        prioridade=pai.prioridade,
        pai_pid=pai_pid
    )

    if filho:
        filho.ciclos_restantes = pai.ciclos_restantes  # Copia o contexto exato
        print(f"[Kernel] fork() realizado: PID {filho.pid} é clone de PID {pai_pid} (ciclos copiados: {filho.ciclos_restantes}).")


# NÍVEL SUPREMO - IPC: memória compartilhada
def ipc_write(pid, chave, valor):
    """Processo escreve na memória compartilhada"""
    processo = next((p for p in tabela_processos if p.pid == pid), None)
    if not processo:
        print(f"[IPC] PID {pid} não encontrado.")
        return
    memoria_compartilhada[chave] = {"valor": valor, "escritor_pid": pid}
    print(f"[IPC] PID {pid} escreveu na chave '{chave}': '{valor}'")


def ipc_read(pid, chave):
    """Processo lê da memória compartilhada"""
    processo = next((p for p in tabela_processos if p.pid == pid), None)
    if not processo:
        print(f"[IPC] PID {pid} não encontrado.")
        return
    if chave in memoria_compartilhada:
        entrada = memoria_compartilhada[chave]
        print(f"[IPC] PID {pid} leu chave '{chave}': '{entrada['valor']}' (escrito por PID {entrada['escritor_pid']})")
    else:
        print(f"[IPC] Chave '{chave}' não encontrada na memória compartilhada.")


def ipc_list():
    """Lista todas as entradas na memória compartilhada"""
    if not memoria_compartilhada:
        print("[IPC] Memória compartilhada vazia.")
        return
    print(f"{'CHAVE':<15} | {'VALOR':<20} | ESCRITOR PID")
    print("-" * 50)
    for chave, entrada in memoria_compartilhada.items():
        print(f"{chave:<15} | {str(entrada['valor']):<20} | {entrada['escritor_pid']}")


# ==========================================
# INTERFACE COM O USUÁRIO (SHELL)
# ==========================================

def shell():
    """O laço principal que aguarda comandos do usuário"""
    global tabela_processos

    while True:
        try:
            comando = input("root@pyos:~# ").strip().split()

            if not comando:
                continue

            acao = comando[0].lower()

            # ── exit ──────────────────────────────────────────────
            if acao == "exit":
                print("Desligando o sistema...")
                break

            # ── help ──────────────────────────────────────────────
            elif acao == "help":
                print("""
╔══════════════════════════════════════════════════════════════╗
║                  PyOS Kernel v2.0 - Comandos                 ║
╠══════════════════════════════════════════════════════════════╣
║ PROCESSOS                                                    ║
║  spawn [nome] [prioridade]  Cria processo (prioridade 1-3)   ║
║  ps                         Lista todos os processos         ║
║  kill [PID]                 Encerra processo à força         ║
║  wait [PID]                 Coleta processo(s) ZUMBI         ║
║  fork [PID]                 Clona um processo (fork)         ║
╠══════════════════════════════════════════════════════════════╣
║ CPU / ESCALONADOR                                            ║
║  cpu                        Executa 1 tick do escalonador    ║
║  run                        Executa ticks até RAM esvaziar   ║
╠══════════════════════════════════════════════════════════════╣
║ E/S (I/O)                                                    ║
║  block [PID]                Bloqueia processo (espera E/S)   ║
║  unblock [PID]              Desbloqueia processo             ║
╠══════════════════════════════════════════════════════════════╣
║ SEMÁFOROS / RECURSOS                                         ║
║  lock [PID] [recurso]       Solicita recurso (impressora,    ║
║                             disco). Padrão: impressora       ║
║  unlock [PID] [recurso]     Libera recurso                   ║
╠══════════════════════════════════════════════════════════════╣
║ IPC - MEMÓRIA COMPARTILHADA                                  ║
║  ipc write [PID] [chave] [valor]  Escreve na memória IPC     ║
║  ipc read  [PID] [chave]          Lê da memória IPC          ║
║  ipc list                         Lista memória IPC          ║
╠══════════════════════════════════════════════════════════════╣
║  clear                      Limpa a tela                     ║
║  exit                       Desliga o sistema                ║
╚══════════════════════════════════════════════════════════════╝
""")

            # ── clear ─────────────────────────────────────────────
            elif acao == "clear":
                print("\033[H\033[J", end="")

            # ── spawn ─────────────────────────────────────────────
            elif acao == "spawn":
                if len(comando) < 2:
                    print("Uso: spawn [nome] [prioridade=1]")
                else:
                    nome = comando[1]
                    prioridade = 1
                    if len(comando) >= 3:
                        try:
                            prioridade = int(comando[2])
                            if prioridade not in (1, 2, 3):
                                print("[Kernel] Prioridade inválida. Use 1 (baixa), 2 (média) ou 3 (alta).")
                                continue
                        except ValueError:
                            print("[Kernel] Prioridade deve ser 1, 2 ou 3.")
                            continue
                    spawn_process(nome, prioridade=prioridade)

            # ── ps ────────────────────────────────────────────────
            elif acao == "ps":
                print(f"\n{'PID':<6} | {'NOME':<14} | {'ESTADO':<12} | {'CICLOS':<7} | {'PRIOR':<6} | PAI PID")
                print("-" * 68)
                for p in tabela_processos:
                    pai = str(p.pai_pid) if p.pai_pid else "-"
                    aguard = f" (aguarda: {p.aguardando_recurso})" if p.aguardando_recurso else ""
                    print(f"{p.pid:<6} | {p.nome[:14]:<14} | {p.estado:<12} | {p.ciclos_restantes:<7} | {p.prioridade:<6} | {pai}{aguard}")
                if not tabela_processos:
                    print("Nenhum processo em execução.")
                print()

            # ── kill ──────────────────────────────────────────────
            elif acao == "kill":
                if len(comando) < 2:
                    print("Uso: kill [PID]")
                else:
                    try:
                        alvo_pid = int(comando[1])
                        # Libera qualquer recurso que o processo segurava
                        for nome_r, recurso in recursos.items():
                            if recurso["dono"] == alvo_pid:
                                recurso["dono"] = None
                                print(f"[Kernel] Recurso '{nome_r}' liberado (dono morto).")
                            if alvo_pid in recurso["fila"]:
                                recurso["fila"].remove(alvo_pid)
                        tabela_processos = [p for p in tabela_processos if p.pid != alvo_pid]
                        print(f"[Kernel] Sinal SIGKILL enviado. PID {alvo_pid} destruído.")
                    except ValueError:
                        print("Erro: PID deve ser um número inteiro.")

            # ── cpu ───────────────────────────────────────────────
            elif acao == "cpu":
                escalonador_tick()

            # ── run ───────────────────────────────────────────────
            elif acao == "run":
                run_automatico()

            # ── block / unblock ───────────────────────────────────
            elif acao == "block":
                if len(comando) < 2:
                    print("Uso: block [PID]")
                else:
                    try:
                        bloquear_processo(int(comando[1]))
                    except ValueError:
                        print("Erro: PID deve ser um número inteiro.")

            elif acao == "unblock":
                if len(comando) < 2:
                    print("Uso: unblock [PID]")
                else:
                    try:
                        desbloquear_processo(int(comando[1]))
                    except ValueError:
                        print("Erro: PID deve ser um número inteiro.")

            # ── lock / unlock ─────────────────────────────────────
            elif acao == "lock":
                if len(comando) < 2:
                    print("Uso: lock [PID] [recurso=impressora]")
                else:
                    try:
                        pid_alvo = int(comando[1])
                        recurso_alvo = comando[2] if len(comando) >= 3 else "impressora"
                        lock_recurso(pid_alvo, recurso_alvo)
                    except ValueError:
                        print("Erro: PID deve ser um número inteiro.")

            elif acao == "unlock":
                if len(comando) < 2:
                    print("Uso: unlock [PID] [recurso=impressora]")
                else:
                    try:
                        pid_alvo = int(comando[1])
                        recurso_alvo = comando[2] if len(comando) >= 3 else "impressora"
                        unlock_recurso(pid_alvo, recurso_alvo)
                    except ValueError:
                        print("Erro: PID deve ser um número inteiro.")

            # ── wait ──────────────────────────────────────────────
            elif acao == "wait":
                if len(comando) >= 2:
                    try:
                        wait_zumbi(int(comando[1]))
                    except ValueError:
                        print("Erro: PID deve ser um número inteiro.")
                else:
                    wait_zumbi()

            # ── fork ──────────────────────────────────────────────
            elif acao == "fork":
                if len(comando) < 2:
                    print("Uso: fork [PID]")
                else:
                    try:
                        fork_processo(int(comando[1]))
                    except ValueError:
                        print("Erro: PID deve ser um número inteiro.")

            # ── ipc ───────────────────────────────────────────────
            elif acao == "ipc":
                if len(comando) < 2:
                    print("Uso: ipc [write|read|list] ...")
                else:
                    sub = comando[1].lower()
                    if sub == "list":
                        ipc_list()
                    elif sub == "write":
                        if len(comando) < 5:
                            print("Uso: ipc write [PID] [chave] [valor]")
                        else:
                            try:
                                ipc_write(int(comando[2]), comando[3], comando[4])
                            except ValueError:
                                print("Erro: PID deve ser um número inteiro.")
                    elif sub == "read":
                        if len(comando) < 4:
                            print("Uso: ipc read [PID] [chave]")
                        else:
                            try:
                                ipc_read(int(comando[2]), comando[3])
                            except ValueError:
                                print("Erro: PID deve ser um número inteiro.")
                    else:
                        print(f"[IPC] Subcomando '{sub}' desconhecido. Use: write, read, list.")

            # ── desconhecido ──────────────────────────────────────
            else:
                print(f"bash: {acao}: comando não encontrado. Digite 'help'.")

        except KeyboardInterrupt:
            print("\nPor favor, use 'exit' para sair do PyOS.")


# ==========================================
# INÍCIO DO SISTEMA
# ==========================================

if __name__ == "__main__":
    boot()
    shell()