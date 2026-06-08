# Cluster prod — requisitos mínimos (cloud-agnostic)

Este repositório **não cria** o cluster de produção — isso é responsabilidade da
camada de provisionamento de infraestrutura (ver [`../../terraform/`](../../terraform/),
ou o provisionamento equivalente do seu provedor). O que está aqui é o **contrato**:
o conjunto mínimo de garantias que `infra/overlays/prod/` assume existirem, para
que o overlay permaneça cloud-agnostic e nenhum manifesto dependa de uma API
proprietária de nuvem.

## Requisitos mínimos do cluster alvo

| Requisito | Mínimo | Por quê |
|---|---|---|
| Versão do Kubernetes | ≥ 1.28 | CRDs e APIs usadas por cert-manager, ArgoCD e kube-prometheus-stack nas versões fixadas em `infra/base/*/kustomization.yaml` |
| Nós | ≥ 3, em ≥ 2 zonas de disponibilidade (quando o provedor suportar) | `topologySpreadConstraints` e `PodDisruptionBudget` do overlay prod pressupõem múltiplas zonas/nós |
| `StorageClass` dinâmica | `ReadWriteOnce`, provisionamento dinâmico | Prometheus (`volumeClaimTemplate`), Alertmanager e Velero precisam de PVCs que se auto-provisionam |
| Mecanismo de `LoadBalancer` | nativo da nuvem **ou** [MetalLB](https://metallb.universe.tf/) on-prem | `Service type: LoadBalancer` do NGINX Ingress Controller depende disso — sem ele, o serviço fica `<pending>` |
| Saída de rede (egress) | acesso a `acme-v02.api.letsencrypt.org`, GHCR (`ghcr.io`), e ao repositório Git | `cert-manager` (HTTP01/DNS01), pull de imagens, e sync do ArgoCD |
| Permissão para instalar CRDs | `cluster-admin` (apenas no bootstrap inicial) | cert-manager, ArgoCD e kube-prometheus-stack instalam CRDs — depois do bootstrap, nenhuma aplicação roda com esse privilégio |
| Object storage compatível com S3 | bucket dedicado + credenciais | Backups do Velero (`infra/base/backup/`) |
| Zona DNS administrável | zona real (ex.: `plataforma.suaempresa.com`) + credenciais de API | `external-dns` cria/atualiza registros a partir das anotações dos `Ingress` |

## O que muda em relação ao dev

Veja a tabela completa de diffs em
[`../../docs/ARQUITETURA.md`](../../docs/ARQUITETURA.md#diferenças-dev--produção).
Resumo:

| Item | Dev (`kind`) | Prod |
|---|---|---|
| Domínio | `*.local.dev` (hosts locais) | domínio real, gerido por `external-dns` |
| TLS | `selfsigned-issuer` | `letsencrypt-prod` (HTTP01 por padrão; DNS01 plugável) |
| Ingress | `hostNetwork`, 1 réplica | `LoadBalancer`, ≥ 2 réplicas + PDB + spread |
| Storage | `emptyDir` / StorageClass local pequena | StorageClass dinâmica, ≥ 20Gi, retenção 30d+ |
| ArgoCD | `server.insecure: true`, 1 réplica, Redis standalone | TLS ponta a ponta, ≥ 2 réplicas, Redis HA, SSO/OIDC |
| PSS | `baseline` | `restricted` |
| Alertas | rota local (sem integração externa) | rotas reais (Slack/email/PagerDuty via Secret externo) |

## Como validar o overlay prod sem um cluster real

```bash
kubectl kustomize infra/overlays/prod | kubectl apply --dry-run=client -f -
```

Isso confirma que o overlay **renderiza** e que os manifestos são estruturalmente
válidos — não substitui um teste real, mas permite revisar o "diff dev↔prod" e
detectar problemas de composição do Kustomize antes de existir um cluster prod.

## Adaptação para um provedor específico (documentado, não hard-coded)

A regra de ouro é: **nada em `infra/base/` ou `infra/overlays/prod/` referencia
uma API de nuvem específica**. Quando for necessário usar um recurso proprietário,
documente a adaptação aqui — sem alterar o caminho padrão. Exemplos:

- **AWS**: trocar o `LoadBalancer` padrão por `aws-load-balancer-controller`
  (ALB), usar `external-dns` com provider `aws` (Route53) e
  `ClusterIssuer` com `solver.dns01.route53`. O Terraform de exemplo em
  [`../../terraform/modules/dns`](../../terraform/modules/dns) já documenta
  esse caminho.
- **GCP**: `external-dns` com provider `google` (Cloud DNS), `StorageClass`
  `pd-ssd`, GKE já fornece `LoadBalancer` nativo.
- **Azure**: `external-dns` com provider `azure`, `StorageClass`
  `managed-csi`, AKS já fornece `LoadBalancer` nativo.
- **On-prem / bare-metal**: [MetalLB](https://metallb.universe.tf/) em modo
  L2 ou BGP para `LoadBalancer`, `external-dns` com provider `rfc2136` (BIND)
  ou `cloudflare`, `local-path-provisioner` ou Ceph/Longhorn como `StorageClass`.

Essas escolhas ficam isoladas em `values`/variáveis do overlay e do Terraform —
nunca em manifestos compartilhados pela `base`.
