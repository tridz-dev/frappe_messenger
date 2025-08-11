import frappe

def create_crm_notification_generic(
    notification_type,
    notification_text,
    recipient,
    reference_doctype,
    reference_name,
    notification_type_doctype,
    notification_type_doc,
    message 
):
    doc_fields = {
        "doctype": "CRM Notification",
        "type": notification_type,
        "notification_text": notification_text,
        "to_user": recipient,
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "notification_type_doctype": notification_type_doctype,
        "notification_type_doc": notification_type_doc,
        "message":message
    }

    frappe.get_doc(doc_fields).insert(ignore_permissions=True)
