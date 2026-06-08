# Cluster dev — `kind`

Cluster Kubernetes local de 3 nós (1 control-plane + 2 workers), criado com
[`kind`](https://kind.sigs.k8s.io/) dentro do WSL2 (`Ubuntu-24.04`), onde o
daemon Docker roda neste host.

## Por que dentro do WSL2?

`kind` precisa de um daemon Docker Linux. Neste host (Windows Server 2025) o
Docker roda dentro da distro WSL2 `Ubuntu-24.04` — por isso **todo** comando
deste guia (e os scripts em `scripts/`) deve ser executado de dentro dela:

```bash
wsl -d Ubuntu-24.04
cd /caminho/para/o/repo
```

## Subir o cluster

Prefira sempre `make up` / `scripts/bootstrap-dev.sh` (idempotentes — criam o
cluster só se ele ainda não existir). Para subir manualmente:

```bash
kind create cluster --name devcluster --config clusters/dev/kind-config.yaml
kubectl cluster-info --context kind-devcluster
kubectl get nodes -o wide   # esperar os 3 nós em "Ready"
```

## Destruir o cluster

```bash
kind delete cluster --name devcluster
# ou: make down / scripts/teardown-dev.sh
```

## Detalhes da configuração (`kind-config.yaml`)

| Item | Valor | Motivo |
|---|---|---|
| Nós | 1 control-plane + 2 workers | Simula topologia mínima de produção (permite testar `topologySpreadConstraints`, `PodDisruptionBudget`, anti-afinidade) |
| `extraPortMappings` | `80→80`, `443→443` no control-plane, `listenAddress: 127.0.0.1` | Permite que o NGINX Ingress (modo `hostNetwork` em dev) receba tráfego do host via `*.local.dev` → `127.0.0.1` |
| `node-labels: ingress-ready=true` | label no control-plane | Usado pelo `nodeSelector` do overlay dev do NGINX Ingress para fixar o controller no nó com as portas mapeadas |
| CNI | padrão (`kindnet`) | Suficiente para o MVP e compatível com `NetworkPolicy` a partir do kind ≥ 0.20 |

## Acessar os serviços

Depois que o ArgoCD sincronizar tudo (ver [`../../argocd/apps/`](../../argocd/apps/)),
os serviços ficam acessíveis em `https://<nome>.local.dev`, desde que o snippet
de `/etc/hosts` em [`../../dns/hosts-snippet.txt`](../../dns/hosts-snippet.txt)
tenha sido aplicado — tanto no `/etc/hosts` do WSL2 quanto no
`C:\Windows\System32\drivers\etc\hosts` do Windows (o navegador roda no Windows).
