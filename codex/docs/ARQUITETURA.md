# Arquitetura - Plataforma GitOps Kubernetes Codex

## Visao Geral

Esta arquitetura descreve uma plataforma GitOps em camadas.

A diferenca principal desta versao Codex e a ordem de entrega: primeiro um MVP pequeno,
funcional e validavel; depois as capacidades avancadas.

O objetivo e evitar uma implementacao grande demais antes de provar o fluxo principal:

```text
Git -> ArgoCD -> Kubernetes -> Ingress -> Aplicacao -> Monitoramento
```

## Diagramas de Arquitetura

### Visao de Componentes

```mermaid
flowchart TB
    subgraph Repo["Repositorio GitOps"]
        Prompt["codex/PROMPT.md"]
        Base["infra/base"]
        DevOverlay["infra/overlays/dev"]
        ProdOverlay["infra/overlays/prod"]
        Apps["argocd/apps"]
        CI[".github/workflows"]
    end

    subgraph Dev["Cluster DEV - kind"]
        ArgoDev["ArgoCD"]
        NginxDev["NGINX Ingress"]
        CertDev["cert-manager self-signed"]
        HeadlampDev["Headlamp"]
        GrafanaDev["Grafana"]
        PromDev["Prometheus"]
        SampleDev["sample-app"]
    end

    subgraph Prod["Cluster PROD - cloud-agnostic"]
        ArgoProd["ArgoCD HA/SSO"]
        NginxProd["NGINX Ingress HA"]
        CertProd["cert-manager Let's Encrypt"]
        ExtDNS["external-dns"]
        GrafanaProd["Grafana"]
        PromProd["Prometheus"]
        Velero["Velero"]
        SampleProd["sample-app"]
    end

    Base --> DevOverlay
    Base --> ProdOverlay
    DevOverlay --> Apps
    ProdOverlay --> Apps
    Apps --> ArgoDev
    Apps --> ArgoProd
    ArgoDev --> NginxDev
    ArgoDev --> CertDev
    ArgoDev --> HeadlampDev
    ArgoDev --> GrafanaDev
    ArgoDev --> PromDev
    ArgoDev --> SampleDev
    ArgoProd --> NginxProd
    ArgoProd --> CertProd
    ArgoProd --> ExtDNS
    ArgoProd --> GrafanaProd
    ArgoProd --> PromProd
    ArgoProd --> Velero
    ArgoProd --> SampleProd
    CI --> Repo
```

### Acesso Web e Entrada de Trafego

```mermaid
flowchart LR
    Browser["Browser"]

    subgraph DevPath["DEV local"]
        Hosts["hosts explicitos local.dev"]
        LocalPorts["localhost 80/443"]
        KindPorts["kind extraPortMappings"]
        IngressDev["NGINX Ingress"]
        ServiceDev["Service"]
        PodDev["Pod"]
    end

    subgraph ProdPath["PROD cloud-agnostic"]
        DNS["DNS real"]
        LB["Kubernetes LoadBalancer"]
        IngressProd["NGINX Ingress"]
        ServiceProd["Service"]
        PodProd["Pod"]
    end

    subgraph AwsOptional["Adaptacao AWS opcional"]
        Route53["Route53"]
        ALB["AWS ALB"]
        AwsController["AWS Load Balancer Controller"]
    end

    Browser --> Hosts --> LocalPorts --> KindPorts --> IngressDev --> ServiceDev --> PodDev
    Browser --> DNS --> LB --> IngressProd --> ServiceProd --> PodProd
    Browser -. opcional AWS .-> Route53 --> ALB --> AwsController -. gerencia .-> IngressProd
```

### Fluxo GitOps e Promocao

```mermaid
sequenceDiagram
    participant Dev as Desenvolvedor
    participant Repo as GitHub Repo
    participant CI as GitHub Actions
    participant GHCR as GHCR
    participant PR as Pull Request
    participant Argo as ArgoCD
    participant K8s as Kubernetes

    Dev->>Repo: push sample-app
    Repo->>CI: dispara pipeline
    CI->>CI: test + build + Trivy + cosign
    CI->>GHCR: publica imagem :sha
    CI->>PR: abre PR atualizando overlay dev/prod
    PR->>Repo: merge aprovado
    Argo->>Repo: detecta mudanca no Git
    Argo->>K8s: sincroniza manifests
    K8s-->>Argo: health e sync status
```

### Observabilidade

```mermaid
flowchart TB
    subgraph Cluster["Cluster Kubernetes"]
        Nodes["Nodes"]
        Pods["Pods e containers"]
        Ingress["NGINX Ingress"]
        Argo["ArgoCD"]
        Certs["cert-manager"]
        App["sample-app"]
    end

    Prom["Prometheus"]
    Grafana["Grafana"]
    Alertmanager["Alertmanager"]
    Rules["PrometheusRule"]
    Dashboards["Dashboards as code"]

    Nodes --> Prom
    Pods --> Prom
    Ingress --> Prom
    Argo --> Prom
    Certs --> Prom
    App --> Prom
    Rules --> Prom
    Prom --> Grafana
    Prom --> Alertmanager
    Dashboards --> Grafana
```

## Camadas

### 1. Cluster

No ambiente dev, o cluster roda com `kind`.

Composicao:

- 1 control-plane.
- 2 workers.
- portas 80 e 443 mapeadas para o host.
- CNI padrao do kind no MVP.

Em producao, o repositorio nao cria o cluster. Ele apenas documenta os requisitos minimos:

- Kubernetes >= 1.28.
- StorageClass dinamica.
- mecanismo de LoadBalancer.
- acesso a internet para imagens, Let's Encrypt e repositorios.
- permissao para instalar CRDs.

### 2. GitOps

ArgoCD e o reconciliador principal.

Existe uma fase inicial de bootstrap, na qual o script instala o ArgoCD. Depois disso,
o ArgoCD assume o controle dos demais componentes.

Padrao:

- `argocd/apps/app-of-apps-dev.yaml` como raiz dev.
- `argocd/apps/app-of-apps-prod.yaml` como raiz prod.
- `ApplicationSet` para evolucao multiambiente.

### 3. Manifests

Os manifests seguem o modelo:

```text
infra/base
infra/overlays/dev
infra/overlays/prod
```

A base contem o que e comum.
O overlay contem apenas o que muda por ambiente.

Exemplos de diferencas:

| Item | Dev | Prod |
|---|---|---|
| Dominio | `*.local.dev` com hosts explicitos | dominio real |
| TLS | self-signed | Let's Encrypt |
| Replicas | 1 | 2 ou mais |
| Storage | local/pequeno | persistente |
| PSS | baseline | restricted |
| ArgoCD | simples | HA/SSO |
| Alertas | local | rotas reais |

### 4. Entrada Web

No dev:

```text
Browser
  -> hosts locais
  -> localhost:80/443
  -> kind extraPortMappings
  -> NGINX Ingress Controller
  -> Service
  -> Pod
```

Em producao cloud-agnostic:

```text
Browser
  -> DNS real
  -> LoadBalancer Kubernetes
  -> NGINX Ingress Controller
  -> Service
  -> Pod
```

Em AWS, isso pode ser adaptado para ALB usando AWS Load Balancer Controller, mas essa
adaptacao fica documentada fora do caminho padrao para manter o projeto portavel.

## Paineis Web

### ArgoCD

URL dev:

```text
https://argocd.local.dev
```

Funcao:

- GitOps;
- sync;
- diff Git vs cluster;
- historico de deploy;
- status de aplicacoes;
- arvore de recursos Kubernetes.

ArgoCD mostra pods e imagens, mas nao e um gerenciador de containers como Portainer.
Ele ve containers pela lente de `Deployment`, `ReplicaSet` e `Pod`.

### Headlamp

URL dev:

```text
https://headlamp.local.dev
```

Funcao:

- gestao visual do cluster;
- namespaces;
- pods;
- services;
- ingress;
- logs;
- events;
- troubleshooting operacional.

### Grafana

URL dev:

```text
https://grafana.local.dev
```

Funcao:

- dashboards;
- CPU/memoria por node e pod;
- reinicios;
- disponibilidade;
- metricas de ingress;
- metricas de ArgoCD;
- status de certificados.

### Prometheus

URL dev:

```text
https://prometheus.local.dev
```

Funcao:

- PromQL;
- targets;
- rules;
- metricas brutas.

### Alertmanager

URL dev:

```text
https://alertmanager.local.dev
```

Funcao:

- alertas ativos;
- silenciamentos;
- rotas de notificacao.

## Seguranca

Seguranca entra em duas etapas.

No MVP:

- acesso local;
- TLS self-signed;
- credenciais iniciais documentadas;
- sem segredo puro em manifests.

Na fase de hardening:

- Sealed Secrets;
- NetworkPolicy default-deny;
- Pod Security Standards;
- RBAC minimo;
- assinatura de imagem;
- scan de vulnerabilidades;
- validacao futura com policy engine.

## Observabilidade

O monitoramento usa `kube-prometheus-stack`.

Componentes:

- Prometheus;
- Grafana;
- Alertmanager;
- node-exporter;
- kube-state-metrics;
- ServiceMonitors.

Dashboards e alertas devem ser versionados no repositorio.

## CI/CD

O CI nao aplica no cluster.

Fluxo esperado:

```text
push
  -> GitHub Actions
  -> testes
  -> build
  -> Trivy scan
  -> cosign sign
  -> push GHCR
  -> PR alterando tag no overlay
  -> merge
  -> ArgoCD sync
```

## Producao

O overlay prod deve ser renderizavel mesmo sem cluster de producao disponivel.

Ele deve preparar:

- TLS Let's Encrypt;
- replicas maiores;
- storage persistente;
- PSS restricted;
- configuracao para DNS real;
- Velero;
- ArgoCD com caminho para SSO/HA.

## Decisoes Codex

1. MVP antes de plataforma completa.
2. Sealed Secrets como primeira solucao de segredos.
3. `.github/workflows` na raiz, nao dentro de pasta auxiliar.
4. Hosts explicitos no dev, porque `/etc/hosts` nao suporta wildcard.
5. Prod cloud-agnostic como padrao.
6. AWS ALB como adaptacao documentada, nao como dependencia inicial.
