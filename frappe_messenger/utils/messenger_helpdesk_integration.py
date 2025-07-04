import frappe

def update_messenger_conversation_on_ticket_change(doc, method):
    try:
        if not doc.custom_messenger_conversation:
            frappe.log_error("HD Messenger Sync Error",f"No linked conversation for HD Ticket {doc.name}")
            return
        
        conversation_hd_ticket = frappe.db.get_value("Messenger Conversation Tickets",{"hd_ticket":doc.name,"parent":doc.custom_messenger_conversation,"parenttype":"Messenger Conversation"},"name")
        if conversation_hd_ticket:
            frappe.db.set_value("Messenger Conversation Tickets",conversation_hd_ticket,"status",doc.status)
            latest_ticket = frappe.get_all(
                "Messenger Conversation Tickets",
                filters={"parent": doc.custom_messenger_conversation, "parenttype": "Messenger Conversation"},
                fields=["hd_ticket"],
                order_by="creation_time desc",
                limit=1
            )
            if latest_ticket and str(latest_ticket[0].hd_ticket) == str(doc.name):
                frappe.db.set_value("Messenger Conversation", doc.custom_messenger_conversation,"latest_ticket_status",doc.status)
            

    except Exception as e:
        frappe.log_error(
            title="Messenger HD Ticket Sync Unexpected Error",
            message=frappe.get_traceback()
        )