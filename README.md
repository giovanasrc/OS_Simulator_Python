# 🖥️ PyOS — Simulador Educacional de Sistema Operacional

![Python](https://img.shields.io/badge/Python-3.x-green)
![Status](https://img.shields.io/badge/Status-Educacional-blue)
![Licença](https://img.shields.io/badge/Licença-MIT-lightgrey)

Simulador lógico de Sistema Operacional desenvolvido em Python para fins didáticos, cobrindo os conceitos fundamentais das **Unidades I e II** da disciplina de Sistemas Operacionais.

O projeto permite explorar a mecânica interna de um Kernel sem a complexidade de linguagens de baixo nível, com uma interface de terminal interativa e todos os níveis da trilha de desafios implementados.

---

## 🎯 Objetivos Pedagógicos

- Compreender o **Bloco Descritor de Processo (PCB)**
- Visualizar o **Chaveamento de Contexto** e o **Escalonamento Round Robin**
- Praticar a **Sincronização de Processos** com Semáforos (Mutex)
- Simular estados críticos como **Deadlock** e **Processos Zumbi**
- Entender chamadas de sistema como o `fork()`
- Explorar **Comunicação entre Processos (IPC)** via memória compartilhada

---

## 🚀 Como Executar

**Pré-requisito:** Python 3 instalado.

```bash

# Entre na pasta
cd pyos

# Execute o kernel
python init.py
```

Ao iniciar, você verá a sequência de boot e terá acesso ao terminal interativo:

```
Iniciando PyOS Kernel v2.0...
Carregando módulos de memória [OK]
Iniciando escalonador de processos [OK]
Carregando semáforos e IPC [OK]
Bem-vindo ao terminal. Digite 'help' para comandos.

root@pyos:~#
```

---

## 🛠️ Referência de Comandos

| Categoria | Comando | Descrição |
|---|---|---|
| **Processos** | `spawn [nome] [prioridade]` | Cria processo (prioridade 1=baixa, 2=média, 3=alta) |
| | `ps` | Lista todos os processos e seus estados |
| | `kill [PID]` | Encerra processo à força (SIGKILL) |
| | `wait [PID]` | Coleta processo(s) ZUMBI da memória |
| | `fork [PID]` | Clona um processo pai |
| **CPU** | `cpu` | Executa 1 tick do escalonador |
| | `run` | Executa ticks automaticamente até esvaziar a RAM |
| **E/S** | `block [PID]` | Bloqueia processo (simula espera de periférico) |
| | `unblock [PID]` | Desbloqueia processo, retornando-o à fila |
| **Semáforos** | `lock [PID] [recurso]` | Solicita recurso exclusivo (`impressora` ou `disco`) |
| | `unlock [PID] [recurso]` | Libera recurso e acorda próximo da fila |
| **IPC** | `ipc write [PID] [chave] [valor]` | Escreve na memória compartilhada |
| | `ipc read [PID] [chave]` | Lê da memória compartilhada |
| | `ipc list` | Lista toda a memória compartilhada |
| **Sistema** | `clear` | Limpa a tela |
| | `help` | Exibe todos os comandos |
| | `exit` | Desliga o simulador |

---

## 🎮 Níveis Implementados

### 🟢 Nível 1 — Limite de Memória (OOM)

**Conceito:** Proteção de recursos e erro *Out of Memory*.

O sistema rejeita a criação de mais de 5 processos simultâneos ativos. Processos no estado ZUMBI não contam para o limite, pois já liberaram seus recursos de execução.

```
root@pyos:~# spawn p1
root@pyos:~# spawn p2
root@pyos:~# spawn p3
root@pyos:~# spawn p4
root@pyos:~# spawn p5
root@pyos:~# spawn p6
[Kernel] ERRO: Out of Memory! Limite de 5 processos atingido.
```

---

### 🟡 Nível 2 — Automador de Clock (comando `run`)

**Conceito:** *Timer Interrupt* e automação de ciclos de CPU.

O comando `run` executa o escalonador em loop contínuo até que não restem processos no estado PRONTO, simulando o comportamento de um timer de hardware que dispara interrupções periodicamente.

```
root@pyos:~# spawn navegador
root@pyos:~# spawn editor
root@pyos:~# run
[Kernel] Modo automático iniciado (Timer Interrupt)...
[CPU] Executando PID 1000 (navegador)...
[CPU] Executando PID 1001 (editor)...
...
[Kernel] Nenhum processo pronto. Loop encerrado.
```

---

### 🟡 Nível 3 — Gargalo de E/S (Estado BLOQUEADO)

**Conceito:** Ciclo de vida do processo e gerenciamento de E/S.

Processos podem ser bloqueados para simular uma espera por periférico (disco, rede, teclado). Enquanto bloqueados, são ignorados pelo escalonador. O comando `unblock` os retorna à fila de prontos.

```
root@pyos:~# spawn leitor_disco
root@pyos:~# block 1000
[Kernel] PID 1000 bloqueado. Aguardando evento de E/S.

root@pyos:~# ps
PID    | NOME           | ESTADO       | ...
1000   | leitor_disco   | BLOQUEADO    | ...

root@pyos:~# unblock 1000
[Kernel] PID 1000 desbloqueado. Retornando à fila de prontos.
```

---

### 🟠 Nível 4 — Prioridades (Escalonamento Preemptivo)

**Conceito:** Escalonamento preemptivo por prioridade.

Cada processo recebe uma prioridade de 1 (baixa) a 3 (alta) na criação. O escalonador sempre escolhe o processo de maior prioridade da fila de prontos, quebrando o Round Robin puro do código original.

```
root@pyos:~# spawn antivirus 1
root@pyos:~# spawn editor 2
root@pyos:~# spawn kernel_task 3
root@pyos:~# cpu
[CPU] Executando PID 1002 (kernel_task) | Prioridade: 3...
```

> Mesmo `kernel_task` sendo o último criado, ele executa primeiro por ter prioridade 3.

---

### 🔴 Nível 5 — Semáforos (Exclusão Mútua)

**Conceito:** Exclusão mútua e Região Crítica.

Recursos compartilhados (`impressora` e `disco`) são controlados por semáforos binários (Mutex). Apenas um processo pode segurar cada recurso por vez. Os demais ficam BLOQUEADOS em fila até o recurso ser liberado.

```
root@pyos:~# spawn proc_a
root@pyos:~# spawn proc_b
root@pyos:~# lock 1000 impressora
[Kernel] Semáforo LOCK: PID 1000 obteve acesso exclusivo à 'impressora'.

root@pyos:~# lock 1001 impressora
[Kernel] Recurso 'impressora' ocupado por PID 1000. PID 1001 bloqueado na fila.

root@pyos:~# unlock 1000 impressora
[Kernel] Semáforo UNLOCK: PID 1000 liberou 'impressora'.
[Kernel] PID 1001 acordado e obteve acesso a 'impressora'.
```

---

### 🔴 Nível 6 — Deadlock (Impasse de Recursos)

**Conceito:** Espera circular e detecção de deadlock.

O kernel detecta automaticamente ciclos no grafo de dependências entre processos. Quando o processo A aguarda um recurso segurado pelo B, e o B aguarda um recurso segurado pelo A, o sistema emite um **KERNEL PANIC**.

```
root@pyos:~# spawn proc_a
root@pyos:~# spawn proc_b
root@pyos:~# lock 1000 impressora
root@pyos:~# lock 1001 disco
root@pyos:~# lock 1000 disco
root@pyos:~# lock 1001 impressora

[KERNEL PANIC] ⚠️  DEADLOCK DETECTADO! PIDs em espera circular: [1000, 1001]
[Kernel] Sistema em impasse. Use 'kill [PID]' para resolver.
```

Para resolver: `kill 1000` libera os recursos e desbloqueia o outro processo.

---

### 🟣 Nível 7 — Processos Zumbi

**Conceito:** Estruturas de dados pós-execução e coleta de lixo.

Processos que terminam seus ciclos não são removidos imediatamente da RAM. Permanecem no estado ZUMBI até serem coletados pelo comando `wait`, simulando o *garbage collection* do kernel.

```
root@pyos:~# spawn temp
root@pyos:~# cpu
[Kernel] PID 1000 finalizou. Estado: ZUMBI (aguardando wait).

root@pyos:~# ps
1000   | temp           | ZUMBI        | ...

root@pyos:~# wait 1000
[Kernel] PID 1000 (temp) coletado da memória.
```

`wait` sem argumento coleta todos os zumbis de uma vez.

---

### 💀 Nível 8 — fork()

**Conceito:** Hierarquia de processos e clonagem de contexto.

O comando `fork` clona um processo pai, criando um filho com o mesmo nome (sufixo `_fork`), mesma prioridade e mesmo número de ciclos restantes. O PCB do filho registra o PID do pai, estabelecendo uma hierarquia de processos.

```
root@pyos:~# spawn servidor 2
root@pyos:~# fork 1000
[Kernel] Processo 'servidor_fork' criado com PID 1001 | Prioridade: 2 (filho de PID 1000)
[Kernel] fork() realizado: PID 1001 é clone de PID 1000 (ciclos copiados: 4).

root@pyos:~# ps
1000   | servidor       | PRONTO       | 4      | 2      | -
1001   | servidor_fork  | PRONTO       | 4      | 2      | 1000
```

---

### 🔥 Nível Supremo — IPC (Comunicação entre Processos)

**Conceito:** Isolamento de memória e IPC (*Inter-Process Communication*).

Processos se comunicam através de uma área de memória compartilhada usando um sistema de chave-valor. Um processo escreve uma mensagem e outro lê, simulando o mecanismo de IPC presente em sistemas operacionais reais.

```
root@pyos:~# spawn servidor
root@pyos:~# spawn cliente
root@pyos:~# ipc write 1000 status ativo
root@pyos:~# ipc write 1000 porta 8080
root@pyos:~# ipc read 1001 status
[IPC] PID 1001 leu chave 'status': 'ativo' (escrito por PID 1000)

root@pyos:~# ipc list
CHAVE           | VALOR                | ESCRITOR PID
--------------------------------------------------
status          | ativo                | 1000
porta           | 8080                 | 1000
```

> **Atenção:** chave e valor não podem conter espaços.

---

## 📐 Arquitetura do Projeto

```
pyos/
└── init.py       # Kernel completo: PCB, escalonador, semáforos, IPC e shell
```

Todo o simulador está contido em um único arquivo, organizado em três camadas:

- **Estruturas de dados** — `tabela_processos`, `recursos`, `memoria_compartilhada`
- **Funções do Kernel** — escalonador, semáforos, fork, IPC, detecção de deadlock
- **Shell (User Space)** — loop de entrada e despacho de comandos

---

## 📘 Referência Teórica

**Unidade I — Fundamentos, Processos e Threads**
- Process Control Block (PCB)
- Estados do processo: Pronto, Executando, Bloqueado, Zumbi
- Chamadas de sistema: `fork()`, `wait()`
- Comunicação entre processos (IPC)

**Unidade II — Gerência do Processador e Escalonamento**
- Escalonamento Round Robin
- Escalonamento por Prioridade
- Chaveamento de Contexto
- Semáforos e Exclusão Mútua
- Deadlock: condições, detecção e resolução

---

Desenvolvido para fins educacionais. ✨
