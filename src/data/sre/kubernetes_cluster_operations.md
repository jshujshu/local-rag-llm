# Kubernetes Cluster Operations Guide

## Overview
This document provides operational guidelines for managing production Kubernetes clusters.

Clusters are deployed across multiple regions using managed services such as Amazon EKS, Google GKE, or Azure AKS.

---

## Cluster Architecture

Core Components:
- API Server
- Controller Manager
- Scheduler
- etcd (key-value store)
- kubelet (node agent)

Node Types:
- System Nodes: Run core cluster services
- Application Nodes: Run user workloads
- Spot Nodes: Cost-optimized, preemptible workloads

---

## Deployment Workflow

1. Build container image:
   docker build -t registry.example.com/app:latest .
   docker push registry.example.com/app:latest

2. Kubernetes Deployment YAML:

apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
      - name: web-app
        image: registry.example.com/app:latest
        ports:
        - containerPort: 8080

3. Apply changes:
   kubectl apply -f deployment.yaml

---

## Scaling Operations

Manual scaling:
kubectl scale deployment web-app --replicas=5

Horizontal Pod Autoscaler:
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

---

## Troubleshooting

Pod issues:
- kubectl get pods
- kubectl describe pod <pod-name>
- kubectl logs <pod-name>

Node issues:
- kubectl get nodes
- kubectl describe node <node-name>

Common problems:
- ImagePullBackOff → registry auth issue
- CrashLoopBackOff → application error
- Pending pods → insufficient resources

---

## Networking

- Services: ClusterIP, NodePort, LoadBalancer
- Ingress controllers: NGINX, Traefik
- CNI plugins: Calico, Cilium

---

## Maintenance

- Monthly Kubernetes version upgrades
- Quarterly credential rotation
- Daily etcd backups