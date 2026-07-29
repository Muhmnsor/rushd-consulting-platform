from consultation_center.staff import OPERATIONS_ACCESS, build_staff_context, get_referral_directory

no_cache = 1


def get_context(context):
	build_staff_context(context, "operations-referral-directory", "دليل جهات الإحالة", "operations", OPERATIONS_ACCESS)
	context.organizations = get_referral_directory()
