# Copyright (c) 2026, Lassod
# License: MIT

import frappe

def jinja_methods():
	"""Custom Jinja methods for templates"""
	return {
		'get_user_po_limit': get_user_po_limit_for_user
	}

def get_user_po_limit_for_user(user, company):
	"""Get user's PO limit - for use in templates/reports"""
	limits = frappe.db.get_value("User PO Limit",
		{"user": user, "company": company},
		["per_po_limit", "per_month_limit", "monthly_usage"],
		as_dict=1
	)
	return limits
