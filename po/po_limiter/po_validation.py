# Copyright (c) 2026, Lassod
# License: MIT

import frappe
from frappe import _
from frappe.utils import flt, getdate, today

def validate_po_limits(doc, method=None):
	"""
	Validate Purchase Order against user's PO limits.
	This is called from Purchase Order validate() and on_submit().

	Args:
		doc: Purchase Order document
		method: Calling method name
	"""
	# Skip validation for cancelled documents
	if doc.docstatus == 2:
		return

	# Get the owner (user who created the PO)
	user = doc.owner

	# Get company
	company = doc.company

	# Get PO amount
	po_amount = flt(doc.base_grand_total)

	if po_amount <= 0:
		return

	# Get user's PO limits
	user_limit = get_user_po_limit(user, company)

	if not user_limit:
		# No limit set - allow but warn (or you can throw error)
		# frappe.msgprint(_("No PO limit set for user {0}. Please request a limit.").format(user))
		return

	# Validate Per PO Limit
	validate_per_po_limit(po_amount, user_limit, doc.name)

	# Validate Per Month Limit (only on submit)
	if method == "on_submit" or doc.docstatus == 1:
		validate_per_month_limit(po_amount, user_limit, user, company, doc.name)

def get_user_po_limit(user, company):
	"""Get user's PO limit for the specified company"""
	limits = frappe.db.get_value("User PO Limit",
		{"user": user, "company": company},
		["per_po_limit", "per_month_limit", "monthly_usage", "last_reset_date", "name"],
		as_dict=1
	)

	return limits

def validate_per_po_limit(po_amount, user_limit, po_name):
	"""Validate Per PO limit"""
	per_po_limit = flt(user_limit.get("per_po_limit", 0))

	if per_po_limit <= 0:
		frappe.throw(
			_("<b>PO Limit Exceeded:</b> You have a zero Per PO limit. "
			  "Please submit a <a href='/app/po-limit-increase-request'>PO Limit Increase Request</a> "
			  "to request a limit increase before submitting Purchase Order <b>{0}</b>.").format(po_name),
			title=_("PO Limit Restriction"),
			exc=frappe.ValidationError
		)

	if po_amount > per_po_limit:
		frappe.throw(
			_("<b>Per PO Limit Exceeded:</b> Purchase Order <b>{0}</b> amount ({1}) "
			  "exceeds your Per PO limit of {2}. "
			  "Please submit a <a href='/app/po-limit-increase-request'>PO Limit Increase Request</a> "
			  "to request a limit increase.").format(
				po_name,
				fmt_money(po_amount),
				fmt_money(per_po_limit)
			  ),
			title=_("PO Limit Restriction"),
			exc=frappe.ValidationError
		)

def validate_per_month_limit(po_amount, user_limit, user, company, po_name):
	"""Validate Per Month limit"""
	per_month_limit = flt(user_limit.get("per_month_limit", 0))

	if per_month_limit <= 0:
		frappe.throw(
			_("<b>Monthly PO Limit Exceeded:</b> You have a zero Per Month limit. "
			  "Please submit a <a href='/app/po-limit-increase-request'>PO Limit Increase Request</a> "
			  "to request a limit increase before submitting Purchase Order <b>{0}</b>.").format(po_name),
			title=_("Monthly PO Limit Restriction"),
			exc=frappe.ValidationError
		)

	# Get current month's usage
	monthly_usage = get_monthly_po_usage(user, company)

	# Include current PO in the calculation
	total_with_current = monthly_usage + po_amount

	if total_with_current > per_month_limit:
		frappe.throw(
			_("<b>Monthly PO Limit Exceeded:</b> Submitting Purchase Order <b>{0}</b> ({1}) "
			  "will exceed your monthly limit of {2}. "
			  "Your current monthly usage is {3}. "
			  "Total would be {4}. "
			  "Please submit a <a href='/app/po-limit-increase-request'>PO Limit Increase Request</a> "
			  "to request a limit increase.").format(
				po_name,
				fmt_money(po_amount),
				fmt_money(per_month_limit),
				fmt_money(monthly_usage),
				fmt_money(total_with_current)
			  ),
			title=_("Monthly PO Limit Restriction"),
			exc=frappe.ValidationError
		)

	# Update monthly usage
	update_monthly_usage(user_limit["name"], monthly_usage + po_amount)

def get_monthly_po_usage(user, company):
	"""
	Calculate total PO amount submitted by user in current month.
	Sums up base_grand_total from all submitted POs this month.
	"""
	from frappe.utils import get_first_day, get_last_day, today

	today_date = getdate(today())
	first_day = get_first_day(today_date)
	last_day = get_last_day(today_date)

	# Sum of all submitted POs in current month
	total = frappe.db.sql("""
		SELECT SUM(base_grand_total)
		FROM `tabPurchase Order`
		WHERE owner = %s
		AND company = %s
		AND docstatus = 1
		AND transaction_date BETWEEN %s AND %s
	""", (user, company, first_day, last_day))[0][0] or 0

	return flt(total)

def update_monthly_usage(limit_name, new_usage):
	"""Update the monthly_usage field in User PO Limit"""
	frappe.db.set_value("User PO Limit", limit_name, "monthly_usage", new_usage)

def fmt_money(amount):
	"""Format money for display"""
	return frappe.format_value(amount, dict(fieldtype="Currency"))

def update_monthly_usage_on_po_cancel(doc, method=None):
	"""
	Update monthly usage when a PO is cancelled.
	This subtracts the cancelled PO amount from monthly usage.
	"""
	if doc.docstatus != 2:  # Only on cancel
		return

	user = doc.owner
	company = doc.company
	po_amount = flt(doc.base_grand_total)

	user_limit = get_user_po_limit(user, company)
	if not user_limit:
		return

	current_usage = flt(user_limit.get("monthly_usage", 0))
	new_usage = max(0, current_usage - po_amount)  # Ensure we don't go negative

	update_monthly_usage(user_limit["name"], new_usage)
