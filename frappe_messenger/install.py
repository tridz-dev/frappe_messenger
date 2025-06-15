import frappe

def after_install():
    add_default_platforms()
    frappe.db.commit()

def add_default_platforms():
    installed_apps = frappe.get_single("Installed Applications").installed_applications
    has_whatsapp = any(app.app_name == "frappe_whatsapp" for app in installed_apps)
    has_crm = any(app.app_name == "crm" for app in installed_apps)
    has_erpnext = any(app.app_name == "erpnext" for app in installed_apps)

    platforms = {
        "Messenger": dict(from_meta=1),
        "Instagram": dict(from_meta=1),
    }
    if has_whatsapp:
        platforms["WhatsApp"] = dict(from_meta=1)

    for name, data in platforms.items():
        if not frappe.db.exists("Messenger Platform", {"platform": name}):
            doc = frappe.new_doc("Messenger Platform")
            doc.platform = name
            doc.from_meta = data["from_meta"]
            doc.insert(ignore_permissions=True)

        if has_crm:
            create_lead_source(name,"CRM Lead Source")
        if has_erpnext:
            create_lead_source(name,"Lead Source")

def create_lead_source(source_name,doctype):
    if not frappe.db.exists(doctype, source_name):
        doc = frappe.get_doc({
            "doctype": doctype,
            "source_name": source_name
        })
        doc.insert(ignore_permissions=True)
