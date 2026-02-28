# Ai_support_agent

![License](https://img.shields.io/github/license/Benjaminofili/ai_support_agent)
![Stars](https://img.shields.io/github/stars/Benjaminofili/ai_support_agent?style=social)
![Issues](https://img.shields.io/github/issues/Benjaminofili/ai_support_agent)

This project is a Django-based AI support agent that utilizes various APIs for AI model integration, messaging, and email services. It is built with dependencies such as OpenAI, Twilio, and Resend, and includes features like Docker and testing.

## Quick Start
```bash
pip install -r requirements.txt && python manage.py runserver
```

## ✨ Highlights
- Utilizes OpenAI API for AI model integration
- Integrates Twilio for WhatsApp messaging
- Uses Resend for email services
- Includes Docker support for easy deployment

## ✨ Features

Based on the actual dependencies and code, the following features are available in Ai_support_agent:
- **Django Integration** - Utilizes the Django framework for building the application
- **Database Support** - Uses PostgreSQL as the database management system
- **Redis Caching** - Employs Redis for caching and improving performance
- **OpenAI API Integration** - Leverages the OpenAI API for AI-related functionality
- **Groq API Integration** - Integrates with the Groq API for additional AI capabilities
- **Twilio WhatsApp Support** - Enables WhatsApp messaging through Twilio
- **Email Sending** - Supports sending emails via SMTP with Resend and Gmail
- **Automated Testing** - Includes tests for ensuring application reliability
- **Docker Containerization** - Allows for containerization using Docker

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Framework | Django |
| Language | Python |
| Database | PostgreSQL |
| Cache | Redis |
| AI/ML | OpenAI, Groq |
| Messaging | Twilio (WhatsApp) |
| Email | SMTP (Gmail) |

## 🚀 Installation

The Ai_support_agent project is built using Django and Python. To get started, follow these steps:

### Prerequisites
- Python
- pip

### Steps

1. **Clone the repository**
```bash
git clone https://github.com/Benjaminofili/ai_support_agent
cd ai_support_agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment**
```bash
cp .env.example .env
```
Update the `.env` file with your actual secret keys and configuration settings.

4. **Run migrations and start development**
```bash
python manage.py migrate
python manage.py runserver
```
Note: Since this project uses Django, you'll need to run the development server using `python manage.py runserver`. Also, make sure to install the required dependencies using `pip` instead of `pnpm` as `pnpm` is used for Node.js projects.

## ⚙️ Environment Variables

Create a `.env` file based on `.env.example`:

```makefile
DEBUG=True
SECRET_KEY=your-secret-key-generate-a-real-one
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://postgres:postgres@db:5432/support_agent
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=sk-your-openai-api-key
GROQ_API_KEY=gsk_your-groq-api-key
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_EMAIL=onboarding@resend.dev
EMAIL_BACKEND=smtp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
EMAIL_HOST_USER=onboarding@resend.dev
EMAIL_HOST_PASSWORD=xxx xxxx xxxx xxxx
DEFAULT_FROM_EMAIL=onboarding@resend.dev
DEFAULT_AI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
MAX_TOKENS=1000
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

| Variable | Description | Required |
|----------|-------------|----------|
| DEBUG | Enables debug mode for Django | Yes |
| SECRET_KEY | Secret key for Django | Yes |
| ALLOWED_HOSTS | List of allowed hosts for Django | Yes |
| DATABASE_URL | URL for PostgreSQL database | Yes |
| REDIS_URL | URL for Redis | Yes |
| OPENAI_API_KEY | API key for OpenAI | Yes |
| GROQ_API_KEY | API key for Groq | Yes |
| TWILIO_ACCOUNT_SID | Account SID for Twilio | Yes |
| TWILIO_AUTH_TOKEN | Auth token for Twilio | Yes |
| TWILIO_WHATSAPP_NUMBER | WhatsApp number for Twilio | Yes |
| RESEND_API_KEY | API key for Resend | Yes |
| RESEND_FROM_EMAIL | From email for Resend | Yes |
| EMAIL_BACKEND | Email backend | Yes |
| EMAIL_HOST | Email host | Yes |
| EMAIL_PORT | Email port | Yes |
| EMAIL_USE_TLS | Use TLS for email | Yes |
| EMAIL_USE_SSL | Use SSL for email | Yes |
| EMAIL_HOST_USER | Email host user | Yes |
| EMAIL_HOST_PASSWORD | Email host password | Yes |
| DEFAULT_FROM_EMAIL | Default from email | Yes |
| DEFAULT_AI_MODEL | Default AI model | Yes |
| EMBEDDING_MODEL | Embedding model | Yes |
| MAX_TOKENS | Maximum tokens | Yes |
| CHUNK_SIZE | Chunk size | Yes |
| CHUNK_OVERLAP | Chunk overlap | Yes |

## 📚 API Reference
Unfortunately, the provided project data does not include explicit API route definitions. However, based on the dependencies and environment variables, we can infer that the API may include endpoints for:

* Interacting with the OpenAI API using the `OPENAI_API_KEY`
* Integrating with Twilio for WhatsApp messaging using the `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`
* Sending emails using the `RESEND_API_KEY` and `EMAIL_BACKEND` settings
* Utilizing Redis for caching or messaging using the `REDIS_URL`

To determine the actual API routes, please refer to the project's codebase and Django application configuration. The API documentation will depend on the specific views, models, and serializers defined in the project.

### Docker Setup
To set up the Ai_support_agent project using Docker, follow these steps:

#### Building the Image
To build the Docker image, navigate to the project directory and run the following command:
```bash
docker build -t ai_support_agent .
```
This command will create a Docker image with the name `ai_support_agent`.

#### Running the Container
To run the Docker container, use the following command:
```bash
docker run -p 8000:8000 ai_support_agent
```
This will start a new container from the `ai_support_agent` image and map port 8000 on the host machine to port 8000 in the container.

#### Docker Compose
To use Docker Compose, navigate to the project directory and run the following command:
```bash
docker-compose up
```
This will start the containers defined in the `docker-compose.yml` file.

#### Volume Mappings and Ports
By default, the `docker-compose.yml` file maps the following volumes and ports:
* Port 8000 on the host machine to port 8000 in the container
* The project directory to the container's working directory

Note: You can customize the volume mappings and ports by modifying the `docker-compose.yml` file.

## 🧪 Testing
To ensure the reliability and stability of the Ai_support_agent application, a test suite has been implemented. 

* The presence of tests is indicated by the `✓ Tests` detected feature.
* However, since the project uses `pip` as the package manager, the command to run tests is likely different from `pnpm test`, which is typically used with npm or yarn.
* To run tests for this Django application, you would typically use a command such as `python manage.py test`. 

Example:
```bash
python manage.py test
```

## 🤝 Contributing

To contribute to the Ai_support_agent project, follow these steps:

1. **Fork the repository**: Create a copy of the repository in your own GitHub account.
2. **Create a feature branch**: Use `git checkout -b feature/your-feature` to create a new branch for your changes.
3. **Commit changes**: Use `git commit -m 'Add feature'` to commit your changes with a meaningful message.
4. **Push changes**: Use `git push origin feature/your-feature` to push your changes to your fork.
5. **Open a Pull Request**: Submit a pull request to the main repository, describing the changes you've made.

Remember to test your changes using the existing test suite, as indicated by the presence of tests in the project. Additionally, ensure your changes are compatible with the project's Docker configuration.

## 📄 License

The Ai_support_agent project is licensed under the MIT License. This means that you are free to use, modify, and distribute the software as long as you include the original copyright and license notice in your distribution. 

For more information, please refer to the [LICENSE](LICENSE) file in the repository.
