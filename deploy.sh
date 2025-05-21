#!/usr/bin/env bash

export DOCKER_SOCKET=unix:///var/run/docker.sock

echo "Инициализация Service Mesh..." &&
istioctl install \
    --set profile=demo \
    --set components.telemetry.enabled=true \
    --skip-confirmation

echo "Сборка образа приложения с очисткой кеша..." &&
docker build \
    --no-cache \
    --build-arg APP_ENV=prod \
    -t journal-api:v1 .

echo "Импорт образа в кластер Minikube..." &&
minikube image load journal-api:v1 \
    --alsologtostderr \
    --v=3

echo "Базовое конфигурирование кластера:" &&
{
    kubectl apply -f kubernetes/namespace.yaml
    
    kubectl label namespace journal-system \
        istio-injection=enabled \
        --overwrite
    
    declare -a manifests=(
        prometheus.yaml
        map.yaml
        test-pod.yaml
        deployment.yaml
        service.yaml
        data.yaml
        d_set.yaml
        c_job.yaml
        istio/gateway.yaml
        istio/service_ve.yaml
        istio/rule_d.yaml
    )
    
    for manifest in "${manifests[@]}"; do
        echo "Применение ${manifest}..."
        kubectl apply -f "kubernetes/${manifest}"
    done
}

echo "Проверка состояния компонентов..." &&
{
    kubectl wait --namespace=journal-system \
        --for=condition=ContainersReady \
        pod/journal-test \
        --timeout=75s
    
    kubectl rollout status --namespace=journal-system \
        deployment/journal-api \
        --timeout=150s
    
    kubectl wait --namespace=journal-system \
        --for=condition=Available \
        deployment/prometheus \
        --timeout=90s
}

cat <<EOF

[ Система готова к работе ]

Доступные команды для тестирования:

1. Проброс портов шлюза:
   kubectl port-forward -n istio-system svc/istio-ingressgateway 8080:80

2. Примеры API-запросов:
   Проверка здоровья: curl http://localhost:8080/status
   Добавление записи: curl -X POST http://localhost:8080/log -H 'Content-Type: application/json' -d '{"message":"demo"}'
   Чтение логов: curl http://localhost:8080/logs

3. Работа с метриками:
   Прикладные метрики: curl http://localhost:8080/metrics
   Prometheus UI: kubectl port-forward -n journal-system svc/prometheus 9090:9090
   Пример запроса: journal_log_requests_total

4. Мониторинг задач:
   Архивация: kubectl get cronjobs -n journal-system
   Сбор логов: kubectl get daemonsets -n journal-system

EOF