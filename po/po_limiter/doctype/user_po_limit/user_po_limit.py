# Copyright (c) 2026, Lassod
# License: MIT

import frappe
from frappe.model.document import Document
from frappe.utils import now

class UserPOLimit(Document):
	def validate(self):
		"""Validate uniqueness of user-company combination"""
		self.validate_unique_user_company()
		# Set audit fields
		self.set_audit_fields()

	def validate_unique_user_company(self):
		"""Ensure only one limit record exists per user per company"""
		if not self.user or not self.company:
			return

		exists = frappe.db.exists("User PO Limit", {
			"user": self.user,
			"company": self.company,
			"name": ["!=", self.name] if self.name else ["!=", ""]
		})

		if exists:
			frappe.throw(
				f"PO Limit already exists for User {self.user} in Company {self.company}"
			)

	def set_audit_fields(self):
		"""Set Last Updated By and Last Updated Date fields"""
		# Only update on existing records (not on insert)
		if not self.is_new():
			self.last_updated_by = frappe.session.user
			self.last_updated_date = now()

	def before_save(self):
		"""Before saving the document"""
		# If status is Revoked, ensure limits are set to 0
		if self.status == "Revoked":
			self.per_po_limit = 0
			self.per_month_limit = 0

	def on_update(self):
		"""After updating the document"""
		# Reset monthly usage if needed
		self.reset_monthly_usage_if_needed()

	def reset_monthly_usage_if_needed(self):
		"""Reset monthly usage if we're in a new month"""
		from frappe.utils import getdate, today

		today_date = getdate(today())

		if self.last_reset_date:
			last_reset = getdate(self.last_reset_date)
			# Reset if month or year changed
			if (today_date.month != last_reset.month or
				today_date.year != last_reset.year):
				self.monthly_usage = 0
				self.last_reset_date = today_date
				frappe.db.set_value("User PO Limit", self.name, {
					"monthly_usage": 0,
					"last_reset_date": today_date
				})
		else:
			# First time setting
			self.last_reset_date = today_date
			frappe.db.set_value("User PO Limit", self.name, "last_reset_date", today_date)

