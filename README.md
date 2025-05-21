
## Установите Minikube (если ещё не установлен)
bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64sudo install minikube-linux-amd64 /usr/local/bin/minikube

## Кластер
bash
minikube start --driver=docker
## Kubernetes работает
bash
kubectl get nodes
## Установка необходимых инструментов
bash
brew install kubectl minikube istioctl
## Запуск Minikube с драйвером Docker и включение Ingress
bash
minikube start --driver=docker
minikube addons enable ingress
## Установка Istio
bash
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATHistioctl install --set profile=default -y

## Разрешения для скрипта развертывания
bash
chmod +x deploy.sh

## Запуск скрипта развертывания
bash
sh deploy.sh
