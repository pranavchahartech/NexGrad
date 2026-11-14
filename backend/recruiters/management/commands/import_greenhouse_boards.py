"""
Management command to discover and import companies, recruiter accounts,
and job/internship listings from Greenhouse Job Board API.
Usage:
  python manage.py import_greenhouse_boards cloudflare github stripe figma
  python manage.py import_greenhouse_boards --default
  python manage.py import_greenhouse_boards --sync-all
"""

from django.core.management.base import BaseCommand
from recruiters.services.greenhouse_importer import GreenhouseJobBoardImporter
from recruiters.models import CompanyBoard


DEFAULT_BOARDS = ['cloudflare', 'github', 'stripe', 'figma', 'datadog']


class Command(BaseCommand):
    help = "Discovers and imports companies, recruiter accounts, and jobs from Greenhouse Job Board API."

    def add_arguments(self, parser):
        parser.add_argument(
            'board_tokens',
            nargs='*',
            help="One or more Greenhouse board tokens (e.g. cloudflare, github, stripe)"
        )
        parser.add_argument(
            '--default',
            action='store_true',
            help="Import verified default set of leading engineering companies (Cloudflare, GitHub, Stripe, Figma, Datadog)"
        )
        parser.add_argument(
            '--sync-all',
            action='store_true',
            help="Re-sync all previously imported company boards in the database"
        )

    def handle(self, *args, **options):
        importer = GreenhouseJobBoardImporter()
        tokens_to_import = []

        if options.get('sync_all'):
            tokens_to_import = list(CompanyBoard.objects.filter(is_active=True).values_list('board_token', flat=True))
            if not tokens_to_import:
                self.stdout.write(self.style.WARNING("No active company boards found in database. Importing defaults..."))
                tokens_to_import = DEFAULT_BOARDS
        elif options.get('default'):
            tokens_to_import = DEFAULT_BOARDS
        elif options.get('board_tokens'):
            tokens_to_import = options['board_tokens']
        else:
            tokens_to_import = DEFAULT_BOARDS

        self.stdout.write(self.style.MIGRATE_HEADING(f"== CareerForge Greenhouse Board Importer =="))
        self.stdout.write(f"Targeting {len(tokens_to_import)} company boards: {', '.join(tokens_to_import)}\n")

        for token in tokens_to_import:
            self.stdout.write(f"Synchronizing board '{token}'...")
            try:
                res = importer.import_board(token)
                company = res['company']
                recruiter_user = res['recruiter_user']
                profile = res['recruiter_profile']

                status_msg = f"  -> Company: {company.name} ({company.slug})"
                recruiter_msg = f"  -> Recruiter Account: {recruiter_user.username} [ID: {profile.internal_identifier}]"
                stats_msg = f"  -> Vacancies: {res['jobs_created']} jobs, {res['internships_created']} internships, {res['jobs_updated']} updated, {res['jobs_deactivated']} deactivated"

                self.stdout.write(self.style.SUCCESS(status_msg))
                self.stdout.write(self.style.SUCCESS(recruiter_msg))
                self.stdout.write(self.style.SUCCESS(stats_msg))
                self.stdout.write("")
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to import board '{token}': {e}"))

        self.stdout.write(self.style.SUCCESS("All requested boards processed successfully."))

