# Copyright (c) 2026, Lassod
# License: MIT

import frappe
from frappe import _
from frappe.utils import flt, getdate, today

def validate_po_limits(doc, method=None):
	"""
	Validate Purchase Order against current user's PO limits.
	This is called from Purchase Order validate() and on_submit().

	IMPORTANT: Only validates on SUBMIT, not on save as draft.
	Users can always save POs as draft regardless of limits.

	Args:
		doc: Purchase Order document
		method: Calling method name
	"""
	# Skip validation for cancelled documents
	if doc.docstatus == 2:
		return

	# Only validate on SUBMIT (docstatus == 1), not on save as draft (docstatus == 0)
	# This allows users to save POs as draft without limits
	if doc.docstatus == 0 and method != "on_submit":
		# Document is being saved as draft - allow without validation
		return

	# Only validate when actually submitting (docstatus becomes 1)
	if doc.docstatus != 1 and method != "on_submit":
		return

	# Get the current logged-in user (session user)
	user = frappe.session.user

	# Get company
	company = doc.company

	# Get PO amount
	po_amount = flt(doc.base_grand_total)

	if po_amount <= 0:
		return

	# Get user's PO limits
	user_limit = get_user_po_limit(user, company)

	if not user_limit:
		# No limit set - block submission
		frappe.throw(
			_("PO submission requires MD approval. Please request a PO submission limit."),
			title=_("PO Limit Restriction"),
			exc=frappe.ValidationError
		)

	# Validate Per PO Limit
	validate_per_po_limit(po_amount, user_limit, doc.name)

	# Validate Per Month Limit (only on submit)
	validate_per_month_limit(po_amount, user_limit, user, company, doc.name)

def get_user_po_limit(user, company):
	"""Get user's PO limit for the specified company"""
	limits = frappe.db.get_value("User PO Limit",
		{"user": user, "company": company},
		["per_po_limit", "per_month_limit", "monthly_usage", "last_reset_date", "name", "status"],
		as_dict=1
	)

	return limits

def validate_per_po_limit(po_amount, user_limit, po_name):
	"""Validate Per PO limit"""
	# Check if status is Revoked
	status = user_limit.get("status", "Revoked")

	if status == "Revoked":
		frappe.throw(
			_("PO submission requires MD approval."),
			title=_("PO Limit Restriction"),
			exc=frappe.ValidationError
		)

	per_po_limit = flt(user_limit.get("per_po_limit", 0))

	if per_po_limit <= 0:
		frappe.throw(
			_("PO submission requires MD approval."),
			title=_("PO Limit Restriction"),
			exc=frappe.ValidationError
		)

	if po_amount > per_po_limit:
		frappe.throw(
			_("PO Amount ({0}) exceeds your Per PO Limit ({1}). Excess: {2}. Please reduce the PO amount or request MD approval.").format(
				frappe.format_value(po_amount, dict(fieldtype="Currency")),
				frappe.format_value(per_po_limit, dict(fieldtype="Currency")),
				frappe.format_value(po_amount - per_po_limit, dict(fieldtype="Currency"))
			),
			title=_("PO Limit Restriction"),
			exc=frappe.ValidationError
		)

def validate_per_month_limit(po_amount, user_limit, user, company, po_name):
	"""Validate Per Month limit - only if monthly limit is set (greater than 0)"""
	# Check if status is Revoked
	status = user_limit.get("status", "Revoked")

	if status == "Revoked":
		frappe.throw(
			_("PO submission requires MD approval."),
			title=_("PO Limit Restriction"),
			exc=frappe.ValidationError
		)

	per_month_limit = flt(user_limit.get("per_month_limit", 0))

	# If monthly limit is 0 or not set, skip monthly validation
	# This allows MD to set only Per PO limit without monthly restriction
	if per_month_limit <= 0:
		return

	# Get current month's usage
	monthly_usage = get_monthly_po_usage(user, company)

	# Include current PO in the calculation
	total_with_current = monthly_usage + po_amount

	if total_with_current > per_month_limit:
		frappe.throw(
			_("Monthly PO Amount ({0}) exceeds your Per Month Limit ({1}). Your current monthly usage: {2}. This PO: {3}. Please request MD approval.").format(
				frappe.format_value(total_with_current, dict(fieldtype="Currency")),
				frappe.format_value(per_month_limit, dict(fieldtype="Currency")),
				frappe.format_value(monthly_usage, dict(fieldtype="Currency")),
				frappe.format_value(po_amount, dict(fieldtype="Currency"))
			),
			title=_("PO Limit Restriction"),
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

def update_monthly_usage_on_po_cancel(doc, method=None):
	"""
	Update monthly usage when a PO is cancelled.
	This subtracts the cancelled PO amount from the current user's monthly usage.
	"""
	if doc.docstatus != 2:  # Only on cancel
		return

	# Use the current logged-in user (session user)
	user = frappe.session.user
	company = doc.company
	po_amount = flt(doc.base_grand_total)

	user_limit = get_user_po_limit(user, company)
	if not user_limit:
		return

	current_usage = flt(user_limit.get("monthly_usage", 0))
	new_usage = max(0, current_usage - po_amount)  # Ensure we don't go negative

	update_monthly_usage(user_limit["name"], new_usage)


@frappe.whitelist()
def get_user_po_limit_status(user, company):
	"""
	Get user's PO limit status for client-side validation.
	Returns status and limit information for the current user.
	"""
	limits = get_user_po_limit(user, company)

	if not limits:
		return {
			"status": "Revoked",
			"per_po_limit": 0,
			"per_month_limit": 0
		}

	return {
		"status": limits.get("status", "Revoked"),
		"per_po_limit": limits.get("per_po_limit", 0),
		"per_month_limit": limits.get("per_month_limit", 0)
	}

