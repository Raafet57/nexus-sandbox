# Kubernetes Deployment: Nexus Global Payments

> This document defines the Kubernetes deployment architecture for the Nexus Global Payments platform, covering multi-region deployment, GitOps workflows, service mesh, and observability integration.

> [!IMPORTANT]
> **Reference Architecture Only**: This document describes a **production-grade Kubernetes deployment** for the actual Nexus scheme. The sandbox is designed for **local development and learning** using Docker Compose:
> ```bash
> # Sandbox deployment (what you actually run)
> docker compose -f docker-compose.lite.yml up -d
> ```
> See [README.md](../../README.md) for sandbox setup instructions.

## Deployment Overview

Nexus requires a highly available, multi-region Kubernetes deployment to ensure global payment processing continuity.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Global Load Balancer                         │
│                (Anycast, GeoDNS routing)                       │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Asia-Pacific  │ │    Europe     │ │   Americas    │
│  EKS/GKE      │ │   AKS/GKE     │ │   EKS/GKE     │
│  Singapore    │ │   Frankfurt   │ │  Virginia     │
└───────────────┘ └───────────────┘ └───────────────┘
```

---

## 1. Cluster Architecture

### 1.1 Node Pool Configuration

```yaml
# Primary node pool for Gateway services
apiVersion: node.gke.io/v1
kind: NodeConfig
metadata:
  name: gateway-nodes
spec:
  machineType: n2-standard-8  # 8 vCPU, 32GB RAM
  diskSizeGb: 100
  diskType: pd-ssd
  labels:
    workload-type: gateway
    criticality: high
  taints:
    - key: dedicated
      value: gateway
      effect: NoSchedule
  nodePoolAutoscaling:
    enabled: true
    minNodeCount: 3
    maxNodeCount: 20
---
# Node pool for FX services
apiVersion: node.gke.io/v1
kind: NodeConfig
metadata:
  name: fx-service-nodes
spec:
  machineType: n2-standard-4  # 4 vCPU, 16GB RAM
  diskSizeGb: 50
  diskType: pd-ssd
  labels:
    workload-type: fx-service
  nodePoolAutoscaling:
    enabled: true
    minNodeCount: 2
    maxNodeCount: 10
```

### 1.2 Namespace Strategy

```yaml
# Namespace structure
namespaces:
  - nexus-gateway        # Gateway and core services
  - nexus-fx             # FX quote and rate services
  - nexus-proxy          # Proxy resolution services
  - nexus-observability  # Prometheus, Grafana, Jaeger
  - nexus-istio-system   # Service mesh control plane
  - nexus-argocd         # GitOps controller
  - nexus-secrets        # External Secrets Operator
```

---

## 2. Service Deployments

### 2.1 Nexus Gateway Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nexus-gateway
  namespace: nexus-gateway
  labels:
    app: nexus-gateway
    version: v1.0.0
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 2
  selector:
    matchLabels:
      app: nexus-gateway
  template:
    metadata:
      labels:
        app: nexus-gateway
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app: nexus-gateway
              topologyKey: kubernetes.io/hostname
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: workload-type
                    operator: In
                    values:
                      - gateway
      tolerations:
        - key: dedicated
          operator: Equal
          value: gateway
          effect: NoSchedule
      containers:
        - name: gateway
          image: nexus/gateway:v1.0.0
          ports:
            - name: grpc
              containerPort: 8080
            - name: metrics
              containerPort: 9090
            - name: health
              containerPort: 8081
          resources:
            requests:
              cpu: "2"
              memory: "4Gi"
            limits:
              cpu: "4"
              memory: "8Gi"
          env:
            - name: POSTGRES_HOST
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: host
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: url
            - name: KAFKA_BROKERS
              valueFrom:
                configMapKeyRef:
                  name: kafka-config
                  key: brokers
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8081
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8081
            initialDelaySeconds: 5
            periodSeconds: 5
          volumeMounts:
            - name: tls-certs
              mountPath: /etc/nexus/certs
              readOnly: true
      volumes:
        - name: tls-certs
          secret:
            secretName: nexus-gateway-tls
      serviceAccountName: nexus-gateway
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
---
apiVersion: v1
kind: Service
metadata:
  name: nexus-gateway
  namespace: nexus-gateway
spec:
  type: ClusterIP
  ports:
    - name: grpc
      port: 8080
      targetPort: 8080
    - name: metrics
      port: 9090
      targetPort: 9090
  selector:
    app: nexus-gateway
```

### 2.2 Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nexus-gateway-hpa
  namespace: nexus-gateway
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nexus-gateway
  minReplicas: 5
  maxReplicas: 50
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    - type: Pods
      pods:
        metric:
          name: grpc_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
```

### 2.3 FX Quote Service Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fx-quote-service
  namespace: nexus-fx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fx-quote-service
  template:
    metadata:
      labels:
        app: fx-quote-service
    spec:
      containers:
        - name: fx-service
          image: nexus/fx-quote-service:v1.0.0
          ports:
            - name: grpc
              containerPort: 8080
          resources:
            requests:
              cpu: "1"
              memory: "2Gi"
            limits:
              cpu: "2"
              memory: "4Gi"
          env:
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: url
```

---

## 3. Service Mesh (Istio)

### 3.1 Gateway Configuration

```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: nexus-gateway
  namespace: nexus-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 443
        name: https
        protocol: HTTPS
      tls:
        mode: MUTUAL
        credentialName: nexus-gateway-credential
        minProtocolVersion: TLSV1_3
      hosts:
        - "gateway.nexusglobalpayments.org"
    - port:
        number: 8443
        name: grpc
        protocol: GRPC
      tls:
        mode: MUTUAL
        credentialName: nexus-grpc-credential
      hosts:
        - "grpc.nexusglobalpayments.org"
```

### 3.2 Virtual Service for Traffic Routing

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: nexus-gateway-vs
  namespace: nexus-gateway
spec:
  hosts:
    - "gateway.nexusglobalpayments.org"
  gateways:
    - nexus-gateway
  http:
    - match:
        - uri:
            prefix: /api/v1/quotes
      route:
        - destination:
            host: fx-quote-service.nexus-fx.svc.cluster.local
            port:
              number: 8080
      timeout: 5s
      retries:
        attempts: 3
        perTryTimeout: 2s
    - match:
        - uri:
            prefix: /api/v1/payments
      route:
        - destination:
            host: nexus-gateway.nexus-gateway.svc.cluster.local
            port:
              number: 8080
      timeout: 60s  # Payment SLA
```

### 3.3 Destination Rules (mTLS)

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: nexus-gateway-mtls
  namespace: nexus-gateway
spec:
  host: "*.nexus-gateway.svc.cluster.local"
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
    connectionPool:
      http:
        h2UpgradePolicy: UPGRADE
        http1MaxPendingRequests: 1024
        http2MaxRequests: 1024
      tcp:
        maxConnections: 100
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 60s
      maxEjectionPercent: 50
```

### 3.4 Authorization Policy

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: nexus-gateway-authz
  namespace: nexus-gateway
spec:
  selector:
    matchLabels:
      app: nexus-gateway
  rules:
    - from:
        - source:
            namespaces: ["nexus-istio-system"]
            principals: ["cluster.local/ns/nexus-istio-system/sa/istio-ingressgateway-service-account"]
      to:
        - operation:
            ports: ["8080"]
    - from:
        - source:
            namespaces: ["nexus-fx"]
      to:
        - operation:
            methods: ["POST"]
            paths: ["/internal/rates/*"]
```

---

## 4. GitOps with ArgoCD

### 4.1 Application Definition

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nexus-gateway
  namespace: nexus-argocd
spec:
  project: nexus-production
  source:
    repoURL: https://github.com/nexus/k8s-manifests.git
    targetRevision: main
    path: environments/production/gateway
  destination:
    server: https://kubernetes.default.svc
    namespace: nexus-gateway
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  revisionHistoryLimit: 10
```

### 4.2 Progressive Delivery (Argo Rollouts)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: nexus-gateway
  namespace: nexus-gateway
spec:
  replicas: 5
  strategy:
    canary:
      canaryService: nexus-gateway-canary
      stableService: nexus-gateway-stable
      trafficRouting:
        istio:
          virtualService:
            name: nexus-gateway-vs
            routes:
              - primary
      steps:
        - setWeight: 5
        - pause: { duration: 5m }
        - setWeight: 20
        - pause: { duration: 10m }
        - setWeight: 50
        - pause: { duration: 15m }
        - setWeight: 100
      analysis:
        templates:
          - templateName: success-rate
        startingStep: 2
        args:
          - name: service-name
            value: nexus-gateway
  selector:
    matchLabels:
      app: nexus-gateway
  template:
    metadata:
      labels:
        app: nexus-gateway
    spec:
      containers:
        - name: gateway
          image: nexus/gateway:v1.0.0
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      interval: 1m
      successCondition: result[0] >= 0.99
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus.nexus-observability:9090
          query: |
            sum(rate(grpc_server_handled_total{service="{{args.service-name}}", grpc_code="OK"}[5m])) /
            sum(rate(grpc_server_handled_total{service="{{args.service-name}}"}[5m]))
```

---

## 5. Secrets Management

### 5.1 External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: postgres-credentials
  namespace: nexus-gateway
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: vault-backend
  target:
    name: postgres-credentials
    creationPolicy: Owner
  data:
    - secretKey: host
      remoteRef:
        key: nexus/production/postgres
        property: host
    - secretKey: username
      remoteRef:
        key: nexus/production/postgres
        property: username
    - secretKey: password
      remoteRef:
        key: nexus/production/postgres
        property: password
---
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "https://vault.nexusglobalpayments.org"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "nexus-production"
```

---

## 6. Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: nexus-gateway-network-policy
  namespace: nexus-gateway
spec:
  podSelector:
    matchLabels:
      app: nexus-gateway
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: nexus-istio-system
          podSelector:
            matchLabels:
              istio: ingressgateway
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: nexus-fx
      ports:
        - protocol: TCP
          port: 8080
    - to:
        - namespaceSelector:
            matchLabels:
              name: nexus-proxy
      ports:
        - protocol: TCP
          port: 8080
    - to:
        - ipBlock:
            cidr: 10.0.0.0/8  # Internal PostgreSQL
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - ipBlock:
            cidr: 10.0.0.0/8  # Internal Redis
      ports:
        - protocol: TCP
          port: 6379
```

---

## 7. Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: nexus-gateway
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: nexus-gateway-pdb
  namespace: nexus-gateway
spec:
  minAvailable: 3
  selector:
    matchLabels:
      app: nexus-gateway
```

---

## 8. Multi-Region Deployment

### 8.1 Cluster Federation

```yaml
# KubeFed federated deployment
apiVersion: types.kubefed.io/v1beta1
kind: FederatedDeployment
metadata:
  name: nexus-gateway
  namespace: nexus-gateway
spec:
  template:
    spec:
      replicas: 5
      selector:
        matchLabels:
          app: nexus-gateway
      template:
        spec:
          containers:
            - name: gateway
              image: nexus/gateway:v1.0.0
  placement:
    clusters:
      - name: apac-singapore
      - name: europe-frankfurt
      - name: americas-virginia
  overrides:
    - clusterName: apac-singapore
      clusterOverrides:
        - path: "/spec/replicas"
          value: 10  # Higher traffic in APAC
```

### 8.2 Global Load Balancer Configuration

```yaml
# GKE Multi-Cluster Ingress
apiVersion: networking.gke.io/v1
kind: MultiClusterIngress
metadata:
  name: nexus-global-ingress
  namespace: nexus-gateway
spec:
  template:
    spec:
      backend:
        serviceName: nexus-gateway-mcs
        servicePort: 8080
      rules:
        - host: gateway.nexusglobalpayments.org
          http:
            paths:
              - path: /*
                backend:
                  serviceName: nexus-gateway-mcs
                  servicePort: 8080
```

---

## 9. Disaster Recovery

### 9.1 Velero Backup Configuration

```yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: nexus-daily-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM UTC
  template:
    includedNamespaces:
      - nexus-gateway
      - nexus-fx
      - nexus-proxy
    excludedResources:
      - events
      - pods
    storageLocation: aws-s3-backup
    ttl: 720h  # 30 days retention
```

---

## Related Documents

- [C4 Architecture](../architecture/C4_ARCHITECTURE.md)
- [Observability](OBSERVABILITY.md)
- [Security Model](../security/SECURITY_MODEL.md)

---

*Deployment patterns follow Kubernetes best practices and CNCF recommendations for production workloads.*
