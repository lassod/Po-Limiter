# Copyright (c) 2026, Lassod
# License: MIT

import frappe
from frappe.utils import get_first_day, get_last_day, today

def execute():
	"""
	Calculate and set monthly_usage for all User PO Limit records.
	This should be run after the initial installation to set baseline usage.
	"""
	print("Calculating monthly PO usage for all users...")

	# Get all User PO Limit records
	limits = frappe.get_all("User PO Limit",
		fields=["name", "user", "company"]
	)

	today_date = today()
	first_day = get_first_day(today_date)
	last_day = get_last_day(today_date)

	count = 0
	for limit in limits:
		# Calculate total PO amount for current month
		total = frappe.db.sql("""
			SELECT SUM(base_grand_total)
			FROM `tabPurchase Order`
			WHERE owner = %s
			AND company = %s
			AND docstatus = 1
			AND transaction_date BETWEEN %s AND %s
		""", (limit.user, limit.company, first_day, last_day))[0][0] or 0

		# Update the monthly_usage field
		if total > 0:
			frappe.db.set_value("User PO Limit", limit.name, {
				"monthly_usage": total,
				"last_reset_date": today_date
			})
			count += 1

	print(f"Updated monthly usage for {count} users")
