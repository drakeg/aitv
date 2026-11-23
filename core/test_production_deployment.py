from pathlib import Path

from django.test import SimpleTestCase


class ProductionDeploymentContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[1]
        cls.compose = (root / 'compose.production.yml').read_text()
        cls.startup = (root / 'scripts' / 'start-production.sh').read_text()
        cls.backup_worker = (root / 'scripts' / 'backup_worker.py').read_text()
        cls.backup_health = (root / 'scripts' / 'backup_health.py').read_text()
        cls.backup_smoke = (root / 'scripts' / 'smoke-backup-profile.sh').read_text()
        cls.ci_workflow = (root / '.github' / 'workflows' / 'ci.yml').read_text()
        cls.caddyfile = (root / 'Caddyfile').read_text()
        cls.prod_env = (root / '.env.production.example').read_text()
        cls.settings = (root / 'streamhub' / 'settings.py').read_text()
        cls.requirements = (root / 'requirements.txt').read_text()


    def test_production_runtime_uses_pinned_server_and_static_dependencies(self):
        self.assertIn('gunicorn==27.0.1', self.requirements)
        self.assertIn('whitenoise==6.12.0', self.requirements)
        self.assertIn('whitenoise.middleware.WhiteNoiseMiddleware', self.settings)
        self.assertIn('django.middleware.clickjacking.XFrameOptionsMiddleware', self.settings)
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
        self.assertIn('command: ["sh", "/app/scripts/start-production.sh"]', self.compose)
        self.assertIn('DJANGO_DEBUG: "false"', self.compose)
        self.assertIn('DJANGO_SECURE_SSL_REDIRECT: "true"', self.compose)
        self.assertIn("headers={'Host':host,'X-Forwarded-Proto':'https'}", self.compose)


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


    def test_production_backup_profile_is_opt_in_and_separate_from_data_volume(self):
        self.assertIn('backups:', self.compose)
        self.assertIn('- backups', self.compose)
        self.assertIn('command: ["python", "-m", "scripts.backup_worker"]', self.compose)
        self.assertIn('- aitv_data:/data:ro', self.compose)
        self.assertIn('${BACKUP_DIR:-./backups}:/backups', self.compose)
        self.assertIn('BACKUP_INTERVAL_SECONDS: "${BACKUP_INTERVAL_SECONDS:-86400}"', self.compose)
        self.assertIn('BACKUP_RETENTION_COUNT: "${BACKUP_RETENTION_COUNT:-7}"', self.compose)
        self.assertIn('test: ["CMD", "python", "-m", "scripts.backup_health"]', self.compose)
        self.assertIn('interval: 15m', self.compose)
        self.assertIn('timeout: 30s', self.compose)
        self.assertIn('retries: 2', self.compose)
        self.assertIn('start_period: 2m', self.compose)
        self.assertIn('BACKUP_DIR=./backups', self.prod_env)
        self.assertIn('BACKUP_INTERVAL_SECONDS=86400', self.prod_env)
        self.assertIn('BACKUP_RETENTION_COUNT=7', self.prod_env)

    def test_backup_worker_uses_verified_backup_helper_and_bounded_retention(self):
        self.assertIn('create_backup(source, destination)', self.backup_worker)
        self.assertIn('BACKUP_PREFIX = "aitv-production"', self.backup_worker)
        self.assertIn('prune_backups(backup_dir, keep)', self.backup_worker)
        self.assertIn('if args.once:', self.backup_worker)


    def test_backup_health_probe_checks_verified_fresh_worker_backup(self):
        self.assertIn('verify_database(backup)', self.backup_health)
        self.assertIn('BACKUP_PREFIX', self.backup_health)
        self.assertIn('BACKUP_MAX_AGE_SECONDS', self.backup_health)
        self.assertIn('DEFAULT_HEALTH_GRACE_SECONDS = 3600', self.backup_health)


    def test_ci_smoke_tests_the_real_production_backup_profile(self):
        self.assertIn('Smoke-test production backup profile', self.ci_workflow)
        self.assertIn('sh scripts/smoke-backup-profile.sh', self.ci_workflow)
        self.assertIn('--profile backups build backups', self.backup_smoke)
        self.assertIn('python -m scripts.backup_worker --once', self.backup_smoke)
        self.assertIn('python -m scripts.backup_health', self.backup_smoke)
        self.assertIn('aitv-production-*.sqlite3', self.backup_smoke)
        self.assertIn('Production backup profile smoke test passed.', self.backup_smoke)
