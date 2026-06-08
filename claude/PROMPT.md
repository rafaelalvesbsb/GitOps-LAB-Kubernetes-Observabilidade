# PROMPT: Plataforma GitOps Kubernetes Multi-Ambiente — Dev + Produção

## 🎯 OBJETIVO GERAL

Você é um engenheiro DevOps/Platform Engineer sênior. Sua tarefa é construir, dentro deste
repositório (`GitOps-LAB-Kubernetes-Observabilidade`), uma **plataforma GitOps de referência**
que funcione tanto em um **laboratório local (dev)** quanto possa ser promovida, com mudanças
mínimas e auditáveis, para um **cluster de produção cloud-agnostic**.

Diferente de um "script gigante que faz tudo de uma vez", o resultado deve ser um repositório
GitOps real: declarativo, versionado, idempotente, com separação clara entre **base** (o que é
igual em qualquer lugar) e **overlay** (o que muda por ambiente), seguindo o padrão
**Kustomize `base/` + `overlays/<env>/`** orquestrado pelo ArgoCD via **App of Apps /
ApplicationSets**.

Stack:

- Cluster Kubernetes (dev: `kind` 3 nós; prod: qualquer cluster K8s ≥ 1.28 — EKS/GKE/AKS/k3s/bare-metal)
- Ingress Controller (NGINX)
- cert-manager (TLS — self-signed em dev, Let's Encrypt em prod)
- ArgoCD (GitOps CD, App of Apps + ApplicationSets por ambiente)
- GitHub Actions (CI: build, test, scan, assinatura de imagem, promoção de versão)
- kube-prometheus-stack — Prometheus + Grafana + Alertmanager (observabilidade)
- Headlamp (dashboard web do cluster)
- CoreDNS customizado (dev) / external-dns + DNS real (prod)
- Sealed Secrets ou External Secrets Operator (gestão de segredos sem segredo em texto puro no Git)
- Velero (backup e disaster recovery)
- NetworkPolicies (deny-all por padrão + exceções explícitas)
- Pod Security Standards (`baseline` em dev, `restricted` em prod)

---

## 🧭 PRINCÍPIOS QUE GUIAM ESTA VERSÃO (o que muda em relação a um "bootstrap script só pra dev")

1. **Um único conjunto de manifests, dois (ou mais) ambientes.** Nada de duplicar YAML —
   tudo que é específico de ambiente (domínio, réplicas, recursos, classe de armazenamento,
   emissor de certificado, política de sync) vive em `overlays/<env>/`, nunca espalhado pela base.
2. **GitOps de verdade.** O estado desejado do cluster é 100% derivado do conteúdo deste
   repositório. `kubectl apply` manual é proibido após o bootstrap inicial — toda mudança
   passa por PR + ArgoCD sync.
3. **Cloud-agnostic em produção.** Nenhum manifesto de prod deve depender de uma API
   proprietária de nuvem (ALB Ingress Controller da AWS, Cloud DNS do GCP etc.). Use
   abstrações padrão (`Ingress`, `LoadBalancer`/MetalLB, `cert-manager` com `HTTP01`/`DNS01`
   configurável, `external-dns` com provider plugável). Documente os pontos de extensão
   para quem quiser amarrar a um provider específico depois.
4. **Segurança desde o dia 1, não como item de TODO.** `restricted` Pod Security Standard,
   NetworkPolicy default-deny, RBAC de menor privilégio, segredos nunca em texto puro no Git,
   imagens escaneadas e assinadas, no `cluster-admin` para apps.
5. **Idempotência e reprodutibilidade.** Bootstrap pode rodar N vezes sem quebrar nada.
   Nenhuma etapa manual além de "rodar o script" e "abrir o PR".
6. **Observabilidade como produto, não acessório.** Dashboards e alertas versionados como
   código (`ConfigMap`/`PrometheusRule`/`GrafanaDashboard`), não clicados manualmente na UI.

---

## 📁 ESTRUTURA DE DIRETÓRIOS ESPERADA

```
.
├── clusters/
│   ├── dev/
│   │   ├── kind-config.yaml          # cluster kind (1 control-plane + 2 workers)
│   │   └── README.md                 # como subir o cluster local
│   └── prod/
│       └── README.md                 # requisitos do cluster alvo (versão, addons, storageclass...)
│
├── infra/
│   ├── base/                         # manifests/Kustomizations cloud-agnostic e env-agnostic
│   │   ├── namespaces/
│   │   ├── ingress-nginx/
│   │   ├── cert-manager/
│   │   ├── argocd/
│   │   ├── monitoring/               # kube-prometheus-stack (HelmRelease/values base)
│   │   ├── headlamp/
│   │   ├── coredns/                  # patch base do CoreDNS
│   │   ├── network-policies/
│   │   ├── secrets-management/       # Sealed Secrets / External Secrets Operator
│   │   └── backup/                   # Velero
│   │
│   └── overlays/
│       ├── dev/                      # *.local.dev, TLS self-signed, 1 réplica, retenção curta
│       │   ├── ingress-nginx/
│       │   ├── cert-manager/
│       │   ├── argocd/
│       │   ├── monitoring/
│       │   └── kustomization.yaml
│       └── prod/                     # domínio real, Let's Encrypt, HA, retenção longa, PSS restricted
│           ├── ingress-nginx/
│           ├── cert-manager/
│           ├── argocd/
│           ├── monitoring/
│           └── kustomization.yaml
│
├── argocd/
│   └── apps/
│       ├── app-of-apps-dev.yaml      # raiz do ambiente dev
│       ├── app-of-apps-prod.yaml     # raiz do ambiente prod
│       └── applicationset-platform.yaml  # ApplicationSet que gera Apps por ambiente/cluster
│
├── observability/
│   ├── dashboards/                   # JSON dos dashboards Grafana (as code)
│   ├── alerts/                       # PrometheusRule (PodCrashLooping, HighMemory, etc.)
│   └── slo/                          # definições de SLO/SLI (opcional, fase 2)
│
├── dns/
│   ├── coredns-custom-cm.yaml        # zona *.local.dev (dev)
│   └── hosts-snippet.txt             # bloco sugerido para /etc/hosts (dev)
│
├── github-actions/.github/workflows/
│   ├── ci.yaml                       # build, test, trivy scan, cosign sign, push GHCR
│   └── cd-promote.yaml               # promove tag de dev → prod via PR automatizado
│
├── sample-app/
│   ├── src/
│   ├── Dockerfile
│   └── k8s/
│       ├── base/                     # Deployment, Service, Ingress, HPA, NetworkPolicy
│       └── overlays/{dev,prod}/
│
├── scripts/
│   ├── check-prerequisites.sh        # valida docker/kubectl/helm/kind/jq etc.
│   ├── bootstrap-dev.sh              # sobe kind + aplica app-of-apps-dev (idempotente)
│   ├── teardown-dev.sh               # destrói o cluster dev com segurança
│   └── smoke-test.sh                 # valida endpoints, pods Ready, certificados emitidos
│
├── docs/
│   ├── ARQUITETURA.md
│   ├── GUIA-DE-IMPLEMENTACAO.md
│   ├── RUNBOOK.md                    # procedimentos operacionais (rotacionar secret, restaurar backup...)
│   └── diagrams/                     # diagramas Mermaid versionados
│
├── Makefile                          # make up | down | status | logs | port-forward | smoke-test
└── README.md
```

---

## 🔧 REQUISITOS TÉCNICOS DETALHADOS

### 1. Clusters

**Dev — `kind`:**
- 1 control-plane + 2 workers, `extraPortMappings` para 80/443, CoreDNS habilitado.
- Subido via `scripts/bootstrap-dev.sh`, que precisa ser **idempotente**: se o cluster já
  existe, reaproveita; se não, cria.

**Prod — cloud-agnostic:**
- Não provisionamos o cluster em si neste repositório (isso é trabalho de IaC/Terraform,
  fora de escopo aqui) — documentamos em `clusters/prod/README.md` os **requisitos mínimos**:
  versão do K8s, StorageClass com `ReadWriteOnce` dinâmico, um mecanismo de `LoadBalancer`
  (cloud LB nativo ou MetalLB on-prem), e acesso de saída para `letsencrypt-prod` e GHCR.
- O overlay `overlays/prod/` assume apenas essas garantias — nada provider-specific.

### 2. Namespaces, RBAC e Pod Security Standards

- Namespaces: `ingress-nginx`, `argocd`, `monitoring`, `dashboard`, `cert-manager`,
  `apps`, `external-secrets` (ou `kube-system` para Sealed Secrets), `velero`.
- Labels de **Pod Security Standards** por overlay:
  - dev → `pod-security.kubernetes.io/enforce: baseline`
  - prod → `pod-security.kubernetes.io/enforce: restricted`
- RBAC de menor privilégio: `ServiceAccount dev-reader` em `apps` com `ClusterRole view`;
  nenhuma aplicação recebe `cluster-admin`.

### 3. Ingress Controller (NGINX)

- Helm values base + overlay. Base define métricas habilitadas (porta 10254), headers de
  segurança (`X-Frame-Options`, `Content-Security-Policy`, etc.) e `resources.requests/limits`.
- Overlay dev: `hostNetwork: true` / `NodePort` (compatível com `kind`).
- Overlay prod: `service.type: LoadBalancer`, `replicaCount` ≥ 2 com `PodDisruptionBudget`
  e `topologySpreadConstraints`.

### 4. cert-manager + TLS

- Base instala CRDs e o controller.
- Overlay dev: `ClusterIssuer selfsigned-issuer` + `Certificate` wildcard `*.local.dev`.
- Overlay prod: `ClusterIssuer letsencrypt-prod` configurável para `HTTP01` (padrão,
  cloud-agnostic) **ou** `DNS01` (plugável por provider, documentado mas não hard-coded).

### 5. ArgoCD (GitOps Engine)

- Base: Helm values comuns (RBAC, `configs.repositories`, Notifications controller,
  ResourceCustomizations para health checks customizados).
- Overlay dev: `server.insecure: true` (TLS termina no Ingress local), 1 réplica, Redis standalone.
- Overlay prod: TLS ponta a ponta, `server.replicas` ≥ 2, **Redis HA**, `applicationsetController`
  habilitado, SSO via OIDC.
- **App of Apps + ApplicationSet**: um `ApplicationSet` gera as `Application` filhas a partir
  de um *generator* de diretórios (`overlays/{dev,prod}/...`), eliminando duplicação manual de
  manifestos de Application por ambiente.
- `syncPolicy.automated.{prune,selfHeal}` habilitado em dev; em prod, `selfHeal` habilitado mas
  com `syncWindows` e `Notifications` para alertar antes/depois de cada sync em horário comercial.

### 6. CI/CD com GitHub Actions

**`ci.yaml` — Build, Test, Scan, Sign, Push:**
- `actions/checkout`, build multi-stage com Buildx + cache GHA.
- Testes automatizados do `sample-app` antes do build da imagem.
- **Scan de vulnerabilidades com Trivy** (falha o pipeline em CRITICAL/HIGH não whitelisted).
- **Assinatura de imagem com `cosign`** (keyless, via OIDC do GitHub) — produção só roda
  imagens assinadas (verificado por admission policy, ex.: Kyverno/Sigstore policy-controller — fase 2).
- Push para GHCR com tags `latest` + `sha` + `semver` (quando aplicável).

**`cd-promote.yaml` — Promoção dev → prod:**
- Em vez de `sed` direto no manifesto (frágil e sem revisão), abre **Pull Request automatizado**
  no próprio repo GitOps atualizando `sample-app/k8s/overlays/prod/kustomization.yaml`
  (`images: newTag: <sha>`), exigindo aprovação humana antes do merge.
- ArgoCD detecta o merge em `main` e sincroniza prod (`selfHeal` + `prune`).

### 7. Observabilidade (kube-prometheus-stack)

- Base: Prometheus + Grafana + Alertmanager com `ServiceMonitor`s para ArgoCD e NGINX Ingress.
- Overlay dev: retenção 7d, armazenamento `emptyDir`/StorageClass local pequena, 1 réplica,
  `adminPassword` lido de Secret local (nunca hard-coded em texto puro, nem em dev).
- Overlay prod: retenção 30d+, `volumeClaimTemplate` com StorageClass dinâmica de 20Gi+,
  Alertmanager com 3 réplicas e roteamento real (Slack/email/PagerDuty via Secret externo).
- **Dashboards e alertas como código**: JSON em `observability/dashboards/`, `PrometheusRule`
  em `observability/alerts/` (`PodCrashLooping`, `HighMemoryUsage`, `CertificateExpiringSoon`,
  `ArgoCDSyncFailed`, `IngressHighErrorRate`, etc.).

### 8. Dashboard Web do Cluster (Headlamp)

- Overlay dev: acesso via `Ingress` com TLS self-signed, autenticação via token de
  ServiceAccount.
- Overlay prod: autenticação via **OIDC** (mesmo provider do ArgoCD, se possível), RBAC
  read-only por padrão.

### 9. DNS

- Dev: ConfigMap de patch do CoreDNS interno (zona `*.local.dev` → service do Ingress) +
  snippet de `/etc/hosts` para a máquina host. `dnsmasq` documentado como opcional para
  wildcard automático.
- Prod: **`external-dns`** cloud-agnostic (suporta múltiplos providers via configuração),
  criando registros reais a partir das anotações dos `Ingress`/`Service`. Nenhum hard-code
  de provider — escolha feita via `values` do overlay.

### 10. Gestão de Segredos

- **Nenhum segredo em texto puro no Git, em nenhum ambiente.** Adote **Sealed Secrets**
  (mais simples para o lab, criptografa no client e descriptografa só no cluster) **ou**
  **External Secrets Operator** (busca de um vault externo — mais alinhado a prod real).
  Documentar a escolha e o trade-off; implementar ao menos a primeira opção de ponta a ponta.

### 11. Network Policies

- `default-deny-all` por namespace de aplicação, com exceções explícitas
  (`allow-ingress-from-nginx`, `allow-dns-egress`, `allow-monitoring-scrape`).
- Habilitado em ambos os ambientes — dev precisa replicar o comportamento de prod para que
  bugs de política sejam descobertos cedo.

### 12. Backup & Disaster Recovery (Velero)

- Instalado via base; overlay prod aponta para um *object storage* compatível com S3
  (qualquer provider — MinIO on-prem incluso) e agenda backups diários dos namespaces
  críticos (`argocd`, `monitoring`, `apps`).
- Documentar e **testar** o procedimento de restore no `docs/RUNBOOK.md`.

---

## 🧪 BOOTSTRAP E VALIDAÇÃO

`scripts/bootstrap-dev.sh` deve, em ordem e de forma idempotente:

1. Validar pré-requisitos (`scripts/check-prerequisites.sh`: docker, kubectl, helm, kind, jq, cosign...).
2. Criar (ou reaproveitar) o cluster `kind`.
3. Instalar o ArgoCD mínimo (bootstrap "chicken-and-egg").
4. Aplicar o `app-of-apps-dev.yaml` — **a partir daqui, o ArgoCD assume o controle** de tudo
   o mais (namespaces, ingress, cert-manager, monitoring, headlamp, sample-app...).
5. Aguardar e validar saúde das `Application`s (`argocd app wait` ou polling via `kubectl`).
6. Rodar `scripts/smoke-test.sh`: valida endpoints HTTPS, certificados emitidos,
   pods `Ready`, dashboards do Grafana acessíveis, ArgoCD sincronizado.
7. Imprimir credenciais iniciais (ArgoCD admin, Grafana) e URLs de acesso.

`Makefile` expõe: `make up`, `make down`, `make status`, `make logs`, `make port-forward`,
`make smoke-test`.

---

## 🔐 SEGURANÇA E BOAS PRÁTICAS (não-negociáveis)

1. Pod Security Standards: `baseline` (dev) / `restricted` (prod) — `runAsNonRoot`,
   `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, `seccompProfile: RuntimeDefault`.
2. NetworkPolicy deny-all + exceções explícitas, em ambos os ambientes.
3. `resources.requests` e `resources.limits` obrigatórios em todo `Deployment`/`StatefulSet`.
4. Nenhum segredo em texto puro no Git — Sealed Secrets ou External Secrets Operator.
5. Imagens escaneadas (Trivy) e assinadas (cosign) no CI; admission policy valida assinatura
   antes de agendar pods em prod (documentar como evolução de fase 2 caso não dê tempo de implementar).
6. RBAC mínimo — nunca `cluster-admin` para aplicações.
7. Backups testados (Velero) com runbook de restore validado manualmente ao menos uma vez.

---

## 📋 PRÉ-REQUISITOS DA MÁQUINA HOST

```
docker          # >= 24.x  (rodar em WSL2/Linux — kind exige daemon Docker)
kubectl         # >= 1.28
helm            # >= 3.12
kind            # >= 0.20
kustomize       # (ou kubectl kustomize embutido)
cosign          # assinatura de imagens
trivy           # scan de vulnerabilidades local (opcional, CI já roda)
git, curl, jq
```

Validar tudo via `scripts/check-prerequisites.sh` antes do bootstrap.

---

## 🎯 ENTREGÁVEIS / CRITÉRIOS DE ACEITE

- [ ] Repositório segue o padrão `base/` + `overlays/{dev,prod}` sem duplicação de manifesto
- [ ] `make up` sobe o ambiente dev local do zero, de forma idempotente, em < ~15 minutos
- [ ] Todos os serviços acessíveis via HTTPS em `*.local.dev` (dev) com certificado válido
      (mesmo que self-signed) e sem editar `/etc/hosts` manualmente além do bootstrap inicial
- [ ] ArgoCD sincronizando automaticamente a partir do App of Apps (`selfHeal` + `prune`)
- [ ] Pipeline CI completo: build → test → scan (Trivy) → assinatura (cosign) → push GHCR
- [ ] Promoção dev → prod via Pull Request automatizado, não via `sed` direto no manifesto
- [ ] Grafana com dashboards versionados (cluster, pods, NGINX, ArgoCD, certificados)
- [ ] Alertas (`PrometheusRule`) versionados cobrindo cenários críticos comuns
- [ ] NetworkPolicy default-deny ativa, com exceções documentadas, em ambos os ambientes
- [ ] Pod Security Standards aplicados (`baseline` dev / `restricted` prod)
- [ ] Segredos geridos via Sealed Secrets/External Secrets — zero segredo em texto puro no Git
- [ ] Backup configurado (Velero) com procedimento de restore documentado e testado
- [ ] `smoke-test.sh` validando o ambiente ponta a ponta, usável em CI também
- [ ] `docs/ARQUITETURA.md`, `docs/GUIA-DE-IMPLEMENTACAO.md` e `docs/RUNBOOK.md` completos

---

## 🗒️ OBSERVAÇÕES FINAIS

- Gere diagramas de arquitetura em **Mermaid**, versionados em `docs/diagrams/`.
- Documente explicitamente **o que muda** ao promover de dev para prod — isso é o coração
  deste design (overlay diff deve ser pequeno e legível).
- Cada decisão "cloud-agnostic" deve vir acompanhada de uma nota de "como adaptar para
  AWS/GCP/Azure especificamente", para não deixar o operador real na mão.
- Releases e mudanças de infraestrutura passam por PR — trate este repositório com o mesmo
  rigor de revisão que código de aplicação.
