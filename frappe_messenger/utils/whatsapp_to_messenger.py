import frappe
from frappe_messenger.utils.webhook import get_or_create_conversation

def get_whatsapp_message(doc, event):
    try:
        if not doc.message_id:
            frappe.log_error(
                title="get_whatsapp_message Error",
                message=f"Missing message_id in WhatsApp Message: {doc.name}"
            )
            return
        
        existing_msg = frappe.db.exists("Messenger Message", {"message_id": doc.message_id})    
        if existing_msg:
            update_messenger_message(existing_msg, doc)
        else:
            create_messenger_message(doc)

    except Exception as e:
        frappe.log_error(title="get_whatsapp_message Error", message=frappe.get_traceback())


def create_messenger_message(doc):
    try:
        if doc.custom_message_from_messenger:
            frappe.log_error(
                title="create_messenger_message Skipped",
                message=f"Message {doc.name} skipped: already created from Messenger."
            )
            return
        
        platform_exist = frappe.db.exists("Messenger Platform", {"platform": "WhatsApp"})
        if not platform_exist:
            frappe.log_error(
                title="Missing WhatsApp Platform",
                message="Messenger Platform 'WhatsApp' not found. Ensure the platform is created in the system."
            )
            return
        
        mobile_no = getattr(doc, "from") if doc.type == "Incoming" else getattr(doc, "to")
        if not mobile_no:
            frappe.log_error(
                title="create_messenger_message Error",
                message=f"Missing mobile number in WhatsApp Message: {doc.name}"
            )
            return

        user = get_or_create_whatsapp_user(mobile_no, doc.profile_name, "WhatsApp")
        conversation = get_or_create_conversation(mobile_no, "WhatsApp")
        message = doc.message

        frappe.db.set_value("Messenger Conversation", conversation, {
            "last_message": message,
            "last_message_time": doc.creation
        })

        content_type = "file" if doc.content_type == "document" else doc.content_type
        msg = frappe.new_doc("Messenger Message")
        msg.update({
            "message_id": doc.message_id,
            "message": message,
            "message_direction": doc.type,
            "content_type": content_type,
            "status": doc.status,
            "is_reply": doc.is_reply,
            "is_auto_generated_outgoing_message": 1 if doc.type == "Outgoing" else 0,
            "conversation": conversation,
            "timestamp": doc.creation,
            "attach":doc.attach
        })

        if doc.type == "Incoming":
            msg.sender_user = user
            msg.sender_id = mobile_no
        else:
            msg.recipient_user = user
            msg.recipient_id = mobile_no

        msg.insert(ignore_permissions=True)

    except Exception as e:
        frappe.log_error(title="create_messenger_message Error", message=frappe.get_traceback())


def update_messenger_message(message_name, doc):
    try:
        msg = frappe.get_doc("Messenger Message", message_name)
        msg.status = doc.status
        msg.attach = doc.attach
        msg.save(ignore_permissions=True)

    except Exception as e:
        frappe.log_error(title="update_messenger_message Error", message=frappe.get_traceback())



def get_or_create_whatsapp_user(mobile_no, username=None, platform="WhatsApp"):
    try:
        user = frappe.db.exists("Messenger User", {"user_id": mobile_no})
        if user:
            return user

        new_user = frappe.new_doc("Messenger User")
        new_user.update({
            "user_id": mobile_no,
            "username": username,
            "platform": platform
        })
        new_user.insert(ignore_permissions=True)
        return new_user.name
    
    except Exception as e:
        frappe.log_error(title="get_or_create_whatsapp_user Error", message=frappe.get_traceback())
        return None
