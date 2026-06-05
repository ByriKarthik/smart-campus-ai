# 🎓 Smart Campus AI - Cloud Native University Management System

## 📌 Overview

Smart Campus AI is a cloud-native University Management System (UMS) developed using Django and PostgreSQL. The project aims to digitalize and automate various academic and administrative activities within a university environment.

The system provides dedicated modules for students, faculty members, and administrators, enabling efficient management of attendance, academics, notifications, planning, and campus services through a centralized platform.

In addition to application development, the project incorporates modern Cloud Computing and DevOps practices including containerization, orchestration, CI/CD automation, monitoring, and infrastructure management.

---

# 🎯 Objectives

The primary objectives of the project are:

- Digitalization of campus operations
- Centralized management of academic information
- Automated attendance and notification systems
- Improved communication between students and faculty
- Cloud-native deployment using container technologies
- Automated deployment using CI/CD pipelines
- Real-time monitoring and observability

---

# 🚀 Key Features

## 👨‍🎓 Student Module

- Student registration and login
- Attendance tracking
- Academic information access
- Notifications and announcements
- Planner and scheduling support

## 👨‍🏫 Faculty Module

- Attendance management
- Student information management
- Academic activity monitoring
- Notification generation

## 👨‍💼 Administrator Module

- User management
- Academic data management
- Monitoring system performance
- Overall platform administration

## 🔔 Notification System

- Automated notification delivery
- Event-based messaging
- Background task execution using Celery

## 📅 Planner Module

- Activity scheduling
- Event management
- Reminder generation

---

# 🛠 Technology Stack

## Backend

- Python
- Django
- Django REST Framework (DRF)
- Gunicorn

## Database

- PostgreSQL

## Cache & Message Broker

- Redis

## Background Task Processing

- Celery

## Web Server

- Nginx

## Containerization

- Docker
- Docker Compose

## Container Orchestration

- Kubernetes
- Minikube

## CI/CD

- Jenkins
- GitHub Webhooks
- ngrok

## Monitoring

- Prometheus
- Grafana
- Node Exporter

---

# 🏗 System Architecture

```text
Users
  |
  v
Nginx
  |
  v
Django Application Pods
  |
  +--------------------+
  |                    |
  v                    v
PostgreSQL          Redis
                        |
                        v
                    Celery

Monitoring Stack
----------------
Node Exporter
      |
      v
Prometheus
      |
      v
Grafana
```

---

# ☁️ Cloud Native Architecture

The project follows a cloud-native architecture by utilizing containerization and orchestration technologies.

Each application component is deployed as an independent container, improving scalability, maintainability, and fault tolerance.

### Application Layer

- Django Web Application
- Celery Worker

### Data Layer

- PostgreSQL Database
- Redis Message Broker

### Infrastructure Layer

- Docker Containers
- Kubernetes Pods
- Kubernetes Deployments
- Kubernetes Services

### Monitoring Layer

- Prometheus
- Grafana
- Node Exporter

---

# 🐳 Containerization using Docker

Docker is used to package the application and its dependencies into portable containers.

### Benefits

- Consistent execution across environments
- Easy deployment
- Dependency isolation
- Improved portability

### Docker Components Used

- Dockerfile
- Docker Compose
- Docker Images
- Docker Containers

---

# ☸️ Kubernetes Deployment

The project is deployed on a Kubernetes cluster using Minikube.

Kubernetes provides:

- Container orchestration
- Self-healing
- Load balancing
- Scalability
- Rolling updates

## Kubernetes Resources Used

### Deployments

- smartcampus-web
- celery
- postgres
- redis
- nginx
- prometheus
- grafana

### Services

- NodePort Services
- ClusterIP Services

### Persistent Storage

- Persistent Volume Claims (PVC)

### Secrets

- Docker Hub Image Pull Secret

---

# 🔄 High Availability

The Django application is deployed with multiple replicas.

```yaml
replicas: 2
```

### Benefits

- High availability
- Fault tolerance
- Load balancing
- Reduced downtime

If one pod fails, Kubernetes automatically creates a replacement pod.

---

# 🌐 Nginx Reverse Proxy

Nginx acts as a reverse proxy and load balancer.

### Responsibilities

- Receives user requests
- Routes requests to Django pods
- Load balances traffic
- Improves scalability
- Provides a single entry point

### Request Flow

```text
User
 |
 v
NodePort Service
 |
 v
Nginx
 |
 v
Django Pods
 |
 v
PostgreSQL
```

---

# ⚡ Redis & Celery Integration

## Redis

Redis is used as an in-memory message broker.

### Responsibilities

- Queue management
- Temporary data storage
- Fast message passing

## Celery

Celery executes background tasks asynchronously.

### Examples

- Notification processing
- Scheduled tasks
- Background computations

### Workflow

```text
Django
   |
   v
Redis Queue
   |
   v
Celery Worker
```

---

# 🔁 CI/CD Pipeline

The project implements Continuous Integration and Continuous Deployment using Jenkins.

## Workflow

```text
Developer
    |
Git Push
    |
GitHub Repository
    |
Webhook
    |
ngrok
    |
Jenkins Pipeline
    |
Kubernetes Deployment
```

### Pipeline Stages

#### 1. Checkout Source

Retrieves latest source code from GitHub.

#### 2. Verify Cluster

Verifies Kubernetes cluster connectivity.

#### 3. Restart Smart Campus

Performs rolling restart of application deployments.

#### 4. Wait For Rollout

Waits until deployment rollout is completed.

#### 5. Verify Deployment

Confirms successful deployment.

---

# 🔗 GitHub Webhooks

GitHub Webhooks are used to automatically trigger Jenkins builds whenever new code is pushed to the repository.

### Benefits

- Eliminates manual deployment
- Enables automation
- Faster delivery pipeline
- Continuous Integration support

---

# 🌍 ngrok Integration

Since Jenkins is hosted locally, GitHub cannot directly access it.

ngrok provides a secure public URL that tunnels requests to the local Jenkins server.

```text
GitHub
   |
ngrok URL
   |
Local Jenkins
```

---

# 📊 Monitoring & Observability

The project implements a complete monitoring stack.

## Node Exporter

Collects system-level metrics:

- CPU Usage
- Memory Usage
- Disk Usage
- Network Statistics

## Prometheus

Prometheus continuously scrapes metrics from Node Exporter and Kubernetes components.

### Responsibilities

- Metrics collection
- Time-series storage
- Querying and analysis

## Grafana

Grafana visualizes metrics through dashboards.

### Monitored Metrics

- CPU utilization
- Memory consumption
- Pod status
- System health
- Resource utilization

---

# 🔒 Security Features

- Kubernetes Secrets
- Container Isolation
- Secure Service Communication
- Persistent Volume Protection
- Future RBAC Integration

---

# 📈 Scalability

The architecture supports horizontal scaling through Kubernetes.

### Example

```bash
kubectl scale deployment smartcampus-web --replicas=5
```

### Benefits

- Increased throughput
- Better fault tolerance
- Improved user experience during peak loads

---

# 📁 Project Structure

```text
smart-campus-ai/
│
├── campus_ai/
│   ├── accounts/
│   ├── academics/
│   ├── attendance/
│   ├── notifications/
│   ├── planner/
│   └── campus_ai/
│
├── k8s/
│   ├── web-deployment.yaml
│   ├── postgres-deployment.yaml
│   ├── redis-deployment.yaml
│   ├── celery-deployment.yaml
│   ├── nginx-deployment.yaml
│   └── monitoring/
│
├── nginx/
│   └── default.conf
│
├── Dockerfile
├── Dockerfile.jenkins
├── docker-compose.yml
├── prometheus.yml
└── Jenkinsfile
```

---

# 🎓 Learning Outcomes

This project provided practical experience in:

- Full Stack Development
- Docker Containerization
- Kubernetes Orchestration
- CI/CD Pipeline Automation
- GitHub Webhooks
- Jenkins Pipeline Development
- Infrastructure Monitoring
- Cloud Native Application Design
- DevOps Best Practices

---

# 🔮 Future Enhancements

- AWS Cloud Deployment
- Kubernetes Ingress Controller
- Horizontal Pod Autoscaling (HPA)
- Role-Based Access Control (RBAC)
- Automated Docker Build & Push Pipeline
- Multi-Node Kubernetes Cluster
- AI-Powered Analytics
- Email and SMS Integration
- Advanced Monitoring & Alerting

---

# 🏆 Conclusion

Smart Campus AI demonstrates the implementation of a modern cloud-native university management system using Django, PostgreSQL, Docker, Kubernetes, Jenkins, Prometheus, and Grafana.

The project combines software engineering principles with Cloud Computing and DevOps practices to build a scalable, resilient, highly available, and production-oriented platform capable of supporting real-world academic environments.

---

## 👨‍💻 Developed By

**Karthik Byri**

B.Tech Computer Science & Engineering

Cloud Computing • DevOps • Full Stack Development • Kubernetes • Machine Learning
