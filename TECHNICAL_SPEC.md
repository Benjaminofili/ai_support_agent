# Technical Specification Document
## AI Customer Support Agent (B2B SaaS) — MVP

**Version:** 1.1   
**Developer:** Solo  
**Status:** SINGLE SOURCE OF TRUTH

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Folder Structure](#4-folder-structure)
5. [Development Setup](#5-development-setup)
6. [Environment Variables](#6-environment-variables)
7. [Database Models](#7-database-models)
8. [API Endpoints](#8-api-endpoints)
9. [Celery Tasks](#9-celery-tasks)
10. [Integration Guides](#10-integration-guides)
11. [Day-by-Day Implementation](#11-day-by-day-implementation)
12. [Testing Checklist](#12-testing-checklist)
13. [Defense Preparation](#13-defense-preparation)

---

## 1. Project Overview

### What We're Building
A B2B SaaS platform where companies can:
1. Upload their documents (PDFs, text files)
2. The system "learns" from these documents using AI
3. Customers can ask questions via Website Chat, WhatsApp, or Email
4. The AI responds automatically using only the company's knowledge base

### Core Concept: RAG (Retrieval-Augmented Generation)
```
Customer Question
↓
[Search Vector Database for relevant document chunks]
↓
[Inject retrieved context into prompt]
↓
[Send to OpenAI GPT-4o]
↓
[Return AI response to customer]
```

We are **NOT** fine-tuning or retraining any model. We're giving the AI a "cheat sheet" of company info before it answers.

---

## 2. Architecture

### System Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL WORLD                              │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│  Website Chat   │    WhatsApp     │         Email                   │
│  (JavaScript)   │    (Twilio)     │      (Postmark)                 │
└────────┬────────┴────────┬────────┴────────────┬────────────────────┘
         │                 │                      │
         ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DJANGO APPLICATION                             │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐    │
│ │ /api/chat/  │ │/api/whatsapp│ │ /api/email/ │ │ /api/upload│    │
│ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └─────┬──────┘    │
│        │               │                │               │           │
│        └───────────────┴────────────────┴───────────────┘           │
│                        │                                            │
│                        ▼                                            │
│              ┌─────────────────────┐                                │
│              │  Celery Task Queue  │                                │
│              └──────────┬──────────┘                                │
└───────────────────────────────────┼──────────────────────────────────┘
                                    │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                           │
        ▼                          ▼                           ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Redis       │    │   PostgreSQL    │    │   OpenAI API    │
│(Message Broker) │    │   + pgvector    │    │ (GPT-4o/Embed)  │
│    [Docker]     │    │    [Docker]     │    │   [External]    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Development Setup (Option B — Hybrid)
- **Docker Container:** PostgreSQL + pgvector (port 5432)
- **Docker Container:** Redis (port 6379)
- **Windows (directly):** Python + Django (port 8000)
- **Windows (directly):** Python + Celery (worker)

### Request Flow Example (WhatsApp Message)
1. Customer sends "What is your return policy?" to WhatsApp
2. Twilio receives it → sends POST to your `/api/webhooks/whatsapp/`
3. Django receives webhook → returns 200 OK immediately
4. Django pushes task to Celery queue
5. Celery worker picks up task:
   - a. Converts question to embedding vector
   - b. Searches pgvector for similar document chunks
   - c. Builds prompt: "Using this context: [chunks], answer: [question]"
   - d. Calls OpenAI GPT-4o
   - e. Sends response back via Twilio API
6. Customer receives answer on WhatsApp

---

## 3. Tech Stack

### Exact Versions (Pin These)
```
Python==3.11.x
Django==5.0.6
django-ninja==1.1.0
celery==5.4.0
redis==5.0.4
psycopg2-binary==2.9.9
pgvector==0.2.5
langchain==0.2.5
langchain-openai==0.1.8
langchain-community==0.2.5
openai==1.35.3
python-multipart==0.0.9
twilio==9.1.0
httpx==0.27.0
python-dotenv==1.0.1
PyPDF2==3.0.1
```

### Why Each Tool
| Tool | Purpose |
|------|---------|
| Django | Web framework, ORM, admin panel |
| django-ninja | Fast API development (faster than DRF) |
| Celery | Background task processing |
| Redis | Message broker for Celery |
| PostgreSQL | Primary database |
| pgvector | Vector similarity search (in Postgres) |
| LangChain | Document loading, chunking, RAG helpers |
| OpenAI | Embeddings + Chat completions |
| Twilio | WhatsApp messaging |
| Postmark | Email sending/receiving |

---

## 4. Folder Structure
```
ai_support_agent/
│
├── docker-compose.yml          # PostgreSQL + Redis
├── .env                        # Environment variables
├── .env.example                # Template for .env
├── requirements.txt            # Python dependencies
├── manage.py                   # Django CLI
├── TECHNICAL_SPEC.md           # This document
│
├── config/
│   ├── __init__.py
│   ├── settings.py             # Django settings
│   ├── urls.py                 # URL routing
│   ├── celery.py               # Celery configuration
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── __init__.py
│   │
│   ├── companies/              # Multi-tenancy
│   │   ├── __init__.py
│   │   ├── models.py           # Company model
│   │   ├── admin.py            # Admin registration
│   │   ├── apps.py             # App config
│   │   └── migrations/
│   │
│   ├── knowledge/              # Document ingestion
│   │   ├── __init__.py
│   │   ├── models.py           # Document, DocumentChunk models
│   │   ├── admin.py            # Admin registration
│   │   ├── apps.py             # App config
│   │   ├── api.py              # Upload endpoints
│   │   ├── services.py         # Ingestion logic
│   │   ├── tasks.py            # Celery tasks for processing
│   │   └── migrations/
│   │
│   ├── conversations/          # Chat logic
│   │   ├── __init__.py
│   │   ├── models.py           # Conversation, Message models
│   │   ├── admin.py            # Admin registration
│   │   ├── apps.py             # App config
│   │   ├── api.py              # Chat endpoints
│   │   ├── services.py         # RAG logic
│   │   ├── tasks.py            # Celery tasks for AI responses
│   │   └── migrations/
│   │
│   └── channels/               # WhatsApp, Email, Web integrations
│       ├── __init__.py
│       ├── admin.py            # Empty for now
│       ├── apps.py             # App config
│       ├── models.py           # Empty for now
│       ├── webhooks.py         # Webhook handlers
│       ├── whatsapp.py         # Twilio logic
│       ├── email.py            # Postmark logic
│       ├── tasks.py            # Celery tasks for sending
│       └── migrations/
│
├── templates/
│   ├── base.html
│   ├── dashboard/
│   │   ├── index.html
│   │   ├── upload.html
│   │   └── conversations.html
│   └── chat/
│       └── widget.html         # Embeddable chat widget
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── chat-widget.js
│
└── media/                      # Uploaded files (gitignored)
    └── documents/
```

---

## 5. Development Setup

### 5.1 Prerequisites
- Python 3.11+ installed on Windows
- Docker Desktop installed and running
- Git (optional but recommended)

### 5.2 Initial Setup (Day 0)

#### Step 1: Create Project Folder
```bash
mkdir ai_support_agent
cd ai_support_agent
```

#### Step 2: Create docker-compose.yml
```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    container_name: support_agent_db
    environment:
      POSTGRES_DB: support_agent
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: support_agent_redis
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

#### Step 3: Start Docker Containers
```bash
docker-compose up -d
docker-compose ps
```

#### Step 4: Create Python Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

#### Step 5: Create requirements.txt
```text
Django==5.0.6
django-ninja==1.1.0
celery==5.4.0
redis==5.0.4
psycopg2-binary==2.9.9
pgvector==0.2.5
langchain==0.2.5
langchain-openai==0.1.8
langchain-community==0.2.5
openai==1.35.3
python-multipart==0.0.9
twilio==9.1.0
httpx==0.27.0
python-dotenv==1.0.1
pypdf==4.2.0
```

#### Step 6: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 7: Verify Connections
```bash
python -c "import psycopg2; conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/support_agent'); print('Database Connected!')"
python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); print('Redis:', r.ping())"
```

### 5.3 Django Project Setup (Day 1)

#### Step 1: Create Django Project
```bash
django-admin startproject config .
```

#### Step 2: Create App Directories (Windows)
```bash
mkdir apps
cd apps
type nul > __init__.py
mkdir companies
mkdir knowledge
mkdir conversations
mkdir channels
cd ..
```

#### Step 3: Create Apps
```bash
python manage.py startapp companies apps/companies
python manage.py startapp knowledge apps/knowledge
python manage.py startapp conversations apps/conversations
python manage.py startapp channels apps/channels
```

#### Step 4: Create Required Folders
```bash
mkdir templates
mkdir static
mkdir media
```

#### Step 5: Create .env File
See Section 6 for contents.

#### Step 6: Update config/settings.py
See Section 5.4 for complete file.

#### Step 7: Update App Configs
Each `apps/*/apps.py` must have `name = 'apps.<appname>'`

#### Step 8: Create Models
See Section 7 for all model code.

#### Step 9: Create Admin Files
See Section 7.5 for admin code.

#### Step 10: Enable pgvector Extension
```bash
python manage.py makemigrations knowledge --empty --name enable_pgvector
```

Edit `apps/knowledge/migrations/0001_enable_pgvector.py`:
```python
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = []
    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;"
        ),
    ]
```

#### Step 11: Create and Run Migrations
```bash
python manage.py makemigrations companies
python manage.py makemigrations knowledge
python manage.py makemigrations conversations
python manage.py makemigrations channels
python manage.py migrate
```

#### Step 12: Create Superuser
```bash
python manage.py createsuperuser
```

#### Step 13: Run Server
```bash
python manage.py runserver
```

### 5.4 Complete config/settings.py
```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key')

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'ninja',
    
    # Our apps
    'apps.companies',
    'apps.knowledge',
    'apps.conversations',
    'apps.channels',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'support_agent',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
DEFAULT_AI_MODEL = os.getenv('DEFAULT_AI_MODEL', 'gpt-4o-mini')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
MAX_TOKENS = int(os.getenv('MAX_TOKENS', 1000))
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 500))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 50))

# Twilio
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', '')

# Postmark
POSTMARK_SERVER_TOKEN = os.getenv('POSTMARK_SERVER_TOKEN', '')
POSTMARK_FROM_EMAIL = os.getenv('POSTMARK_FROM_EMAIL', '')
```

### 5.5 config/celery.py
```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

### 5.6 config/__init__.py
```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### 5.7 Running the Application

**Terminal 1 — Django:**
```bash
venv\Scripts\activate
python manage.py runserver
```

**Terminal 2 — Celery Worker:**
```bash
venv\Scripts\activate
celery -A config worker --loglevel=info --pool=solo
```

---

## 6. Environment Variables

### .env
```env
# Django
DEBUG=True
SECRET_KEY=django-insecure-change-this-to-random-string-12345
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Docker)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/support_agent

# Redis (Docker)
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here

# Twilio (WhatsApp)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Postmark (Email)
POSTMARK_SERVER_TOKEN=your-postmark-token
POSTMARK_FROM_EMAIL=support@yourdomain.com

# AI Settings
DEFAULT_AI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
MAX_TOKENS=1000
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### .env.example
Same as above but with placeholder values. Commit this to git, not `.env`.

---

## 7. Database Models

### 7.1 apps/companies/models.py
```python
from django.db import models
from django.contrib.auth.models import User
import uuid


class Company(models.Model):
    """
    Represents a B2B client company.
    All documents and conversations belong to a company.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='owned_companies'
    )
    
    api_key = models.CharField(max_length=64, unique=True, blank=True)
    
    ai_personality = models.TextField(
        default="You are a helpful customer support agent. Be concise and friendly."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "companies"
    
    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = uuid.uuid4().hex + uuid.uuid4().hex
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
```

### 7.2 apps/knowledge/models.py
```python
from django.db import models
from pgvector.django import VectorField
import uuid


class Document(models.Model):
    """
    A document uploaded by a company.
    """
    class SourceType(models.TextChoices):
        PDF = 'pdf', 'PDF File'
        TEXT = 'text', 'Text File'
        PASTE = 'paste', 'Pasted Content'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    
    title = models.CharField(max_length=255)
    source_type = models.CharField(max_length=10, choices=SourceType.choices)
    file = models.FileField(upload_to='documents/', null=True, blank=True)
    raw_content = models.TextField(blank=True)
    
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING
    )
    error_message = models.TextField(blank=True)
    chunk_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.company.name} - {self.title}"


class DocumentChunk(models.Model):
    """
    A chunk of text from a document, with its vector embedding.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    
    content = models.TextField()
    chunk_index = models.IntegerField()
    
    embedding = VectorField(dimensions=1536)
    
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['document', 'chunk_index']
    
    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"
```

### 7.3 apps/conversations/models.py
```python
from django.db import models
import uuid


class Conversation(models.Model):
    """
    A conversation thread with a customer.
    """
    class Channel(models.TextChoices):
        WEB = 'web', 'Website Chat'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        EMAIL = 'email', 'Email'
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        RESOLVED = 'resolved', 'Resolved'
        HANDED_OFF = 'handed_off', 'Handed Off to Human'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    
    channel = models.CharField(max_length=20, choices=Channel.choices)
    customer_identifier = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255, blank=True)
    
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.ACTIVE
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.channel} - {self.customer_identifier}"


class Message(models.Model):
    """
    A single message in a conversation.
    """
    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        ASSISTANT = 'assistant', 'AI Assistant'
        SYSTEM = 'system', 'System'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    
    source_chunks = models.ManyToManyField(
        'knowledge.DocumentChunk',
        blank=True,
        related_name='used_in_messages'
    )
    
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
```

### 7.4 apps/channels/models.py
```python
from django.db import models

# No models needed yet - this app handles webhooks
```

### 7.5 Admin Files

**apps/companies/admin.py:**
```python
from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'owner', 'created_at']
    search_fields = ['name', 'slug']
    readonly_fields = ['id', 'api_key', 'created_at', 'updated_at']
```

**apps/knowledge/admin.py:**
```python
from django.contrib import admin
from .models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'source_type', 'status', 'chunk_count', 'created_at']
    list_filter = ['status', 'source_type', 'company']
    search_fields = ['title']
    readonly_fields = ['id', 'chunk_count', 'created_at', 'updated_at']


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['document', 'chunk_index', 'created_at']
    list_filter = ['document__company']
    readonly_fields = ['id', 'embedding', 'created_at']
```

**apps/conversations/admin.py:**
```python
from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['id', 'role', 'content', 'created_at']
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['customer_identifier', 'company', 'channel', 'status', 'created_at']
    list_filter = ['channel', 'status', 'company']
    search_fields = ['customer_identifier']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'role', 'short_content', 'created_at']
    list_filter = ['role', 'conversation__company']
    readonly_fields = ['id', 'created_at']
    
    def short_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'
```

**apps/channels/admin.py:**
```python
from django.contrib import admin

# No models to register yet
```

### 7.6 App Configs

**apps/companies/apps.py:**
```python
from django.apps import AppConfig

class CompaniesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.companies'
```

**apps/knowledge/apps.py:**
```python
from django.apps import AppConfig

class KnowledgeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.knowledge'
```

**apps/conversations/apps.py:**
```python
from django.apps import AppConfig

class ConversationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.conversations'
```

**apps/channels/apps.py:**
```python
from django.apps import AppConfig

class ChannelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.channels'
```

### 7.7 pgvector Migration
Create `apps/knowledge/migrations/0001_enable_pgvector.py`:
```python
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = []
    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;"
        ),
    ]
```

---

## 8. API Endpoints

### 8.1 URL Structure
```
/api/
├── knowledge/
│   ├── POST   /documents/upload/    # Upload PDF or text
│   ├── GET    /documents/           # List all documents
│   ├── GET    /documents/{id}/      # Get document details
│   └── DELETE /documents/{id}/      # Delete document
│
├── chat/
│   ├── POST   /message/             # Website chat endpoint
│   ├── GET    /conversations/       # List conversations
│   └── GET    /conversations/{id}/messages/  # Get messages
│
└── webhooks/
    ├── POST   /whatsapp/            # Twilio WhatsApp webhook
    └── POST   /email/               # Postmark inbound webhook
```

### 8.2 config/urls.py
```python
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from ninja import NinjaAPI

from apps.knowledge.api import router as knowledge_router
from apps.conversations.api import router as chat_router
from apps.channels.webhooks import router as webhooks_router

api = NinjaAPI(title="AI Support Agent API", version="1.0.0")

api.add_router("/knowledge/", knowledge_router, tags=["Knowledge Base"])
api.add_router("/chat/", chat_router, tags=["Chat"])
api.add_router("/webhooks/", webhooks_router, tags=["Webhooks"])

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 8.3 apps/knowledge/api.py
```python
from ninja import Router, File, UploadedFile, Schema
from ninja.security import HttpBearer
from django.shortcuts import get_object_or_404
from typing import List
from .models import Document
from .tasks import process_document_task
from apps.companies.models import Company
import uuid

router = Router()


class ApiKeyAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            company = Company.objects.get(api_key=token)
            return company
        except Company.DoesNotExist:
            return None


class DocumentOut(Schema):
    id: uuid.UUID
    title: str
    source_type: str
    status: str
    chunk_count: int
    created_at: str


class UploadResponse(Schema):
    id: uuid.UUID
    message: str


class ErrorResponse(Schema):
    error: str


@router.post("/documents/upload/", response={200: UploadResponse, 400: ErrorResponse}, auth=ApiKeyAuth())
def upload_document(request, title: str, file: UploadedFile = File(None), content: str = None):
    """Upload a PDF file or paste text content."""
    company = request.auth
    
    if not file and not content:
        return 400, {"error": "Either file or content must be provided"}
    
    if file:
        if file.content_type == 'application/pdf':
            source_type = Document.SourceType.PDF
        else:
            source_type = Document.SourceType.TEXT
    else:
        source_type = Document.SourceType.PASTE
    
    doc = Document.objects.create(
        company=company,
        title=title,
        source_type=source_type,
        file=file if file else None,
        raw_content=content if content else "",
        status=Document.Status.PENDING
    )
    
    process_document_task.delay(str(doc.id))
    
    return {"id": doc.id, "message": "Document uploaded. Processing started."}


@router.get("/documents/", response=List[DocumentOut], auth=ApiKeyAuth())
def list_documents(request):
    """List all documents for this company."""
    company = request.auth
    docs = Document.objects.filter(company=company).order_by('-created_at')
    return [
        DocumentOut(
            id=d.id,
            title=d.title,
            source_type=d.source_type,
            status=d.status,
            chunk_count=d.chunk_count,
            created_at=d.created_at.isoformat()
        ) for d in docs
    ]


@router.get("/documents/{doc_id}/", response=DocumentOut, auth=ApiKeyAuth())
def get_document(request, doc_id: uuid.UUID):
    """Get details of a specific document."""
    company = request.auth
    doc = get_object_or_404(Document, id=doc_id, company=company)
    return DocumentOut(
        id=doc.id,
        title=doc.title,
        source_type=doc.source_type,
        status=doc.status,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at.isoformat()
    )


@router.delete("/documents/{doc_id}/", auth=ApiKeyAuth())
def delete_document(request, doc_id: uuid.UUID):
    """Delete a document and all its chunks."""
    company = request.auth
    doc = get_object_or_404(Document, id=doc_id, company=company)
    doc.delete()
    return {"message": "Document deleted"}
```

### 8.4 apps/conversations/api.py
```python
from ninja import Router, Schema
from ninja.security import HttpBearer
from django.shortcuts import get_object_or_404
from typing import List, Optional
from .models import Conversation, Message
from .services import generate_response
from apps.companies.models import Company
import uuid

router = Router()


class ApiKeyAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            company = Company.objects.get(api_key=token)
            return company
        except Company.DoesNotExist:
            return None


class ChatRequest(Schema):
    message: str
    session_id: Optional[str] = None


class ChatResponse(Schema):
    conversation_id: uuid.UUID
    session_id: str
    response: str


class MessageOut(Schema):
    role: str
    content: str
    created_at: str


class ConversationOut(Schema):
    id: uuid.UUID
    channel: str
    customer_identifier: str
    status: str
    message_count: int
    created_at: str


@router.post("/message/", response=ChatResponse, auth=ApiKeyAuth())
def send_message(request, data: ChatRequest):
    """Website chat endpoint."""
    company = request.auth
    
    if data.session_id:
        try:
            conversation = Conversation.objects.get(
                id=data.session_id,
                company=company,
                channel=Conversation.Channel.WEB
            )
        except Conversation.DoesNotExist:
            conversation = None
    else:
        conversation = None
    
    if not conversation:
        conversation = Conversation.objects.create(
            company=company,
            channel=Conversation.Channel.WEB,
            customer_identifier=f"web_{uuid.uuid4().hex[:8]}"
        )
    
    Message.objects.create(
        conversation=conversation,
        role=Message.Role.CUSTOMER,
        content=data.message
    )
    
    ai_response = generate_response(company, data.message, conversation)
    
    Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content=ai_response
    )
    
    return ChatResponse(
        conversation_id=conversation.id,
        session_id=str(conversation.id),
        response=ai_response
    )


@router.get("/conversations/", response=List[ConversationOut], auth=ApiKeyAuth())
def list_conversations(request, channel: Optional[str] = None):
    """List all conversations for this company."""
    company = request.auth
    convos = Conversation.objects.filter(company=company)
    
    if channel:
        convos = convos.filter(channel=channel)
    
    return [
        ConversationOut(
            id=c.id,
            channel=c.channel,
            customer_identifier=c.customer_identifier,
            status=c.status,
            message_count=c.messages.count(),
            created_at=c.created_at.isoformat()
        ) for c in convos
    ]


@router.get("/conversations/{convo_id}/messages/", response=List[MessageOut], auth=ApiKeyAuth())
def get_conversation_messages(request, convo_id: uuid.UUID):
    """Get all messages in a conversation."""
    company = request.auth
    conversation = get_object_or_404(Conversation, id=convo_id, company=company)
    
    return [
        MessageOut(
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat()
        ) for m in conversation.messages.all()
    ]
```

### 8.5 apps/channels/webhooks.py
```python
from ninja import Router
from django.http import HttpResponse
from .tasks import process_whatsapp_message_task, process_email_message_task
import json

router = Router()


@router.post("/whatsapp/")
def whatsapp_webhook(request):
    """Receives incoming WhatsApp messages from Twilio."""
    from twilio.twiml.messaging_response import MessagingResponse
    
    from_number = request.POST.get('From', '')
    to_number = request.POST.get('To', '')
    body = request.POST.get('Body', '')
    message_sid = request.POST.get('MessageSid', '')
    
    process_whatsapp_message_task.delay(
        from_number=from_number,
        to_number=to_number,
        body=body,
        message_sid=message_sid
    )
    
    response = MessagingResponse()
    return HttpResponse(str(response), content_type='application/xml')


@router.post("/email/")
def email_webhook(request):
    """Receives incoming emails from Postmark."""
    data = json.loads(request.body)
    
    from_email = data.get('From', '')
    to_email = data.get('To', '')
    subject = data.get('Subject', '')
    body = data.get('TextBody', '') or data.get('HtmlBody', '')
    message_id = data.get('MessageID', '')
    
    process_email_message_task.delay(
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        body=body,
        message_id=message_id
    )
    
    return {"status": "received"}
```

---

## 9. Celery Tasks

### 9.1 apps/knowledge/tasks.py
```python
from celery import shared_task
from django.conf import settings
from .models import Document, DocumentChunk
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from openai import OpenAI
import tempfile
import os


@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    """Process an uploaded document into vector chunks."""
    try:
        doc = Document.objects.get(id=document_id)
        doc.status = Document.Status.PROCESSING
        doc.save()
        
        # Extract text
        if doc.source_type == Document.SourceType.PDF:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                for chunk in doc.file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            
            loader = PyPDFLoader(tmp_path)
            pages = loader.load()
            text = "\n".join([p.page_content for p in pages])
            os.unlink(tmp_path)
        else:
            text = doc.raw_content
        
        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_text(text)
        
        # Generate embeddings
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        for i, chunk_text in enumerate(chunks):
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=chunk_text
            )
            embedding = response.data[0].embedding
            
            DocumentChunk.objects.create(
                document=doc,
                content=chunk_text,
                chunk_index=i,
                embedding=embedding,
                metadata={"source": doc.title, "chunk": i}
            )
        
        doc.status = Document.Status.COMPLETED
        doc.chunk_count = len(chunks)
        doc.save()
        
        return {"status": "success", "chunks": len(chunks)}
        
    except Exception as e:
        doc = Document.objects.get(id=document_id)
        doc.status = Document.Status.FAILED
        doc.error_message = str(e)
        doc.save()
        raise self.retry(exc=e, countdown=60)
```

### 9.2 apps/conversations/services.py
```python
from django.conf import settings
from openai import OpenAI
from pgvector.django import L2Distance
from apps.knowledge.models import DocumentChunk
from apps.companies.models import Company
from .models import Conversation


def generate_response(company: Company, question: str, conversation: Conversation = None) -> str:
    """Core RAG function to generate AI responses."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Generate question embedding
    embedding_response = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=question
    )
    question_embedding = embedding_response.data[0].embedding
    
    # Search for relevant chunks
    relevant_chunks = DocumentChunk.objects.filter(
        document__company=company
    ).order_by(
        L2Distance('embedding', question_embedding)
    )[:5]
    
    # Build context
    if not relevant_chunks:
        context = "No relevant information found in the knowledge base."
    else:
        context = "\n\n---\n\n".join([chunk.content for chunk in relevant_chunks])
    
    # Build prompt
    system_prompt = f"""You are a customer support agent for {company.name}.
{company.ai_personality}

IMPORTANT RULES:
1. ONLY answer based on the provided context below.
2. If the context doesn't contain the answer, say "I don't have information about that. Would you like me to connect you with a human agent?"
3. Be concise and helpful.
4. Never make up information.

CONTEXT FROM KNOWLEDGE BASE:
{context}
"""
    
    # Get response
    response = client.chat.completions.create(
        model=settings.DEFAULT_AI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        max_tokens=settings.MAX_TOKENS,
        temperature=0.3
    )
    
    return response.choices[0].message.content
```

### 9.3 apps/conversations/tasks.py
```python
from celery import shared_task
from .services import generate_response
from .models import Conversation, Message
from apps.companies.models import Company


@shared_task
def generate_ai_response_task(conversation_id: str, question: str):
    """Async task to generate AI response."""
    conversation = Conversation.objects.get(id=conversation_id)
    company = conversation.company
    
    response = generate_response(company, question, conversation)
    
    Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content=response
    )
    
    return {"response": response}
```

### 9.4 apps/channels/tasks.py
```python
from celery import shared_task
from django.conf import settings
from twilio.rest import Client as TwilioClient
from apps.companies.models import Company
from apps.conversations.models import Conversation, Message
from apps.conversations.services import generate_response
import httpx


@shared_task
def process_whatsapp_message_task(from_number: str, to_number: str, body: str, message_sid: str):
    """Process incoming WhatsApp message."""
    company = Company.objects.first()
    if not company:
        return {"error": "No company configured"}
    
    conversation, _ = Conversation.objects.get_or_create(
        company=company,
        channel=Conversation.Channel.WHATSAPP,
        customer_identifier=from_number,
        defaults={"status": Conversation.Status.ACTIVE}
    )
    
    Message.objects.create(
        conversation=conversation,
        role=Message.Role.CUSTOMER,
        content=body
    )
    
    ai_response = generate_response(company, body, conversation)
    
    Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content=ai_response
    )
    
    client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=ai_response,
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        to=from_number
    )
    
    return {"status": "sent", "conversation_id": str(conversation.id)}


@shared_task
def process_email_message_task(from_email: str, to_email: str, subject: str, body: str, message_id: str):
    """Process incoming email."""
    company = Company.objects.first()
    if not company:
        return {"error": "No company configured"}
    
    conversation, _ = Conversation.objects.get_or_create(
        company=company,
        channel=Conversation.Channel.EMAIL,
        customer_identifier=from_email,
        defaults={"status": Conversation.Status.ACTIVE}
    )
    
    Message.objects.create(
        conversation=conversation,
        role=Message.Role.CUSTOMER,
        content=body,
        metadata={"subject": subject}
    )
    
    ai_response = generate_response(company, body, conversation)
    
    Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content=ai_response
    )
    
    httpx.post(
        "https://api.postmarkapp.com/email",
        headers={
            "X-Postmark-Server-Token": settings.POSTMARK_SERVER_TOKEN,
            "Content-Type": "application/json"
        },
        json={
            "From": settings.POSTMARK_FROM_EMAIL,
            "To": from_email,
            "Subject": f"Re: {subject}",
            "TextBody": ai_response
        }
    )
    
    return {"status": "sent", "conversation_id": str(conversation.id)}
```

---

## 10. Integration Guides

### 10.1 Twilio WhatsApp Sandbox

1. Create Twilio account at https://www.twilio.com/try-twilio
2. Go to Console → Messaging → Try it out → WhatsApp
3. Follow the "Send a WhatsApp message" instructions
4. Send the join code from your phone
5. Set webhook URL in Sandbox Settings:
   - For local testing with ngrok: `https://abc123.ngrok.io/api/webhooks/whatsapp/`

**ngrok Setup:**
```bash
# Download from https://ngrok.com/download
ngrok http 8000
# Use the https URL in Twilio webhook settings
```

### 10.2 Postmark Email

1. Create Postmark account at https://postmarkapp.com
2. Create a Server
3. Go to Settings → Inbound
4. Set webhook URL: `https://your-domain.com/api/webhooks/email/`
5. Note the inbound email address

### 10.3 OpenAI API

1. Create account at https://platform.openai.com
2. Add billing ($5 minimum)
3. Create API key in API Keys section
4. Add to `.env` as `OPENAI_API_KEY`

---

## 11. Day-by-Day Implementation

### Day 0: Setup ✅
- ✅ Docker containers (Postgres, Redis)
- ✅ Python virtual environment
- ✅ Install dependencies
- ✅ Verify connections

### Day 1: Django Project
- ✅ Create Django project
- ✅ Create apps (companies, knowledge, conversations, channels)
- ✅ Create all models
- ✅ Create admin files
- ✅ Run migrations
- ✅ Create superuser
- ✅ Test admin panel
- ✅ Create test company

### Day 2: Document Ingestion
- ✅ Create knowledge/tasks.py
- ✅ Setup Celery configuration
- ✅ Test document upload via admin
- ✅ Verify chunks created with embeddings

### Day 3: RAG Logic
- ✅ Create conversations/services.py
- ✅ Test generate_response function
- ✅ Verify context retrieval works

### Day 4: Website Chat API
- ✅ Create knowledge/api.py
- ✅ Create conversations/api.py
- ✅ Setup config/urls.py with NinjaAPI
- ✅ Test API with curl/Postman

### Day 5: Celery Integration
- ✅ Move heavy tasks to Celery
- ✅ Test async processing
- ✅ Add error handling

### Day 6: WhatsApp Integration
- ✅ Setup Twilio Sandbox
- ✅ Create channels/webhooks.py
- ✅ Create channels/tasks.py
- ✅ Test WhatsApp flow

### Day 7: Email Integration
- ✅ Setup Postmark
- ✅ Test email webhook
- ✅ Test email response

### Day 8: Multi-tenancy & Dashboard
- ✅ Verify company isolation
- ✅ Create basic dashboard templates
- ✅ Add upload form

### Day 9: Testing & Polish
- ✅ Test edge cases
- ✅ Verify PDF/DOCX Uploads and Processing
- ✅ Refine prompts
- ✅ Handle errors gracefully

### Day 10: Demo Preparation
- ✅ Record backup demo video
- ✅ Write README
- ✅ Prepare defense talking points

---

## 12. Testing Checklist

| Test | Steps | Expected |
|------|-------|----------|
| PDF Upload | Upload 5-page PDF | Status = completed |
| Web Chat | Send "Hello" | Get AI response |
| Knowledge Query | Ask about doc content | Uses doc info |
| Unknown Query | Ask unrelated question | "I don't have info" |
| WhatsApp | Send from phone | Response on phone |
| Email | Send to inbound | Response in inbox |
| Multi-tenant | Query wrong company | No results |

---

## 13. Defense Preparation

### Demo Script (5 min)
1. **Show Dashboard** (30s)
2. **Upload Document** (1 min)
3. **Website Chat Demo** (1 min)
4. **WhatsApp Demo** (1.5 min)
5. **Email Demo** (1 min)

### Key Talking Points
- RAG architecture (not fine-tuning)
- Celery for async processing
- Multi-tenant data isolation
- Vector similarity search with pgvector
