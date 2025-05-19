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

    for platform in platforms:
        if frappe.db.exists("Messenger Platform",platform):
            continue
        doc = frappe.new_doc("Messenger Platform")
        doc.platform = platform
        doc.from_meta = platforms[platform]["from_meta"]
        doc.insert()

    

