from consultation_center.setup.services import ensure_default_services
from consultation_center.website import migrate_homepage_copy_to_primary_audience


def execute():
	migrate_homepage_copy_to_primary_audience()
	ensure_default_services()
