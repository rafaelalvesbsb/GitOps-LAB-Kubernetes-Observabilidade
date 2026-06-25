# HANDOFF — GitOps LAB Kubernetes & Observabilidade

> Documento de continuidade. Objetivo: qualquer IA ou desenvolvedor que abra este repositório deve conseguir entender o estado do projeto e continuar o trabalho sem precisar re-perguntar o que já foi decidido.
>
> Última atualização: 2026-06-25 (App of Apps completo — **9/9 Applications Synced/Healthy**, todos os 4 endpoints HTTPS validados)

---

## 1. Objetivo do Projeto

Construir, dentro deste repositório, uma **plataforma GitOps de referência** que funcione em um **laboratório local (dev)** e possa ser promovida — com mudanças mínimas e auditáveis — para um **cluster de produção cloud-agnostic**.

Não é um script descartável. É um repositório GitOps real: declarativo, versionado, idempotente, com:
- Separação `base/` (comum a qualquer ambiente) + `overlays/<env>/` (específico por ambiente).
- Orquestração via **ArgoCD** (App of Apps / ApplicationSets).
- CI/CD via **GitHub Actions** (build → test → scan → sign → push → PR de promoção).
- **Observabilidade como produto** (dashboards e alertas versionados como código).
- **Segurança desde o dia 1** (NetworkPolicy default-deny, Pod Security Standards, secrets nunca em texto puro, RBAC mínimo).

Fonte da especificação completa: [claude/PROMPT.md](claude/PROMPT.md), [claude/docs/ARQUITETURA.md](claude/docs/ARQUITETURA.md), [claude/docs/GUIA-DE-IMPLEMENTACAO.md](claude/docs/GUIA-DE-IMPLEMENTACAO.md).

> Nota: existe uma pasta `codex/` com cópia espelhada dos mesmos documentos — não é relevante para o trabalho real, ignorar.

---

## 2. Stack Utilizada

| Componente | Função | Observação |
|---|---|---|
| Kubernetes (dev) | Cluster real via **kubeadm vanilla** em VMs Hyper-V | 1 control-plane + 2 workers (substituiu o `kind`, ver seção 7) |
| Kubernetes (prod) | Cloud-agnostic, ≥1.28 | EKS/GKE/AKS/k3s/bare-metal — ver `clusters/prod/README.md` |
| containerd | Runtime de containers | usado pelo kubeadm (em vez de Docker dentro do cluster) |
| Calico | CNI | recomendado para suportar NetworkPolicy enforcement (requisito de hardening) |
| NGINX Ingress | Entrada HTTP/HTTPS | Chart oficial Helm |
| cert-manager | TLS/Certificados | self-signed (dev) / Let's Encrypt (prod) |
| ArgoCD | Motor GitOps | App of Apps + ApplicationSets |
| GitHub Actions | CI/CD | build, test, scan, sign, push, promote |
| kube-prometheus-stack | Observabilidade | Prometheus + Grafana + Alertmanager |
| Headlamp | Dashboard web do cluster | — |
| CoreDNS custom (dev) / external-dns (prod) | DNS | zona `*.local.dev` em dev |
| Sealed Secrets / External Secrets Operator | Gestão de segredos | zero plain text no Git |
| Velero | Backup/DR | obrigatório em prod |
| NetworkPolicy + Pod Security Standards | Segurança de rede e pods | baseline (dev) / restricted (prod) |
| GHCR + Trivy + cosign | Registry, scan de vulnerabilidades, assinatura de imagens | CI falha em CRITICAL/HIGH não whitelisted |

---

## 3. Estrutura Atual do Projeto

```
GitOps-LAB-Kubernetes-Observabilidade/
├── .claude/settings.json            # permissões/config do Claude Code
├── .gitattributes
├── claude/
│   ├── PROMPT.md                    # especificação técnica completa
│   └── docs/
│       ├── ARQUITETURA.md           # decisões de arquitetura, diagramas, tabela dev↔prod
│       ├── GUIA-DE-IMPLEMENTACAO.md # 12 fases de implementação com critério de saída
│       └── pdf/                     # geração de PDF consolidado (build_html.py + README)
├── clusters/
│   ├── dev/
│   │   ├── kind-config.yaml         # cluster kind: 1 control-plane + 2 workers, portas 80/443
│   │   └── README.md
│   └── prod/
│       └── README.md                # requisitos mínimos cloud-agnostic
├── codex/                           # cópia espelhada — ignorar
└── handoff.md                       # este arquivo
```

**Já existe e está implantado no cluster** (não apenas especificado): `infra/base/{namespaces,ingress-nginx,cert-manager,monitoring,headlamp,network-policies,storage,argocd}/`, `infra/overlays/dev/{namespaces,ingress-nginx,cert-manager,monitoring,headlamp,network-policies,storage,argocd,argocd-ingress}/`, `argocd/apps/{app-of-apps-dev.yaml,dev/*.yaml}`, `scripts/` (Ansible).

**Ainda não existe**: `observability/` (dashboards/alertas extras versionados além do que o chart já traz), `dns/`, `github-actions/.github/workflows/`, `sample-app/`, `Makefile`, `docs/RUNBOOK.md`, `infra/{base,overlays}/prod/`.

---

## 4. Funcionalidades Já Feitas

- ✅ Especificação técnica completa e revisada (PROMPT.md, ARQUITETURA.md, GUIA-DE-IMPLEMENTACAO.md).
- ✅ Cluster `kubeadm` HA real no ar (6 VMs Hyper-V): 3 control-plane + 2 workers `Ready`, VIP via kube-vip, Calico, `mgmt-01` com kubectl/helm/kustomize/argocd-cli.
- ✅ ArgoCD instalado (Helm manual, ver seção 7) e **App of Apps completo aplicado**: `argocd/apps/app-of-apps-dev.yaml` → 8 Applications filhas, **todas `Synced/Healthy`**:
  `namespaces-dev`, `storage-dev`, `network-policies-dev`, `cert-manager-dev`, `ingress-nginx-dev`, `monitoring-dev`, `headlamp-dev`, `argocd-ingress-dev`.
- ✅ 4 endpoints HTTPS validados de ponta a ponta (`curl` com `--resolve`, certificado self-signed do cert-manager, todos via Ingress real): `argocd.local.dev` (200), `dashboard.local.dev` (200), `grafana.local.dev` (302 — redirect normal de login), `prometheus.local.dev` (302).
- ✅ `local-path-provisioner` como StorageClass default (bare-metal não vem com nenhuma).
- ✅ NetworkPolicy default-deny + 3 exceções no namespace `apps` (ainda sem nenhuma app real rodando lá — Fase 7/sample-app pendente).
- ✅ Geração de PDF consolidado da documentação (`claude/docs/pdf/`).

## 5. Funcionalidades Pendentes

- [x] Fase 0/1/2 (substituídas) — cluster kubeadm HA via Ansible.
- [x] Fase 3 — ArgoCD bootstrap manual.
- [x] Fase 4 — App of Apps aplicado, 9/9 Applications Synced/Healthy.
- [x] Fase 5 — DNS local + HTTPS/TLS validados (via `curl --resolve`; `/etc/hosts` real do operador ainda não configurado — ver seção 7).
- [~] Fase 6 — observabilidade: kube-prometheus-stack rodando com seus dashboards/alertas **padrão do chart**; ainda faltam dashboards/`PrometheusRule` customizados versionados em `observability/` (PodCrashLooping, CertificateExpiringSoon, ArgoCDSyncFailed específicos do PROMPT.md).
- [ ] Fase 7 — sample-app + pipeline CI completo (GitHub Actions, GHCR, Trivy, cosign) — nada disso existe ainda.
- [ ] Fase 8 — hardening adicional: Sealed Secrets/External Secrets Operator (zero secrets hoje, mas também zero segredo de app para gerenciar ainda), validação formal de NetworkPolicy com pod de teste.
- [ ] Fase 9 — backup/restore com Velero testado.
- [ ] Fase 10 — `smoke-test.sh` + `Makefile` (`make up/down/status`) — não existe Makefile ainda.
- [ ] Fase 11 — overlay prod + fluxo de promoção dev→prod via PR.

---

## 6. Decisões Técnicas Importantes

1. **Kustomize `base/` + `overlays/<env>/`** em vez de Helm puro ou repositórios separados por ambiente — elimina duplicação, integra nativamente com ArgoCD, e ainda permite consumir Helm charts da comunidade via `helmCharts:` do Kustomize.
2. **Cloud-agnostic em produção** — nenhuma decisão hard-coda um provider específico (ex.: ALB da AWS). Cada escolha (Ingress+NGINX, LoadBalancer/MetalLB, external-dns plugável, cert-manager com HTTP01 padrão) vem com nota de "como adaptar" para AWS/GCP/Azure/on-prem.
3. **Segurança desde o dia 1**: Pod Security `restricted` em prod, NetworkPolicy default-deny + exceções em ambos os ambientes, secrets nunca em texto puro (Sealed Secrets/External Secrets), RBAC mínimo, scan (Trivy) + assinatura (cosign) no CI.
4. **Nada aplica direto no cluster** — CI só constrói/testa/escaneia/abre PR. Quem aplica é o ArgoCD reconciliando o que está em `main`. Toda mudança tem commit + PR por trás (auditoria).
5. **Promoção dev→prod via PR**, nunca via `sed`/script direto no cluster prod.
6. **Control-plane do dev também em HA (3 nós)** — decisão de 2026-06-24, foge um pouco do princípio "dev minimalista" original do PROMPT.md, mas o usuário optou por replicar HA desde o laboratório. Vale revisar/alinhar a tabela dev↔prod do `ARQUITETURA.md` (que hoje descreve réplicas mínimas em dev) à luz dessa escolha.

---

## 7. Problemas Conhecidos / Mudança de Ambiente em Andamento

⚠️ **Decisão 1 (2026-06-24):** o projeto **não usa WSL2** como ambiente de execução — em vez disso, **6 VMs Ubuntu Server no Hyper-V** (já provisionadas pelo usuário): 1 bastion/gerenciamento + 3 control-plane (HA) + 2 workers.

⚠️ **Decisão 2 (2026-06-24):** o cluster **não usa `kind`** — é um cluster real provisionado com **kubeadm vanilla**.

⚠️ **Decisão 3 (2026-06-24):** control-plane em **HA com 3 nós** (quórum de etcd), com IP virtual via **kube-vip** (sem VM extra de load balancer).

### Inventário real das VMs (preenchido em 2026-06-24)

| Papel | Hostname | IP | Usuário |
| --- | --- | --- | --- |
| `mgmt-01` (bastion) | `lab01` | `192.168.1.105` | `lab01` |
| `k8s-cp-01` | `lab02` | `192.168.1.101` | `lab02` |
| `k8s-cp-02` | `lab03` | `192.168.1.106` | `lab03` |
| `k8s-cp-03` | `lab04` | `192.168.1.107` | `lab04` |
| `k8s-worker-01` | `lab05` | `192.168.1.108` | `lab05` |
| `k8s-worker-02` | `lab06` | `192.168.1.109` | `lab06` |

VIP da API (kube-vip): `192.168.1.110:6443` — **confirmar que está livre e fora do range do DHCP** antes de rodar o bootstrap. Credenciais reais (senha) ficam em `scripts/inventory.ini`, que é **gitignored** — nunca commitar.

### O que já foi criado (este repositório)

- [`claude/docs/AMBIENTE-E-IMPLEMENTACAO.md`](claude/docs/AMBIENTE-E-IMPLEMENTACAO.md) — doc completa com diagramas Mermaid (rede, componentes, sequência de bootstrap), inventário e instruções de execução.
- `scripts/inventory.ini` (real, gitignored) + `scripts/inventory.example.ini` (template versionado) — inventário Ansible com as 6 VMs.
- `scripts/ansible.cfg` + `scripts/playbooks/site.yml` + roles (`common`, `kube-vip`, `control-plane-init`, `control-plane-join`, `worker-join`, `cni-calico`, `mgmt-tools`) — automação completa do bootstrap kubeadm + kube-vip + Calico.
- `scripts/bootstrap-cluster.sh` — script único de entrada (`./scripts/bootstrap-cluster.sh`), idempotente.
- Banner de aviso adicionado no topo de `claude/docs/GUIA-DE-IMPLEMENTACAO.md` apontando Fases 0-2 como obsoletas e linkando para o novo fluxo.
- `clusters/dev/kind-config.yaml` **ainda existe mas está obsoleto** — não foi removido (decisão de não apagar histórico/arquivo sem necessidade), mas não é mais usado em lugar nenhum do fluxo atual.

### Bugs reais encontrados e corrigidos durante a execução (2026-06-24)

Importante para quem for reexecutar/depurar `scripts/playbooks/`:

1. **O `sudo` destas VMs não é compatível com o `become` do Ansible.** Ele aceita o flag `-p` de prompt customizado, mas sempre reformata como `[sudo: <prompt>] Password:` em vez de usar o texto literal — o detector de prompt do Ansible nunca reconhece isso e trava em "Timeout waiting for privilege escalation prompt". **Solução adotada:** nenhuma role usa `become:`; toda escalação de privilégio é manual via `shell: "sudo -S <comando>"` com a senha passada por `args.stdin`. Ver `roles/common/tasks/main.yml` para o padrão.
2. **`kube_version=1.30` no INI virou float `1.3`** (o parser INI do Ansible converte valores que parecem número). Corrigido colocando aspas: `kube_version="1.30"`. Se adicionar novas vars numéricas-como-string no inventário, sempre colocar aspas.
3. **`kube-vip` em `CrashLoopBackOff` nos control-planes que entraram via `kubeadm join`** (lab03/lab04): o kubeadm (≥1.29) só gera `/etc/kubernetes/super-admin.conf` (acesso `system:masters`) no nó do `kubeadm init` — nos joins, esse arquivo nunca é criado, e o `hostPath` do kube-vip criava um arquivo vazio (semântica `FileOrCreate`). **Solução:** o manifesto do kube-vip usa `/etc/kubernetes/admin.conf` (presente em todos os nós) e a role `control-plane-init` cria um `ClusterRoleBinding` extra (`kube-vip-admin-fix`, `cluster-admin` → user `kubernetes-admin`) porque o `admin.conf` do kubeadm moderno só vem com o grupo `kubeadm:cluster-admins`, que por si só não foi suficiente para o kube-vip gerenciar `Lease` objects.
4. **403 transitório do CDN do `pkgs.k8s.io`** ao baixar a chave do repositório simultaneamente nos 5 nós (rate limit por estarem atrás do mesmo IP do Hyper-V). Corrigido com `curl --retry 5 --retry-delay 3 --retry-all-errors`.

### Bugs reais do ArgoCD/GitOps encontrados e corrigidos (2026-06-25, Fase 4)

Importante para quem for adicionar novos componentes Helm via ArgoCD neste cluster:

5. **`helm template` (usado pelo `helmCharts:` do Kustomize) ignora a pasta `crds/` dos charts** — limitação conhecida do Helm, não um bug do projeto. Charts que dependem disso (kube-prometheus-stack) nunca teriam suas CRDs criadas via Kustomize+helmCharts. **Solução:** `monitoring-dev` usa fonte **Helm nativa multi-source do ArgoCD** (`argocd/apps/dev/monitoring.yaml`: chart + valueFiles do nosso Git + um terceiro source Kustomize só para o Ingress) em vez de Kustomize. `cert-manager` não precisou disso porque seu chart tem um flag `crds.enabled` que contorna o problema.
6. **Webhooks de admissão (ingress-nginx e kube-prometheus-stack) dependem de Jobs com `helm.sh/hook` para gerar/aplicar certificado TLS.** O ArgoCD interpreta parcialmente esses hooks mas não reproduz o ciclo de vida real do Helm — o Job de "patch" do CA nunca roda corretamente, deixando o webhook com certificado não confiável (`x509: certificate signed by unknown authority`), o que trava a criação de **qualquer** recurso no cluster (não só do próprio chart) enquanto o webhook existir. **Solução:** `controller.admissionWebhooks.enabled: false` (ingress-nginx) e `prometheusOperator.admissionWebhooks.enabled: false` (kube-prometheus-stack). Não é crítico para um lab.
7. **Pod Security `baseline` bloqueia `hostNetwork`/`hostPort`/`hostPID`/`hostPath`** — necessários para o `ingress-nginx-controller` (sem MetalLB, expõe 80/443 direto no host) e para o `prometheus-node-exporter` (lê métricas de kernel do host). **Solução:** os namespaces `ingress-nginx` e `monitoring` usam PSS `privileged` (exceção deliberada e documentada em `infra/base/namespaces/namespaces.yaml`); os demais namespaces continuam `baseline`.
8. **`Service type: LoadBalancer` do ingress-nginx nunca sai de `EXTERNAL-IP <pending>`** sem MetalLB/LB de nuvem, e o ArgoCD espera por isso indefinidamente, travando a Application em "Progressing" para sempre. **Solução:** patch para `type: ClusterIP` no overlay dev (tráfego chega via hostNetwork, a Service não precisa expor nada externamente).
9. **Rollout do `Deployment` do ingress-nginx travava com 1 pod `Pending` eterno**: a estratégia padrão (`maxSurge: 25%`) tenta criar um 3º pod durante qualquer rolling update, mas com `hostPort` e só 2 nós `ingress-ready`, esse 3º pod nunca tem onde rodar. **Solução:** `maxSurge: 0, maxUnavailable: 1` no patch do Deployment.
10. **CRDs do prometheus-operator são tão grandes que o `kubectl apply` client-side (padrão) excede o limite de 262144 bytes da annotation `last-applied-configuration`** em re-aplicações. **Solução:** `ServerSideApply=true` no `syncOptions` da Application — mas se o CRD já foi criado uma vez via client-side antes dessa flag existir, é preciso remover manualmente a annotation antiga (`kubectl annotate crd <nome> kubectl.kubernetes.io/last-applied-configuration-`) uma única vez para desbloquear.
11. **CRDs (ServiceMonitor/PrometheusRule) usadas por OUTRA Application (ingress-nginx) antes de existirem** — `SkipDryRunOnMissingResource=true` no `syncOptions` evita que o sync falhe permanentemente enquanto a CRD não existe; o `selfHeal` corrige automaticamente assim que a CRD aparece.
12. **Nomes de Service errados no Ingress do Grafana/Prometheus** — copiados de um plano anterior (`kube-prometheus-stack-*`) que usava `releaseName` fixo via Kustomize; ao migrar para fonte Helm nativa do ArgoCD, o release passou a se chamar `monitoring-dev` (nome da Application), então os Services reais são `monitoring-dev-grafana` e `monitoring-dev-kube-promet-prometheus`. Sempre confirmar `kubectl get svc -n <ns>` antes de escrever o Ingress.
13. **Truque operacional:** depois de editar `argocd/apps/dev/*.yaml`, é preciso `kubectl patch application app-of-apps-dev -n argocd --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'` para o spec da Application filha atualizar — e depois um sync explícito (`{"operation":{"sync":{"revision":"HEAD","prune":true}}}'`) se a automação não pegar sozinha rápido o suficiente.

### Pendente

- Trocar as senhas padrão das VMs por algo seguro / migrar para chave SSH (o acesso por chave já existe para um usuário de automação: `~/.ssh/lab_gitops_key.pub` foi autorizado em `~/.ssh/authorized_keys` de todos os 6 nós).
- Configurar `/etc/hosts` real (ou DNS) na máquina do operador — hoje a validação foi feita com `curl --resolve`, ver `dns/hosts-snippet.txt`.
- Deletar o secret `argocd-initial-admin-secret` depois de guardar a senha em outro lugar seguro (recomendação oficial do ArgoCD).

---

## 8. Próximos Passos Recomendados

O cluster já está no ar e validado — os passos abaixo são os que faltam:

1. Trocar as senhas padrão das 6 VMs (ou migrar definitivamente para chave SSH) — ver aviso de segurança em `claude/docs/AMBIENTE-E-IMPLEMENTACAO.md`, seção 7.
2. Criar o esqueleto de diretórios GitOps (`infra/`, `argocd/`, `observability/`, `dns/`, `Makefile`) conforme a árvore especificada em `claude/PROMPT.md`.
3. Seguir as Fases 3 a 11 de `GUIA-DE-IMPLEMENTACAO.md` em ordem (bootstrap do ArgoCD em diante), validando o critério de saída de cada fase antes de avançar.

---

## 9. Instruções para Continuar o Desenvolvimento

- **Onde está a verdade sobre "o que construir"**: `claude/PROMPT.md` (requisitos), `claude/docs/ARQUITETURA.md` (por quê), `claude/docs/GUIA-DE-IMPLEMENTACAO.md` (como, passo a passo com critério de saída).
- **Não duplicar manifests** entre dev e prod — tudo que é comum vai em `base/`; o que muda por ambiente vai em `overlays/<env>/`.
- **Não aplicar nada manualmente no cluster** fora do fluxo GitOps (CI abre PR → ArgoCD sincroniza). Excecão: comandos de bootstrap inicial do ArgoCD (chicken-and-egg, Fase 3 do guia), que são manuais por natureza.
- **Ambiente de execução mudou**: ignorar qualquer instrução dos docs originais que assuma WSL2/`kind`; o ambiente real é 6 VMs Ubuntu Server no Hyper-V provisionadas via `kubeadm` (ver seção 7 e `claude/docs/AMBIENTE-E-IMPLEMENTACAO.md`).
- **Automação de bootstrap já existe** em `scripts/` (Ansible) — não escrever um novo mecanismo do zero; estender os roles existentes se precisar mudar algo no provisionamento dos nós.
- **Ignorar a pasta `codex/`** — é uma cópia espelhada da documentação e não deve ser editada nem usada como referência.
- Ao concluir cada fase do guia, marque o item correspondente na seção 5 deste handoff e atualize a seção 7 caso surjam novos problemas/decisões.
