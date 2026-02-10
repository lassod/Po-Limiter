# Copyright (c) 2026, Lassod
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, nowdate

class POLimitIncreaseRequest(Document):
	def validate(self):
		"""Validate the request before saving"""
		self.set_current_limits()
		self.validate_requested_limits()
		self.validate_status()

	def set_current_limits(self):
		"""Fetch and display current limits for the user"""
		if not self.user or not self.company:
			return

		# Get current limits
		limits = frappe.db.get_value("User PO Limit",
			{"user": self.user, "company": self.company},
			["per_po_limit", "per_month_limit"]
		)

		if limits:
			self.current_per_po_limit = limits[0] or 0
			self.current_per_month_limit = limits[1] or 0
		else:
			self.current_per_po_limit = 0
			self.current_per_month_limit = 0

	def validate_requested_limits(self):
		"""Ensure requested limits are greater than current"""
		if self.status == "Draft":
			if (self.requested_per_po_limit <= self.current_per_po_limit and
				self.requested_per_month_limit <= self.current_per_month_limit):
				frappe.throw(
					_("Requested limits must be greater than current limits. "
					  "Please request an increase.")
				)

	def validate_status(self):
		"""Validate status transitions"""
		if self.status == "Approved":
			if not self.approved_by:
				self.approved_by = frappe.session.user
			if not self.approval_date:
				self.approval_date = now()

	def on_submit(self):
		"""Handle submission - send for approval"""
		if self.status == "Draft":
			self.status = "Pending Approval"
			frappe.db.set_value("PO Limit Increase Request", self.name, "status", "Pending Approval")
			frappe.msgprint(_("Request submitted for approval"))

	def on_cancel(self):
		"""Handle cancellation"""
		if self.status == "Approved":
			frappe.throw(_("Cannot cancel an approved request. Please create a new request to revert."))

	def approve_request(self):
		"""Approve the request and update User PO Limit"""
		if self.status != "Pending Approval":
			frappe.throw(_("Only Pending Approval requests can be approved"))

		# Update status
		self.status = "Approved"
		self.approved_by = frappe.session.user
		self.approval_date = now()
		self.save()

		# Update or create User PO Limit
		self.update_user_po_limit()

		frappe.msgprint(_("Request approved successfully. PO limits updated for {0}").format(self.user))

	def reject_request(self, rejection_reason=""):
		"""Reject the request"""
		if self.status != "Pending Approval":
			frappe.throw(_("Only Pending Approval requests can be rejected"))

		self.status = "Rejected"
		self.rejection_reason = rejection_reason
		self.save()

		frappe.msgprint(_("Request rejected"))

	def update_user_po_limit(self):
		"""Update or create User PO Limit record"""
		# Check if limit record exists
		exists = frappe.db.exists("User PO Limit", {
			"user": self.user,
			"company": self.company
		})

		if exists:
			# Update existing record
			frappe.db.set_value("User PO Limit", exists, {
				"per_po_limit": self.requested_per_po_limit,
				"per_month_limit": self.requested_per_month_limit
			})
		else:
			# Create new record
			frappe.get_doc({
				"doctype": "User PO Limit",
				"user": self.user,
				"company": self.company,
				"per_po_limit": self.requested_per_po_limit,
				"per_month_limit": self.requested_per_month_limit,
				"monthly_usage": 0,
				"last_reset_date": frappe.utils.today()
			}).insert()


# Whitelist methods for use from client
@frappe.whitelist()
def approve_request(request_name):
	"""Approve a PO Limit Increase Request"""
	doc = frappe.get_doc("PO Limit Increase Request", request_name)
	doc.approve_request()


@frappe.whitelist()
def reject_request(request_name, rejection_reason=""):
	"""Reject a PO Limit Increase Request"""
	doc = frappe.get_doc("PO Limit Increase Request", request_name)
	doc.reject_request(rejection_reason)
