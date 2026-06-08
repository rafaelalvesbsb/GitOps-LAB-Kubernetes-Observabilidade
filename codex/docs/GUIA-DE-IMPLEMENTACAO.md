# Guia de Implementacao - Plataforma GitOps Kubernetes Codex

## Ordem Recomendada

Esta implementacao deve ser feita em fases pequenas. Cada fase precisa ter um criterio de
saida objetivo antes de seguir para a proxima.

## Fase 0 - Preparar o Repositorio

Criar:

- `README.md`
- `Makefile`
- `clusters/dev/kind-config.yaml`
- `scripts/check-prerequisites.sh`
- `scripts/bootstrap-dev.sh`
- `scripts/teardown-dev.sh`
- `scripts/smoke-test.sh`
- estrutura `infra/base`
- estrutura `infra/overlays/dev`
- estrutura `argocd/apps`

Criterio de saida:

```bash
make status
```

deve rodar sem erro de sintaxe, mesmo que o cluster ainda nao exista.

## Fase 1 - Pre-requisitos

Validar:

- docker;
- kubectl;
- helm;
- kind;
- kustomize ou `kubectl kustomize`;
- jq;
- curl;
- git.

Ferramentas como `cosign` e `trivy` podem entrar na fase de CI/CD, para nao bloquear o MVP.

Criterio de saida:

```bash
scripts/check-prerequisites.sh
```

mostra as versoes e falha com mensagens claras se algo estiver ausente.

## Fase 2 - Cluster kind

Criar cluster dev:

```bash
kind create cluster --name gitops-dev --config clusters/dev/kind-config.yaml
```

O script deve ser idempotente:

- se o cluster nao existir, cria;
- se ja existir, reaproveita.

Criterio de saida:

```bash
kubectl get nodes
```

mostra 3 nos `Ready`.

## Fase 3 - Bootstrap do ArgoCD

Instalar ArgoCD uma vez via script.

Depois de instalado, aplicar:

```bash
kubectl apply -f argocd/apps/app-of-apps-dev.yaml
```

A partir deste ponto, o restante deve ser gerenciado pelo ArgoCD.

Criterio de saida:

- namespace `argocd` existe;
- pods do ArgoCD estao `Running`;
- `argocd-server` responde por port-forward ou ingress temporario.

## Fase 4 - App of Apps Dev

Criar as Applications iniciais:

- namespaces;
- ingress-nginx;
- cert-manager;
- sample-app.

No primeiro MVP, deixar monitoring, Headlamp e seguranca avancada para fases seguintes.

Criterio de saida:

```bash
kubectl get applications -n argocd
```

mostra apps `Synced` e `Healthy`.

## Fase 5 - Ingress e TLS Dev

Instalar:

- NGINX Ingress Controller;
- cert-manager;
- ClusterIssuer self-signed;
- Certificates para os hosts locais.

Hosts dev:

```text
argocd.local.dev
headlamp.local.dev
grafana.local.dev
prometheus.local.dev
alertmanager.local.dev
app.local.dev
```

Criar `dns/hosts-snippet.txt` com entradas explicitas.

Criterio de saida:

```bash
curl -k https://argocd.local.dev
curl -k https://app.local.dev
kubectl get certificate -A
```

## Fase 6 - Sample App

Criar uma app simples com:

- endpoint `/`;
- endpoint `/healthz`;
- testes;
- Dockerfile;
- Deployment;
- Service;
- Ingress;
- kustomization base/dev/prod.

Criterio de saida:

```bash
curl -k https://app.local.dev/healthz
```

retorna sucesso.

## Fase 7 - Headlamp

Instalar Headlamp via ArgoCD.

Dev:

- acesso por `https://headlamp.local.dev`;
- login por token de ServiceAccount.

Prod:

- documentar OIDC/SSO como caminho recomendado.

Criterio de saida:

- pagina abre;
- token permite ver namespaces e pods.

## Fase 8 - Observabilidade

Instalar `kube-prometheus-stack`.

Configurar:

- Grafana;
- Prometheus;
- Alertmanager;
- ServiceMonitor do ingress;
- ServiceMonitor do ArgoCD;
- ServiceMonitor da sample-app.

Criar dashboards iniciais:

- cluster overview;
- pods;
- ingress;
- ArgoCD;
- certificados.

Criar alertas iniciais:

- pod em CrashLoopBackOff;
- alto uso de memoria;
- certificado expirando;
- sync failed no ArgoCD;
- erro 5xx no ingress.

Criterio de saida:

- `https://grafana.local.dev` abre;
- dashboards aparecem sem import manual;
- Prometheus tem targets ativos.

## Fase 9 - Smoke Test

Implementar `scripts/smoke-test.sh` validando:

- nodes Ready;
- ArgoCD Applications Synced/Healthy;
- certificates Ready;
- endpoints HTTPS;
- sample-app health;
- Grafana acessivel;
- Prometheus com targets.

Criterio de saida:

```bash
make smoke-test
```

termina com sucesso.

## Fase 10 - Hardening

Adicionar:

- NetworkPolicy default-deny;
- allow DNS egress;
- allow ingress-nginx -> apps;
- allow Prometheus scrape;
- Pod Security labels;
- securityContext nos workloads;
- resources requests/limits.

Criterio de saida:

- pods continuam subindo;
- trafego nao permitido e bloqueado;
- workloads respeitam PSS.

## Fase 11 - Segredos

Implementar Sealed Secrets.

Criar:

- controller;
- exemplo de secret selado;
- documentacao de criacao e rotacao.

Criterio de saida:

- nenhum secret puro no Git;
- secret e criado no cluster pelo controller.

## Fase 12 - CI/CD

Criar `.github/workflows/ci.yaml`.

Pipeline:

- checkout;
- teste;
- build;
- Trivy scan;
- cosign sign keyless;
- push GHCR.

Criar `.github/workflows/cd-promote.yaml`.

Promocao:

- workflow abre PR alterando `images.newTag`;
- ArgoCD sincroniza apos merge.

Criterio de saida:

- imagem publicada no GHCR;
- PR de promocao criado;
- overlay atualizado por PR.

## Fase 13 - Producao

Criar `infra/overlays/prod`.

Prod deve configurar:

- replicas maiores;
- TLS Let's Encrypt;
- ingress com LoadBalancer;
- storage persistente;
- PSS restricted;
- valores de recursos mais realistas;
- external-dns documentado;
- OIDC documentado.

Criterio de saida:

```bash
kubectl kustomize infra/overlays/prod
```

renderiza sem erro.

## Fase 14 - Backup e Runbook

Instalar Velero.

Dev:

- documentar teste com MinIO ou modo simulado.

Prod:

- S3-compatible object storage.

Criar `docs/RUNBOOK.md` com:

- restaurar backup;
- rotacionar secret;
- recuperar ArgoCD;
- diagnosticar certificado;
- diagnosticar app fora de sync;
- diagnosticar pod sem rede.

Criterio de saida:

- restore documentado;
- procedimento testado pelo menos uma vez quando houver backend de storage.

## Resultado Esperado

Ao final:

```bash
make up
make smoke-test
```

devem entregar uma plataforma local funcional, com acesso web para:

- ArgoCD;
- Headlamp;
- Grafana;
- Prometheus;
- Alertmanager;
- sample-app.

E o overlay prod deve estar pronto para adaptacao em um cluster real.
