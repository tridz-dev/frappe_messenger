# Copyright (c) 2025, Tridz Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MessengerSettings(Document):
	def on_update(self):
		frappe.cache().delete_value("messenger_settings_cache")
