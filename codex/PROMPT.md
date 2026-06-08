# PROMPT: Plataforma GitOps Kubernetes - Implementacao Codex

## Objetivo

Voce e um Platform Engineer senior trabalhando neste repositorio
`GitOps-LAB-Kubernetes-Observabilidade`.

Sua tarefa e construir uma plataforma GitOps Kubernetes com dois objetivos:

1. Rodar localmente em ambiente de laboratorio usando `kind`.
2. Servir como base promovivel para producao, com mudancas pequenas, auditaveis e revisadas.

O foco desta implementacao Codex e entregar primeiro um **MVP GitOps funcional**, e depois
evoluir em camadas: observabilidade, seguranca, CI/CD, segredos, backup e producao.

## Principio Central

O cluster deve refletir o Git.

Depois do bootstrap inicial do ArgoCD, nenhuma mudanca estrutural deve ser feita com
`kubectl apply` manual. Alteracoes devem entrar no repositorio, passar por revisao e ser
sincronizadas pelo ArgoCD.

## Escopo MVP

O MVP deve entregar:

- Cluster local `kind` com 3 nos.
- ArgoCD instalado e acessivel via web.
- Padrao GitOps com `infra/base` e `infra/overlays/dev`.
- NGINX Ingress Controller.
- cert-manager com certificado self-signed para dev.
- Sample app publicada via HTTPS.
- Headlamp para visualizacao operacional do cluster.
- Grafana/Prometheus basicos para monitoramento.
- `make up`, `make down`, `make status` e `make smoke-test`.

## Escopo Evolutivo

Apos o MVP, implementar:

- `infra/overlays/prod` renderizavel.
- NetworkPolicies default-deny com excecoes explicitas.
- Pod Security Standards: `baseline` em dev e `restricted` em prod.
- Sealed Secrets para o laboratorio.
- GitHub Actions com build, test, scan Trivy, assinatura cosign e push GHCR.
- Promocao dev -> prod via Pull Request automatizado.
- Velero para backup e restore.
- Runbook operacional.

## Stack

- Kubernetes local: `kind`.
- Kubernetes prod: qualquer cluster Kubernetes >= 1.28.
- GitOps: ArgoCD.
- Manifests: Kustomize `base/` + `overlays/<env>/`.
- Ingress: NGINX Ingress Controller.
- TLS: cert-manager.
- Dashboard Kubernetes: Headlamp.
- Monitoramento: kube-prometheus-stack.
- Segredos: Sealed Secrets no MVP; External Secrets como evolucao.
- CI/CD: GitHub Actions, GHCR, Trivy, cosign.
- Backup: Velero.

## Estrutura Esperada

```text
.
├── clusters/
│   ├── dev/
│   │   ├── kind-config.yaml
│   │   └── README.md
│   └── prod/
│       └── README.md
│
├── infra/
│   ├── base/
│   │   ├── namespaces/
│   │   ├── ingress-nginx/
│   │   ├── cert-manager/
│   │   ├── argocd/
│   │   ├── monitoring/
│   │   ├── headlamp/
│   │   ├── sealed-secrets/
│   │   ├── network-policies/
│   │   └── backup/
│   └── overlays/
│       ├── dev/
│       └── prod/
│
├── argocd/
│   └── apps/
│       ├── app-of-apps-dev.yaml
│       ├── app-of-apps-prod.yaml
│       └── applicationset-platform.yaml
│
├── observability/
│   ├── dashboards/
│   └── alerts/
│
├── dns/
│   ├── hosts-snippet.txt
│   └── README.md
│
├── sample-app/
│   ├── src/
│   ├── Dockerfile
│   └── k8s/
│       ├── base/
│       └── overlays/
│           ├── dev/
│           └── prod/
│
├── scripts/
│   ├── check-prerequisites.sh
│   ├── bootstrap-dev.sh
│   ├── teardown-dev.sh
│   └── smoke-test.sh
│
├── .github/
│   └── workflows/
│       ├── ci.yaml
│       └── cd-promote.yaml
│
├── docs/
│   ├── ARQUITETURA.md
│   ├── GUIA-DE-IMPLEMENTACAO.md
│   └── RUNBOOK.md
│
├── Makefile
└── README.md
```

## Acessos Web no Ambiente Dev

Usar hosts explicitos, porque `/etc/hosts` nao suporta wildcard real.

```text
https://argocd.local.dev
https://headlamp.local.dev
https://grafana.local.dev
https://prometheus.local.dev
https://alertmanager.local.dev
https://app.local.dev
```

## Responsabilidade de Cada Painel

### ArgoCD

Painel de GitOps.

Usado para:

- visualizar aplicacoes;
- comparar Git vs cluster;
- sincronizar aplicacoes;
- ver historico de deploy;
- diagnosticar erro de manifesto;
- acompanhar App of Apps e ApplicationSets.

ArgoCD ve pods e containers indiretamente, por meio de recursos Kubernetes como
`Deployment`, `ReplicaSet` e `Pod`. Ele nao substitui um painel operacional de cluster.

### Headlamp

Painel operacional Kubernetes.

Usado para:

- visualizar namespaces;
- visualizar pods;
- ver logs;
- inspecionar services, ingresses e configmaps;
- acompanhar events;
- entender o estado atual do cluster.

### Grafana, Prometheus e Alertmanager

Painel de monitoramento e alerta.

Grafana e o painel principal. Prometheus e usado para PromQL, targets e regras.
Alertmanager gerencia alertas, rotas e silenciamentos.

## Regras de Implementacao

1. Comecar pelo MVP.
2. Validar cada fase antes de seguir.
3. Evitar duplicacao entre `base` e `overlays`.
4. Nao guardar segredo puro no Git.
5. Nao usar `cluster-admin` para aplicacoes.
6. Todo workload deve ter `resources.requests` e `resources.limits`.
7. Producao deve ser cloud-agnostic por padrao.
8. Recursos especificos de AWS, Azure ou GCP devem ficar documentados como adaptacoes.

## Criterios de Aceite do MVP

- `make up` cria ou reutiliza o cluster dev.
- ArgoCD fica acessivel em `https://argocd.local.dev`.
- Headlamp fica acessivel em `https://headlamp.local.dev`.
- Grafana fica acessivel em `https://grafana.local.dev`.
- Sample app responde em `https://app.local.dev`.
- ArgoCD mostra as aplicacoes `Synced` e `Healthy`.
- `make smoke-test` valida nodes, apps, certificados e endpoints.

## Criterios de Aceite Final

- Dev sobe do zero de forma idempotente.
- Prod overlay renderiza sem erro.
- CI constroi, testa, escaneia, assina e publica imagem.
- Promocao para prod acontece por PR.
- Dashboards e alertas sao versionados.
- NetworkPolicy default-deny ativa.
- PSS aplicado por ambiente.
- Sealed Secrets implementado.
- Velero configurado e restore documentado.
- `docs/RUNBOOK.md` cobre operacoes principais.
