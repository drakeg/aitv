from pathlib import Path

from django.test import SimpleTestCase


class ProductionDeploymentContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[1]
        cls.compose = (root / 'compose.production.yml').read_text()
        cls.startup = (root / 'scripts' / 'start-production.sh').read_text()
        cls.caddyfile = (root / 'Caddyfile').read_text()
        cls.prod_env = (root / '.env.production.example').read_text()
        cls.settings = (root / 'streamhub' / 'settings.py').read_text()
        cls.requirements = (root / 'requirements.txt').read_text()


    def test_production_runtime_uses_pinned_server_and_static_dependencies(self):
        self.assertIn('gunicorn==27.0.1', self.requirements)
        self.assertIn('whitenoise==6.12.0', self.requirements)
        self.assertIn('whitenoise.middleware.WhiteNoiseMiddleware', self.settings)
        self.assertIn('CompressedManifestStaticFilesStorage', self.settings)
        self.assertIn("STATIC_ROOT = BASE_DIR / 'staticfiles'", self.settings)


    def test_production_startup_validates_configuration_and_prepares_application(self):
        self.assertIn('DJANGO_SECRET_KEY must be set to a non-development secret', self.startup)
        self.assertIn('DJANGO_ALLOWED_HOSTS must be configured for production', self.startup)
        self.assertIn('python manage.py migrate --noinput', self.startup)
        self.assertIn('python manage.py collectstatic --noinput', self.startup)
        self.assertIn('exec gunicorn streamhub.wsgi:application', self.startup)
        self.assertIn('workers="${GUNICORN_WORKERS:-1}"', self.startup)


    def test_production_compose_does_not_bind_mount_source_tree(self):
        self.assertNotIn('- .:/app', self.compose)
        self.assertIn('- aitv_data:/data', self.compose)
        self.assertIn('command: ["/app/scripts/start-production.sh"]', self.compose)
        self.assertIn('DJANGO_DEBUG: "false"', self.compose)
        self.assertIn('DJANGO_SECURE_SSL_REDIRECT: "true"', self.compose)


    def test_production_proxy_is_version_pinned_and_only_web_is_upstream(self):
        self.assertIn('image: caddy:2.11.9-alpine', self.compose)
        self.assertIn('reverse_proxy web:8000', self.caddyfile)
        self.assertIn('{$PUBLIC_HOST}', self.caddyfile)
        self.assertIn('caddy_data:/data', self.compose)
        self.assertIn('caddy_config:/config', self.compose)


    def test_production_environment_documents_required_host_and_security_inputs(self):
        self.assertIn('PUBLIC_HOST=aitv.example.com', self.prod_env)
        self.assertIn('DJANGO_SECRET_KEY=replace-with-a-long-random-secret', self.prod_env)
        self.assertIn('DJANGO_ALLOWED_HOSTS=aitv.example.com', self.prod_env)
        self.assertIn('DJANGO_CSRF_TRUSTED_ORIGINS=https://aitv.example.com', self.prod_env)
        self.assertIn('GUNICORN_WORKERS=1', self.prod_env)


    def test_proxy_trust_is_opt_in_in_django_settings(self):
        self.assertIn("env_bool('DJANGO_TRUST_PROXY_HEADERS', False)", self.settings)
        self.assertIn("SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')", self.settings)
        self.assertIn("CSRF_TRUSTED_ORIGINS = [", self.settings)
