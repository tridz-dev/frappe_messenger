# Copyright (c) 2025, Tridz Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.desk.form import assign_to  


class MessengerConversation(Document):
	def before_save(self):
		self.log_status_change()
	def after_insert(self):
		auto_assign(self)

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


def raven_installed():
    return any("raven" in app.lower() for app in frappe.get_installed_apps())

def get_available_users():
    if not raven_installed():
        frappe.logger().warning("Raven not installed – skipping auto-assign")
        return []
    settings = frappe.get_single("Messenger Settings")
    selected = [u.user for u in (settings.assignable_agents or "") if u.user]
    # print("selected",selected)
    if selected:
        rows = frappe.get_all(
             "Raven User",
             filters={
                  "user":["in",selected],
                  "enabled":1,
                  "availability_status":"Available"
			 },
            fields =["user"]
		)
    else:
          rows = frappe.get_all(
			"Raven User",
			filters={
				"enabled": 1,
				"availability_status": "Available"
			},
			fields=["user"]
		)
    return [r.user for r in rows]


def pick_next_user(pool):
    if not pool:
        return None

    settings = frappe.get_single("Messenger Settings")  
    if settings.last_user in pool:
        idx = (pool.index(settings.last_user) + 1) % len(pool)
    else:
        idx = 0

    settings.last_user = pool[idx]
    settings.save(ignore_permissions=True)
    return pool[idx]


def auto_assign(self):
    current_user = frappe.session.user
    try:
        frappe.set_user("Administrator")
        settings = frappe.get_single("Messenger Settings")

        if not settings.enable_auto_assign:
            frappe.logger("Auto-assign disabled",f"Auto-assign disabled – {self.name} left unassigned")
            return

        pool = get_available_users()
        user = pick_next_user(pool)

        if not user:
            frappe.log_error(
                "Messenger Auto-Assign-No AVAILABLE Raven agent",
                f"No AVAILABLE Raven agent – conversation {self.name} left unassigned."
            )
            return

        assign_to.add({
            "doctype": "Messenger Conversation",
            "name": self.name,
            "assign_to": [user],          # list!
            "description": "Auto-assigned (round-robin)",
            "notify": 1
        })

    except Exception:
        frappe.log_error( "Messenger Auto-Assign",frappe.get_traceback())
    finally:
        frappe.set_user(current_user)