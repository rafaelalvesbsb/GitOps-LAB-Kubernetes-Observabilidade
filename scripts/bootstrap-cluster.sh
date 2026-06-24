#!/usr/bin/env bash
# Sobe o cluster Kubernetes (kubeadm + kube-vip + Calico) nas 6 VMs do laboratório.
# Rodar de dentro da VM mgmt-01 (lab01) — é ela que tem acesso SSH às outras 5 VMs.
# Detalhes e diagramas: claude/docs/AMBIENTE-E-IMPLEMENTACAO.md
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f inventory.ini ]; then
  echo "ERRO: scripts/inventory.ini não encontrado."
  echo "Copie scripts/inventory.example.ini para scripts/inventory.ini e preencha os acessos reais."
  exit 1
fi

if ! command -v ansible-playbook >/dev/null 2>&1; then
  echo "==> Instalando Ansible e sshpass..."
  sudo apt-get update
  sudo apt-get install -y ansible sshpass
fi

echo "==> Testando conectividade SSH com todas as VMs do inventário..."
ansible all -m ping

echo "==> Executando playbook de bootstrap do cluster..."
ansible-playbook playbooks/site.yml "$@"

echo
echo "==> Bootstrap concluído. Validar com:"
echo "    kubectl get nodes -o wide"
echo "    kubectl get pods -A"
