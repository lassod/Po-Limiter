# Copyright (c) 2026, Lassod
# License: MIT

import frappe
from frappe.model.document import Document

class UserPOLimit(Document):
	def validate(self):
		"""Validate uniqueness of user-company combination"""
		self.validate_unique_user_company()

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
