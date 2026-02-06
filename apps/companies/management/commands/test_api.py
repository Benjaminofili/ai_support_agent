"""
Management command to test API configuration.
Usage: python manage.py test_api
"""

import requests
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.companies.models import Company


class Command(BaseCommand):
    help = 'Test API endpoints and configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            default='http://localhost:8000',
            help='Host URL for testing'
        )

    def handle(self, *args, **options):
        host = options['host']
        
        self.stdout.write(self.style.HTTP_INFO('🔍 Testing API Configuration\n'))

        # Get first company
        company = Company.objects.first()
        if not company:
            self.stdout.write(self.style.ERROR('❌ No company found in database'))
            return

        api_key = company.api_key
        
        self.stdout.write(f'Company: {company.name}')
        self.stdout.write(f'API Key: {api_key[:8]}...\n')

        # Test endpoints
        tests = [
            {
                'name': 'Documents List',
                'method': 'GET',
                'url': f'{host}/api/knowledge/documents/',
            },
            {
                'name': 'Conversations List',
                'method': 'GET',
                'url': f'{host}/api/chat/conversations/',
            },
        ]

        for test in tests:
            self.stdout.write(f'\n📡 Testing: {test["name"]}')
            self.stdout.write(f'   URL: {test["url"]}')

            try:
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Accept': 'application/json'
                }

                response = requests.request(
                    method=test['method'],
                    url=test['url'],
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else 'N/A'
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Success (HTTP {response.status_code})'))
                    self.stdout.write(f'   Items: {count}')
                elif response.status_code == 401:
                    self.stdout.write(self.style.ERROR(f'   ❌ Authentication Failed (HTTP {response.status_code})'))
                    self.stdout.write('   Check API key configuration')
                else:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  HTTP {response.status_code}'))
                    try:
                        error = response.json()
                        self.stdout.write(f'   Error: {error}')
                    except:
                        self.stdout.write(f'   Response: {response.text[:100]}')

            except requests.exceptions.ConnectionError:
                self.stdout.write(self.style.ERROR(f'   ❌ Connection Error'))
                self.stdout.write(f'   Make sure server is running at {host}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Error: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('\n✨ Testing complete'))