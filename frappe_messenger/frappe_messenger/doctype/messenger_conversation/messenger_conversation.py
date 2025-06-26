# Copyright (c) 2025, Tridz Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MessengerConversation(Document):
	def before_save(self):
		self.log_status_change()

	def log_status_change(self):
		last_status = frappe.db.get_value("Messenger Conversation", self.name, "status")
		new_status = self.status

		if last_status == new_status:
			return  

		now = frappe.utils.now_datetime()

		
		log_entry = {
			"status": new_status,
			"changed_by": frappe.session.user,
			"changed_on": now
		}

		if new_status == "Resolved":
			open_logs = frappe.db.get_all(
				"Messenger Conversation Status Log",
				filters={
					"parent": self.name,
					"parenttype": "Messenger Conversation",
					"status": "Open"
				},
				fields=["name", "changed_on"],
				order_by="changed_on desc",
				limit_page_length=1
			)
			print("open_logs",open_logs)
			if open_logs:
				open_time = frappe.utils.get_datetime(open_logs[0].changed_on)
				print("Open Time",open_time)
				print("NOw",now)
				resolution_time = (now - open_time).total_seconds()
				print("Resolution TIme",resolution_time)
				log_entry["resolution_time"] = resolution_time

		self.append("status_log", log_entry)

	