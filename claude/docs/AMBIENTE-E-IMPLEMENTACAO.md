# Ambiente Real e Implementação — Plataforma GitOps Kubernetes

> Este documento descreve o **ambiente físico real** (6 VMs no Hyper-V), como ele mapeia
> para a arquitetura descrita em [`ARQUITETURA.md`](./ARQUITETURA.md), e o passo a passo
> de bootstrap do cluster Kubernetes via `kubeadm` + `kube-vip` + `Calico`, substituindo o
> fluxo baseado em `kind`/WSL2 descrito originalmente no [`GUIA-DE-IMPLEMENTACAO.md`](./GUIA-DE-IMPLEMENTACAO.md)
> (Fases 0-2). Para a especificação completa do que será construído por cima do cluster
> (ArgoCD, observabilidade, etc.), veja [`../PROMPT.md`](../PROMPT.md).
>
> Diagramas neste documento usam **Mermaid** (texto versionado em Git, renderizado
> automaticamente no PDF gerado por `claude/docs/pdf/build_html.py`) — funciona como o
> Draw.io, mas como código: cada mudança de arquitetura é um diff legível, não um arquivo
> binário.

---

## 1. Visão Geral — do PROMPT.md ao Hardware Real

Recapitulando o objetivo (detalhado em [`../PROMPT.md`](../PROMPT.md)): construir uma
**plataforma GitOps de referência**, com `base/` + `overlays/{dev,prod}` orquestrados por
ArgoCD, observabilidade como código, e segurança desde o dia 1.

A decisão original do projeto era rodar o ambiente `dev` via `kind` (Kubernetes-in-Docker)
dentro do WSL2. Essa decisão **mudou**: o ambiente `dev` agora é um **cluster Kubernetes real**,
provisionado com `kubeadm` em **6 máquinas virtuais Ubuntu Server no Hyper-V**, com
**control-plane em alta disponibilidade (3 nós)** — um cenário muito mais próximo de produção
do que um cluster `kind` efêmero.

| | Antes (descontinuado) | Agora |
|---|---|---|
| Onde roda | WSL2 (Ubuntu-24.04) dentro do Windows Server | 6 VMs Ubuntu Server dedicadas no Hyper-V |
| Como sobe o cluster | `kind create cluster` (nós = containers Docker) | `kubeadm init`/`join` (nós = VMs reais) |
| Control-plane | 1 nó (dentro do `kind-config.yaml`) | 3 nós em HA, com VIP via `kube-vip` |
| CNI | `kindnet` (padrão do kind) | `Calico` (enforcement real de NetworkPolicy) |
| Rede | NAT interno do Docker/WSL2 | Rede física da LAN (`192.168.1.0/24`) |

---

## 2. Inventário Real das Máquinas

| Papel | Hostname físico | IP | Usuário | vCPU¹ | RAM¹ | Função |
|---|---|---|---|---|---|---|
| Bastion / gerenciamento | `lab01` | `192.168.1.105` | `lab01` | 2 | 4 GB | Roda `kubectl`, `helm`, `kustomize`, `argocd` CLI e o Ansible que provisiona todo o resto. Não participa do cluster Kubernetes. |
| Control-plane #1 | `lab02` | `192.168.1.101` | `lab02` | 2-4 | 8 GB | Primeiro nó (`kubeadm init`), também roda `kube-vip`. |
| Control-plane #2 | `lab03` | `192.168.1.106` | `lab03` | 2-4 | 8 GB | Entra via `kubeadm join --control-plane`, também roda `kube-vip`. |
| Control-plane #3 | `lab04` | `192.168.1.107` | `lab04` | 2-4 | 8 GB | Idem — fecha o quórum de 3 nós do `etcd`, também roda `kube-vip`. |
| Worker #1 | `lab05` | `192.168.1.108` | `lab05` | 4 | 16 GB | Roda as cargas: ArgoCD, ingress-nginx, cert-manager, kube-prometheus-stack. |
| Worker #2 | `lab06` | `192.168.1.109` | `lab06` | 4 | 16 GB | Idem — distribui carga com o worker #1. |

¹ vCPU/RAM conforme planejado em [`handoff.md`](../../handoff.md); ajustar conforme alocado de fato no Hyper-V.

**IP virtual (VIP) do control-plane:** `192.168.1.110:6443`, gerenciado por `kube-vip` (não é
uma 7ª VM — é um endereço flutuante anunciado por ARP por quem quer que seja o líder entre os
3 control-planes naquele momento). **Confirme que esse IP está livre e fora do range do DHCP**
da rede `192.168.1.0/24` antes de rodar o bootstrap.

> ⚠️ As senhas reais de acesso SSH (mesma para todas as VMs no momento da criação) estão em
> `scripts/inventory.ini`, que é **ignorado pelo Git** (`.gitignore` na raiz) — nunca commitar
> esse arquivo. Troque essas senhas (ou migre para autenticação por chave) depois do bootstrap
> inicial; ver seção 7.

---

## 3. Diagrama de Rede

```mermaid
flowchart TB
    subgraph LAN["Rede física — 192.168.1.0/24"]
        direction TB
        VIP["VIP API Server<br/>192.168.1.110:6443<br/>(kube-vip, flutuante)"]

        subgraph Mgmt["Bastion"]
            M1["mgmt-01 (lab01)<br/>192.168.1.105<br/>kubectl · helm · kustomize · argocd-cli · Ansible"]
        end

        subgraph CPs["Control-plane (HA, 3 nós)"]
            CP1["k8s-cp-01 (lab02)<br/>192.168.1.101<br/>kube-vip + apiserver + etcd"]
            CP2["k8s-cp-02 (lab03)<br/>192.168.1.106<br/>kube-vip + apiserver + etcd"]
            CP3["k8s-cp-03 (lab04)<br/>192.168.1.107<br/>kube-vip + apiserver + etcd"]
        end

        subgraph Workers["Workers"]
            W1["k8s-worker-01 (lab05)<br/>192.168.1.108<br/>ArgoCD · Ingress · cert-manager · Monitoring"]
            W2["k8s-worker-02 (lab06)<br/>192.168.1.109<br/>réplica de carga"]
        end
    end

    M1 -- "SSH (Ansible)" --> CP1 & CP2 & CP3 & W1 & W2
    M1 -- "kubectl (via VIP)" --> VIP
    VIP -. "líder eleito por vez" .-> CP1
    VIP -. "failover" .-> CP2
    VIP -. "failover" .-> CP3
    CP1 <-->|"etcd raft (quórum 2/3)"| CP2
    CP2 <-->|"etcd raft"| CP3
    CP1 <-->|"etcd raft"| CP3
    CP1 & CP2 & CP3 -- "agenda pods" --> W1 & W2
```

---

## 4. Diagrama de Componentes (o que roda em cada nó)

```mermaid
flowchart LR
    subgraph mgmt01["mgmt-01 — Bastion"]
        Tools["kubectl / helm / kustomize<br/>argocd CLI / Ansible"]
    end

    subgraph cluster["Cluster Kubernetes (kubeadm)"]
        direction TB
        subgraph cp["Control-plane (×3, HA)"]
            ApiServer["kube-apiserver"]
            Etcd["etcd"]
            Sched["kube-scheduler"]
            CtrlMgr["kube-controller-manager"]
            KubeVip["kube-vip (static pod)"]
        end
        subgraph workers["Workers (×2)"]
            Calico["Calico (CNI, todos os nós)"]
            Argo["ArgoCD"]
            Ingress["ingress-nginx"]
            Cert["cert-manager"]
            Mon["kube-prometheus-stack"]
            Head["Headlamp"]
            Apps["apps: sample-app"]
        end
    end

    Tools -- "kubectl apply -f argocd/apps/" --> ApiServer
    ApiServer --> Sched --> workers
    Argo -- "reconcilia a partir do Git" --> Ingress & Cert & Mon & Head & Apps
```

---

## 5. Sequência de Bootstrap (o que o script automatiza)

```mermaid
sequenceDiagram
    participant Op as Operador (você)
    participant Mgmt as mgmt-01 (lab01)
    participant CP1 as k8s-cp-01 (lab02)
    participant CP23 as k8s-cp-02/03 (lab03/04)
    participant W as workers (lab05/06)

    Op->>Mgmt: ./scripts/bootstrap-cluster.sh
    Mgmt->>Mgmt: instala ansible + sshpass (se faltar)
    Mgmt->>CP1: (common) containerd, kubeadm, kubelet, kubectl
    Mgmt->>CP23: (common) idem
    Mgmt->>W: (common) idem
    Mgmt->>CP1: grava manifest static pod kube-vip
    Mgmt->>CP23: grava manifest static pod kube-vip
    Mgmt->>CP1: kubeadm init --control-plane-endpoint=VIP:6443 --upload-certs
    CP1-->>Mgmt: comandos de join (worker + control-plane)
    Mgmt->>CP23: kubeadm join --control-plane (usa certificate-key)
    Mgmt->>W: kubeadm join (worker)
    Mgmt->>CP1: kubectl apply calico.yaml (CNI)
    Mgmt->>Mgmt: copia /etc/kubernetes/admin.conf de CP1 para ~/.kube/config
    Mgmt-->>Op: cluster pronto — kubectl get nodes (5 nós Ready)
```

Após esse ponto, o cluster Kubernetes existe e está saudável — mas **vazio** (sem ArgoCD,
sem Ingress, sem nada além do CNI). A partir daqui, segue-se o restante do
[`GUIA-DE-IMPLEMENTACAO.md`](./GUIA-DE-IMPLEMENTACAO.md) a partir da **Fase 3** (bootstrap do
ArgoCD), já que as Fases 0-2 (ferramentas, esqueleto, subir cluster) foram substituídas pelo
fluxo deste documento.

---

## 6. Como Executar

### 6.1 Pré-requisitos

- As 6 VMs criadas, com Ubuntu Server instalado, acessíveis por SSH com usuário/senha.
- Acesso de rede entre `mgmt-01` e as outras 5 VMs (mesma sub-rede `192.168.1.0/24`).
- O IP `192.168.1.110` (VIP) livre e fora da faixa do DHCP.
- Este repositório clonado **dentro da VM `mgmt-01`** (não no Windows/host Hyper-V) — é de lá
  que o Ansible vai orquestrar as outras 5 VMs via SSH.

```bash
# dentro da VM mgmt-01 (lab01)
git clone <url-deste-repo>
cd GitOps-LAB-Kubernetes-Observabilidade/scripts
cp inventory.example.ini inventory.ini
nano inventory.ini   # preencher IPs/usuários/senhas reais (já vêm preenchidos como exemplo)
```

### 6.2 Rodar o bootstrap

```bash
./bootstrap-cluster.sh
```

O script:
1. Instala `ansible` e `sshpass` em `mgmt-01` se não existirem.
2. Testa conectividade SSH com as 5 outras VMs (`ansible all -m ping`).
3. Executa `playbooks/site.yml`, que aplica os passos da seção 5 em ordem, **de forma
   idempotente** (pode ser executado de novo sem quebrar nada — cada tarefa verifica o
   estado atual antes de agir).

### 6.3 Validar

```bash
# ainda em mgmt-01
kubectl get nodes -o wide   # esperar 5 nós Ready (3 control-plane + 2 workers)
kubectl get pods -n kube-system   # calico-node, kube-vip, coredns, etc. Running
```

**Critério de saída:** `kubectl get nodes` mostra os 5 nós do cluster em `Ready`, e
`kubectl get pods -A` não mostra nenhum pod em `CrashLoopBackOff`/`Pending` por falta de CNI.

---

## 7. Observações de Segurança (ambiente de laboratório)

- As senhas usadas no inventário (a mesma senha simples em todas as VMs) são **adequadas apenas para
  o bootstrap inicial em rede isolada de laboratório**. Antes de expor este ambiente a
  qualquer rede menos confiável, ou ao seguir para hardening (Fase 8 do guia), troque as
  senhas e migre para autenticação por chave SSH (`ssh-copy-id`).
- `scripts/inventory.ini` contém credenciais reais e está no `.gitignore` — confirme que
  nunca foi commitado (`git log --all -- scripts/inventory.ini` deve retornar vazio).
- O bootstrap usa `ansible_become_password` (sudo) igual à senha de login — também trocar
  junto quando rotacionar credenciais.

---

## 8. Onde Isto se Encaixa no Resto do Projeto

| Pergunta | Onde procurar |
|---|---|
| "Por que kubeadm e não kind/k3s?" | [`handoff.md`](../../handoff.md), seção 7 — decisão registrada com o histórico da conversa |
| "O que vem depois do cluster estar de pé?" | [`GUIA-DE-IMPLEMENTACAO.md`](./GUIA-DE-IMPLEMENTACAO.md), a partir da Fase 3 |
| "Por que a arquitetura é dividida em base/overlays?" | [`ARQUITETURA.md`](./ARQUITETURA.md) |
| "Qual o contrato completo de cada componente (ArgoCD, observabilidade, etc.)?" | [`../PROMPT.md`](../PROMPT.md) |
| "Como rodar o provisionamento das VMs?" | Este documento, seção 6, e `scripts/` |
