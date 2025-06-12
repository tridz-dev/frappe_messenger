import frappe

def after_install():
    add_default_platforms()
    frappe.db.commit()

def add_default_platforms():
    platforms = {
        "Messenger":{
            "from_meta":1
        },
        "Instagram":{
            "from_meta":1
        }
    }
    
    apps = frappe.get_single("Installed Applications").installed_applications
    whatsapp_app = [app.app_name for app in apps if app.app_name == "frappe_whatsapp"]
    
    if whatsapp_app:
        platforms["WhatsApp"] = {
            "from_meta": 1
        }

    for platform in platforms:
        if frappe.db.exists("Messenger Platform",platform):
            continue
        doc = frappe.new_doc("Messenger Platform")
        doc.platform = platform
        doc.from_meta = platforms[platform]["from_meta"]
        doc.insert()

    

