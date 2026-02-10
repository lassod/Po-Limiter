# Copyright (c) 2026, Lassod
# License: MIT

import frappe

def execute():
	"""
	Create default zero PO limits for all existing users.
	Run this patch after installing the app.
	"""
	print("Creating PO limits for existing users...")

	# Get all active users
	users = frappe.get_all("User",
		filters={"enabled": 1},
		fields=["name"],
		pluck="name"
	)

	# Get all companies
	companies = frappe.get_all("Company",
		fields=["name"],
		pluck="name"
	)

	if not companies:
		print("No companies found. Skipping patch.")
		return

	count = 0
	for user in users:
		for company in companies:
			# Check if limit already exists
			exists = frappe.db.exists("User PO Limit", {
				"user": user,
				"company": company
			})

			if not exists:
				try:
					frappe.get_doc({
						"doctype": "User PO Limit",
						"user": user,
						"company": company,
						"per_po_limit": 0,
						"per_month_limit": 0,
						"monthly_usage": 0,
						"last_reset_date": frappe.utils.today()
					}).insert(ignore_permissions=True)
					count += 1
				except Exception as e:
					print(f"Error creating limit for user {user}, company {company}: {str(e)}")

	print(f"Created {count} PO limit records for existing users")
