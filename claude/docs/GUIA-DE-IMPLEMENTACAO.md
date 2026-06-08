# Guia de Implementação — Plataforma GitOps Kubernetes (Dev + Produção)

> Passo a passo prático: o que será feito, em que ordem, com quais comandos, e como validar
> cada etapa antes de seguir para a próxima. Este guia assume o repositório descrito em
> [`../PROMPT.md`](../PROMPT.md) e as decisões explicadas em [`ARQUITETURA.md`](./ARQUITETURA.md).

---

## 0. Diagnóstico do ambiente atual (já levantado)

Antes de qualquer coisa, este é o estado real do host onde vamos rodar o ambiente `dev`:

| Item | Situação encontrada | Implicação |
|---|---|---|
| OS | Windows Server 2025 + WSL2 (Ubuntu-24.04, *running*) | O cluster `kind` precisa rodar **dentro do WSL2** (kernel Linux + Docker), não no Windows |
| Docker | ✅ já instalado e funcionando dentro do `Ubuntu-24.04` (v29.5.3, usuário `server` no grupo `docker`) | Não precisa instalar — *(atualiza a nota "pendente: instalar Docker" do setup, que está desatualizada)* |
| kubectl / helm / kind / kustomize / cosign / trivy | ❌ nenhum instalado | Precisamos instalar — passo 1 abaixo |
| Portas 80 / 443 / 6443 | ✅ livres | `kind` pode mapear sem conflito |
| RAM / Disco | 98 GB RAM (93 GB livres) / ~933 GB livres em `/` | Sobra de sobra para um cluster `kind` de 3 nós + toda a stack |
| `sudo` | pede senha (não é passwordless) | Os scripts de instalação que exigem `sudo` vão pedir senha interativamente — não dá para automatizar 100% sem o usuário digitar a senha uma vez |
| Containers já rodando no WSL2 | Ollama, Open WebUI, Postgres, Portainer, **Prometheus (9090)**, **Grafana (3000)**, node-exporter, cadvisor, nginx (8080) | ⚠️ **atenção**: o `kube-prometheus-stack` vai instalar *seu próprio* Prometheus/Grafana dentro do cluster — eles não competem por porta com os containers Docker existentes (acesso será via Ingress/`*.local.dev`, não via `localhost:3000`/`:9090`), mas é bom ter isso em mente ao depurar "por que a Grafana que abri não é a do cluster" |

> 💡 Nota: a memória do projeto registra "Pendente: Instalar Docker Engine no Ubuntu 24.04
> (WSL2)" — isso **já foi resolvido** (Docker 29.5.3 rodando). Vamos atualizar essa anotação.

---

## 1. Fase 0 — Ferramentas de linha de comando (dentro do WSL2 `Ubuntu-24.04`)

Tudo a partir daqui roda **dentro do WSL2** (`wsl -d Ubuntu-24.04`), porque é onde o Docker
e o kernel Linux estão.

Instalar (versões mínimas indicadas no `PROMPT.md`):

```bash
# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind

# kustomize (opcional — kubectl já embute "kubectl kustomize")
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash

# cosign + trivy
go install github.com/sigstore/cosign/v2/cmd/cosign@latest   # ou binário pré-compilado do GitHub Releases
sudo apt-get install -y trivy  # ou script oficial aquatone/trivy
```

**Critério de saída desta fase:** `scripts/check-prerequisites.sh` (criado na Fase 1) roda
sem erros e imprime as versões de todas as ferramentas.

---

## 2. Fase 1 — Esqueleto do repositório

Criar a estrutura de diretórios completa descrita no `PROMPT.md` (vazia/com placeholders),
e os primeiros scripts utilitários:

1. `scripts/check-prerequisites.sh` — valida `docker`, `kubectl`, `helm`, `kind`, `jq`,
   `cosign`, `trivy`; falha com mensagem clara apontando o que falta.
2. `clusters/dev/kind-config.yaml` — cluster de 3 nós (1 control-plane + 2 workers),
   `extraPortMappings` 80→80 e 443→443.
3. `Makefile` com os targets `up`, `down`, `status`, `logs`, `port-forward`, `smoke-test`
   (inicialmente "esqueleto", preenchidos conforme as fases avançam).

**Critério de saída:** `make status` roda (mesmo que ainda reporte "cluster não existe")
sem erro de sintaxe; estrutura de diretórios espelha o `PROMPT.md`.

---

## 3. Fase 2 — Subir o cluster `kind` (dev)

```bash
kind create cluster --config clusters/dev/kind-config.yaml --name devcluster
kubectl cluster-info --context kind-devcluster
kubectl get nodes -o wide        # esperar 3 nós em Ready
```

**Critério de saída:** `kubectl get nodes` mostra 3 nós `Ready`; `kind get clusters` lista
`devcluster`.

> Idempotência: o `bootstrap-dev.sh` deve checar `kind get clusters | grep devcluster`
> antes de tentar criar — se já existe, pula esta etapa.

---

## 4. Fase 3 — Bootstrap do ArgoCD ("ovo e galinha")

ArgoCD precisa existir no cluster *antes* de poder gerenciar o resto via GitOps — por isso
ele é instalado uma vez, manualmente/via script, e a partir daí **assume o controle de tudo**.

```bash
kubectl create namespace argocd
helm upgrade --install argocd argo-cd \
  --repo https://argoproj.github.io/argo-helm \
  --namespace argocd \
  -f infra/base/argocd/values.yaml \
  -f infra/overlays/dev/argocd/values-patch.yaml

kubectl -n argocd wait --for=condition=available --timeout=300s deployment/argocd-server
```

**Critério de saída:** `kubectl -n argocd get pods` mostra todos os pods `Running`;
`argocd-server` acessível via `port-forward` antes mesmo do Ingress existir:

```bash
kubectl -n argocd port-forward svc/argocd-server 8081:443
# abrir https://localhost:8081 — login admin / senha do secret argocd-initial-admin-secret
```

---

## 5. Fase 4 — Aplicar o "App of Apps" (a partir daqui, é tudo GitOps)

```bash
kubectl apply -f argocd/apps/app-of-apps-dev.yaml
```

A partir deste ponto, **nenhum outro `kubectl apply`/`helm install` deve ser feito manualmente**
— o ArgoCD reconcilia tudo a partir do Git: namespaces, RBAC, NetworkPolicies, NGINX Ingress,
cert-manager, kube-prometheus-stack, Headlamp, CoreDNS patch, Sealed Secrets, Velero, sample-app.

**Critério de saída:** `argocd app list` (ou `kubectl get applications -n argocd`) mostra
todas as `Application`s com `SYNC STATUS = Synced` e `HEALTH STATUS = Healthy`. Isso pode
levar alguns minutos na primeira sincronização (pull de imagens, CRDs do cert-manager etc.).

> Se alguma `Application` ficar `Degraded`/`OutOfSync` por muito tempo, **não** corrija com
> `kubectl edit` direto no cluster — corrija o manifesto no Git e deixe o ArgoCD ressincronizar.
> Isso é o próprio propósito do `selfHeal`: o cluster sempre volta a refletir o Git.

---

## 6. Fase 5 — DNS local e validação de acesso HTTPS

1. Aplicar o snippet de `/etc/hosts` (dentro do WSL2 e/ou no Windows, conforme onde o
   navegador roda) apontando `*.local.dev` para `127.0.0.1`.
2. Confirmar que o patch do CoreDNS foi aplicado (`kubectl -n kube-system get cm coredns -o yaml`).
3. Acessar cada serviço via HTTPS e confirmar que o certificado (self-signed) foi emitido:

```bash
curl -kv https://argocd.local.dev      # esperar handshake TLS OK + redirect/login
curl -kv https://grafana.local.dev
kubectl get certificate -A             # READY=True em todos
```

**Critério de saída:** todos os hosts em `*.local.dev` respondem via HTTPS com certificado
emitido pelo `selfsigned-issuer`, sem erro de conexão recusada.

---

## 7. Fase 6 — Observabilidade: validar dashboards e alertas como código

1. Confirmar que os `ConfigMap`s/`PrometheusRule`s de `observability/` foram sincronizados
   pelo ArgoCD (não criados manualmente na UI).
2. Acessar `https://grafana.local.dev`, confirmar que os dashboards de
   `observability/dashboards/*.json` aparecem na pasta "Kubernetes" sem import manual.
3. Validar que os alertas existem no Prometheus/Alertmanager:

```bash
kubectl -n monitoring get prometheusrules
# Abrir https://prometheus.local.dev/alerts e conferir PodCrashLooping, HighMemoryUsage etc.
```

**Critério de saída:** dashboards e alertas aparecem **sem nenhuma ação manual na UI** —
tudo veio do Git via ArgoCD. Esse é o teste decisivo de "observabilidade como código".

---

## 8. Fase 7 — Sample app e fluxo de CI completo

1. Implementar o `sample-app` (API simples) com `Dockerfile`, testes, manifests `base`/`overlays`.
2. Configurar os *secrets* do GitHub Actions (`GITHUB_TOKEN` já existe; adicionar
   `COSIGN_PRIVATE_KEY`/OIDC keyless, e o token de PR automatizado).
3. Disparar o pipeline (`git push` em `sample-app/**`):
   - build → test → scan Trivy → assina com cosign → push GHCR → abre PR atualizando
     `sample-app/k8s/overlays/dev/kustomization.yaml` (`images.newTag`).
4. Mergear o PR → ArgoCD detecta e sincroniza → novo pod sobe em `https://app.local.dev`.

**Critério de saída:** alterar uma linha no `sample-app`, dar `git push`, e ver — sem
nenhum passo manual no cluster — a nova versão rodando em `app.local.dev` em poucos minutos,
com o histórico completo (commit → PR → sync) auditável no GitHub e no ArgoCD.

---

## 9. Fase 8 — Hardening de segurança

1. Aplicar `NetworkPolicy` default-deny + exceções; validar com testes negativos
   (`kubectl run` um pod de teste e confirmar que o tráfego não permitido é bloqueado).
2. Confirmar labels de Pod Security Standard (`baseline` em dev) e que pods que violam
   o padrão são rejeitados (testar deliberadamente com um manifesto "ruim").
3. Migrar qualquer segredo em texto puro para Sealed Secrets/External Secrets — `git grep`
   por padrões de segredo deve retornar zero resultados fora de `*.sealed.yaml`/referências
   ao operador externo.
4. Rodar `trivy` localmente contra as imagens usadas e revisar achados.

**Critério de saída:** `git grep -i -E "(password|secret|token|api[_-]?key)\s*[:=]\s*['\"][^'\"$]"`
não encontra segredo em texto puro em nenhum manifesto versionado.

---

## 10. Fase 9 — Backup/Restore (Velero) e Runbook

1. Configurar Velero apontando para um *object storage* compatível com S3 (MinIO local serve
   para o teste em dev).
2. **Executar de fato** um backup e um restore de teste (ex.: apagar o namespace `apps` e
   restaurá-lo a partir do backup) — documentar o procedimento exato em `docs/RUNBOOK.md`.

**Critério de saída:** restore testado manualmente ao menos uma vez, com passos exatos
documentados — "documentado mas nunca testado" não conta como pronto.

---

## 11. Fase 10 — `smoke-test.sh` e `make up` ponta a ponta

Consolidar tudo em `scripts/smoke-test.sh`, que valida (e pode rodar em CI também):

- todos os nós `Ready`;
- todas as `Application`s do ArgoCD `Synced`/`Healthy`;
- todos os `Certificate`s `Ready=True`;
- endpoints HTTPS respondendo (`argocd`, `grafana`, `prometheus`, `dashboard`, `app`);
- dashboards/alertas presentes no Grafana/Prometheus.

Depois, validar que **o processo inteiro é idempotente e reproduzível do zero**:

```bash
make down       # destrói o cluster dev
make up         # recria do zero — deve funcionar sem intervenção manual
make smoke-test # valida tudo automaticamente
```

**Critério de saída:** `make down && make up && make smoke-test` roda do zero, sem
intervenção manual além de digitar a senha do `sudo` quando solicitado, e termina com
"tudo verde".

---

## 12. Fase 11 — Overlay de produção e fluxo de promoção

Esta fase **não exige um cluster de produção real** para ser validada — o objetivo é que
o overlay `prod` seja **renderizável e coerente**:

```bash
kubectl kustomize infra/overlays/prod | kubectl apply --dry-run=client -f -
```

1. Revisar o *diff* `kubectl kustomize overlays/dev` vs `overlays/prod` — deve ser pequeno,
   legível, e bater exatamente com a tabela da seção 6 de `ARQUITETURA.md`.
2. Escrever `clusters/prod/README.md` com os requisitos mínimos do cluster alvo.
3. Implementar e testar o workflow `cd-promote.yaml` (abre PR de promoção dev → prod) —
   pode ser testado contra o próprio cluster dev simulando "prod" num segundo namespace,
   se não houver cluster de produção disponível.

**Critério de saída:** `kubectl kustomize infra/overlays/prod` renderiza sem erro, o diff
para `dev` é exatamente o esperado, e o fluxo de PR de promoção foi testado ao menos uma vez
de ponta a ponta (mesmo que o destino final seja simulado).

---

## 13. Ordem recomendada de execução (resumo)

```
Fase 0  → instalar ferramentas (kubectl, helm, kind, kustomize, cosign, trivy)
Fase 1  → criar esqueleto de diretórios + scripts utilitários
Fase 2  → subir cluster kind
Fase 3  → bootstrap manual do ArgoCD (chicken-and-egg)
Fase 4  → aplicar App of Apps — ArgoCD assume o controle
Fase 5  → validar DNS local + HTTPS/TLS
Fase 6  → validar observabilidade como código (dashboards/alertas)
Fase 7  → sample-app + pipeline CI completo (build→test→scan→sign→push→PR→sync)
Fase 8  → hardening (NetworkPolicy, PSS, secrets geridos)
Fase 9  → backup/restore (Velero) testado e documentado
Fase 10 → smoke-test + make down/up idempotente
Fase 11 → overlay de produção renderizável + fluxo de promoção testado
```

Cada fase tem um **critério de saída objetivo** — não avance para a próxima sem cumpri-lo.
Isso evita o cenário clássico de "infra que só funciona na primeira vez que alguém rodou".

---

## 14. Quando algo der errado — primeiros passos de troubleshooting

| Sintoma | Onde olhar primeiro |
|---|---|
| `kind create cluster` falha | `docker info` dentro do WSL2 — daemon rodando? Conflito de porta 80/443/6443? |
| `Application` em `OutOfSync`/`Degraded` | `argocd app diff <nome>` e `kubectl describe application <nome> -n argocd` — **nunca** corrigir com `kubectl edit` direto |
| Certificado não fica `Ready` | `kubectl describe certificate <nome>` e `kubectl logs -n cert-manager deploy/cert-manager` — geralmente é DNS/HTTP01 challenge não alcançável |
| `*.local.dev` não resolve | conferir `/etc/hosts` (WSL2 *e* Windows, dependendo de onde o navegador roda) e o patch do CoreDNS |
| Pod não sobe por Pod Security / NetworkPolicy | `kubectl get events -n <ns> --sort-by=.lastTimestamp` — geralmente a mensagem de violação é explícita |
| CI falha no scan Trivy | revisar achados — não silenciar com `--exit-code 0`; corrigir a base image ou adicionar exceção justificada e versionada |

---

## 15. Próximos passos após este guia

Quando o usuário disser **"pode começar"**, a implementação seguirá exatamente esta ordem,
fase por fase, com checkpoint de validação ao final de cada uma antes de prosseguir —
nada de gerar 40 arquivos de uma vez sem testar incrementalmente.
