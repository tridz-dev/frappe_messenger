# Copyright (c) 2025, Tridz Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MessengerConversation(Document):
	def before_save(self):
		self.log_status_change()

	def log_status_change(self):
		last_status = frappe.db.get_value("Messenger Conversation",self.name,"status")
		print("LAST STatus",last_status)
		new_status = self.status

		print("New status",new_status)
		print("frappe.session.user",frappe.session.user)

		if last_status != new_status:
			self.append("status_log", {
				"status": new_status,
				"changed_by": frappe.session.user,
				"changed_on": frappe.utils.now_datetime()
			})

	