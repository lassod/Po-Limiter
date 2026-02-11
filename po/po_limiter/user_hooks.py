# Copyright (c) 2026, Lassod
# License: MIT

import frappe

def create_default_po_limit(doc, method=None):
	"""
	Create default PO limit (zero) for new users.
	This is called via User after_insert hook.
	"""
	# Get all companies
	companies = frappe.get_all("Company", filters={"enabled": 1}, pluck="name")

	if not companies:
		return

	# Create zero limit records for each company
	for company in companies:
		# Check if already exists (might be created by other means)
		exists = frappe.db.exists("User PO Limit", {
			"user": doc.name,
			"company": company
		})

		if not exists:
			frappe.get_doc({
				"doctype": "User PO Limit",
				"user": doc.name,
				"company": company,
				"status": "Revoked",
				"per_po_limit": 0,
				"per_month_limit": 0,
				"monthly_usage": 0,
				"last_reset_date": frappe.utils.today()
			}).insert(ignore_permissions=True)
