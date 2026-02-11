# Copyright (c) 2026, Lassod
# License: MIT

import frappe
from frappe import _

def get_context(context):
	"""Get context for the PO Limiter page"""
	# Ensure only MD can access this page
	if not has_md_access():
		frappe.throw(_("You don't have permission to access this page."), frappe.PermissionError)

	context.no_cache = 1
	context.title = _("PO Limiter Tool")

	# Get all companies
	context.companies = frappe.get_all("Company", filters={"enabled": 1}, fields=["name", "abbr"])

	# Get users with PO access
	context.users = get_purchase_users()

	# Get all user limits
	context.user_limits = get_all_user_limits()

	# Get pending requests
	context.pending_requests = get_pending_limit_requests()

	return context


@frappe.whitelist()
def get_purchase_users():
	"""Get all users who have access to create Purchase Orders"""
	# Get users with Purchase Order create permission
	users = frappe.get_all("User", filters={
		"enabled": 1,
		"user_type": "System User"
	}, fields=["name", "full_name", "email"])

	purchase_users = []
	for user in users:
		if has_po_create_permission(user.name):
			purchase_users.append(user)

	return purchase_users


@frappe.whitelist()
def has_po_create_permission(user=None):
	"""Check if user has permission to create Purchase Orders"""
	if not user:
		user = frappe.session.user

	# Check if user has "Purchase Order Creator" or "Purchase Order Manager" role
	# or has create permission on Purchase Order
	has_role = frappe.db.exists("Has Role", {
		"parent": user,
		"role": ["in", ["Purchase Order Creator", "Purchase Order Manager", "System Manager", "Managing Director"]]
	})

	return has_role


@frappe.whitelist()
def get_all_user_limits():
	"""Get all user PO limits"""
	limits = frappe.get_all("User PO Limit",
		fields=["name", "user", "company", "status", "per_po_limit", "per_month_limit",
				"monthly_usage", "last_reset_date", "last_updated_by", "last_updated_date"],
		order_by="user, company"
	)
	return limits


@frappe.whitelist()
def get_pending_limit_requests():
	"""Get all pending PO limit increase requests"""
	requests = frappe.get_all("PO Limit Increase Request",
		filters={"status": "Pending Approval"},
		fields=["name", "user", "company", "requested_per_po_limit", "requested_per_month_limit",
				"reason", "creation"]
	)
	return requests


@frappe.whitelist()
def update_user_limit(user, company, per_po_limit, per_month_limit, status):
	"""Update or create user PO limit"""
	if not has_md_access():
		frappe.throw(_("You don't have permission to perform this action."), frappe.PermissionError)

	# Check if limit exists
	exists = frappe.db.exists("User PO Limit", {"user": user, "company": company})

	if exists:
		# Update existing limit
		frappe.db.set_value("User PO Limit", exists, {
			"per_po_limit": per_po_limit,
			"per_month_limit": per_month_limit,
			"status": status,
			"last_updated_by": frappe.session.user,
			"last_updated_date": frappe.utils.now()
		})
	else:
		# Create new limit
		frappe.get_doc({
			"doctype": "User PO Limit",
			"user": user,
			"company": company,
			"per_po_limit": per_po_limit,
			"per_month_limit": per_month_limit,
			"status": status,
			"monthly_usage": 0,
			"last_reset_date": frappe.utils.today()
		}).insert()

	frappe.msgprint(_("PO Limit updated for {0}").format(user))
	return {"success": True}


@frappe.whitelist()
def get_user_limit_details(user, company):
	"""Get user limit details for editing"""
	if not has_md_access():
		frappe.throw(_("You don't have permission to access this information."), frappe.PermissionError)

	limit = frappe.db.get_value("User PO Limit",
		{"user": user, "company": company},
		["name", "per_po_limit", "per_month_limit", "status", "monthly_usage",
		 "last_reset_date", "last_updated_by", "last_updated_date"],
		as_dict=1
	)

	return limit


def has_md_access():
	"""Check if current user has MD access"""
	# Check for Managing Director role
	has_md_role = frappe.db.exists("Has Role", {
		"parent": frappe.session.user,
		"role": "Managing Director"
	})

	# Also allow System Manager
	has_sm_role = frappe.db.exists("Has Role", {
		"parent": frappe.session.user,
		"role": "System Manager"
	})

	return has_md_role or has_sm_role
