import frappe
import json
import requests
import time
from werkzeug.wrappers import Response
import frappe.utils
from pytz import timezone, UTC
import pytz
from dateutil import parser	
from frappe.utils.file_manager import save_url

@frappe.whitelist(allow_guest=True)
def messenger_webhook():
	if frappe.request.method == "GET":
		return verify_webhook_token()
	return process_incoming_messages()

def verify_webhook_token():
	hub_challenge = frappe.form_dict.get("hub.challenge")
	webhook_verify_token = frappe.db.get_single_value("Messenger Settings", "webhook_verify_token")
	if frappe.form_dict.get("hub.verify_token") != webhook_verify_token:
		frappe.throw("Verify token does not match")
	
	return Response(hub_challenge, status=200)

def process_incoming_messages():
    data = frappe.local.form_dict
    if not data:
        data = json.loads(frappe.request.data)
    print("DATA From WEbhook ", data)
    frappe.get_doc({
		"doctype": "Messenger Notification Log",
		"template": "Webhook",
		"meta_data": json.dumps(data)
	}).insert(ignore_permissions=True)
    # frappe.log_error("DATA From WEbhook ", data)
    entry = data.get("entry",[])
    object = data.get("object")
    platform = "messenger" if object == "page" else "instagram"
    for page_entry in entry:
        handle_incoming_messenger_message(page_entry,platform)


def handle_incoming_messenger_message(entry,platform):
    for messaging_event in entry.get("messaging", []):
        try:
            # Ignore outgoing messages (from the page itself)
            if messaging_event["sender"]["id"] == entry.get("id"):
                continue  

            if "delivery" in messaging_event:
                handle_message_delivery_event(messaging_event)
                continue

            if "read" in messaging_event:
                handle_message_read_event(messaging_event,platform)
                continue

            sender_id = messaging_event["sender"]["id"]
            recipient_id = messaging_event["recipient"]["id"]
            timestamp = frappe.utils.now_datetime()
            message = messaging_event.get("message")
            user = create_or_update_messenger_user(sender_id,platform)
            # frappe.log_error("User",user)
            if not message:
                continue

            try:
                conversation = get_or_create_conversation(sender_id,platform)
            except Exception as e:
                frappe.log_error("Error in get_or_create_conversation", frappe.get_traceback())
                continue

            content_type = "text"
            message_text = ""
            file_url = None

            if "text" in message:
                message_text = message.get("text")
                content_type = "text"

            elif "attachments" in message:
                try:
                    attachment = message["attachments"][0]
                    content_type = attachment.get("type")
                    file_url = attachment.get("payload", {}).get("url")
                    message_text = f"{content_type.capitalize()} message"
                except Exception as e:
                    frappe.log_error("Error processing attachment", frappe.get_traceback())
                    continue

            try:
                frappe.db.set_value("Messenger Conversation", conversation, "last_message", message_text)
                frappe.db.set_value("Messenger Conversation", conversation, "last_message_time", timestamp)
            except Exception as e:
                frappe.log_error("Error setting last message/time", frappe.get_traceback())

            try:
                doc = frappe.get_doc({
                    "doctype": "Messenger Message",
                    "message_direction": "Incoming",
                    "sender_id": sender_id,
                    "sender_user": user,
                    "recipient_id": recipient_id,
                    "timestamp": timestamp,
                    "message_id": message.get("mid"),
                    "message": message_text,
                    "content_type": content_type,
                    "conversation": conversation,
                    "is_read": 0
                })
                try:
                    doc.insert(ignore_permissions=True)
                except Exception as e:
                    frappe.log_error("Error inserting Messenger Message", frappe.get_traceback())
                    return

                if file_url and content_type in ["image", "video", "audio", "file", "document"]:
                    if content_type == "file":
                        content_type = "document"
                    try:
                        # saved_file = save_url(file_url, f"{content_type}_{doc.message_id}", doc.doctype, doc.name)
                        saved_file = save_url(
                            file_url,
                            f"{content_type}_{doc.message_id}",
                            doc.doctype,
                            doc.name,
                            folder="Home/Attachments",   # Or any other folder you prefer
                            is_private=0                 # Set to 1 if the file should be private
                        )
                        doc.attach = saved_file.file_url
                        doc.save(ignore_permissions=True)
                    except Exception as e:
                        frappe.log_error("Error saving attachment file", frappe.get_traceback())

                # doc.insert(ignore_permissions=True)

            except Exception as e:
                frappe.log_error("Error inserting Messenger Message", frappe.get_traceback())

        except Exception as e:
            frappe.log_error("Unexpected error in handle_incoming_messenger_message", frappe.get_traceback())

def handle_message_delivery_event(messaging_event):
    sender_id = messaging_event["sender"]["id"]
    delivery = messaging_event["delivery"]
    mids = delivery.get("mids", [])
    watermark = delivery.get("watermark")

    for mid in mids:
        try:
            print("message delivery",mid)
            message_name = frappe.db.get_value("Messenger Message", {"message_id": mid},"name")
            message = frappe.get_doc("Messenger Message", message_name)
            message.status = "Delivered"
            message.save(ignore_permissions=True)

        except Exception as e:
            frappe.log_error("Error updating delivery status for message_id {}: {}".format(mid, str(e)))


def handle_message_read_event(messaging_event,platform):
    sender_id = messaging_event["sender"]["id"]
    # watermark = messaging_event["read"]["watermark"]
    conversation = get_or_create_conversation(sender_id,platform)

    if not conversation:
        frappe.log_error("Conversation not found for sender_id: {}".format(sender_id))
        return

    try:
        message_list = frappe.db.get_list("Messenger Message", {"conversation": conversation, "message_direction": "Outgoing","status": ("!=", "Read")},ignore_permissions=True)
        frappe.log_error("Message List",message_list)
        for message in message_list:
            message = frappe.get_doc("Messenger Message", message.name)
            message.status = "Read"
            message.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error("Error updating read status for messages in conversation: {}".format(conversation), str(e))

def get_or_create_conversation(sender_id,platform):
    # Dummy conversation logic – replace with your actual logic
    conversation = frappe.db.get_value("Messenger Conversation", {"sender_id": sender_id})
    
    reference_doctype = frappe.db.get_value("Messenger Conversation", {"sender_id": sender_id},"reference_doctype")
    reference_name = frappe.db.get_value("Messenger Conversation", {"sender_id": sender_id},"reference_name")
    if not reference_name:
        if get_cached_setting("auto_create_lead") == "1":
            sender = get_messenger_user(sender_id, platform)
            lead = get_or_create_new_lead(conversation,sender)
            reference_doctype = "CRM Lead"
            reference_name = lead
    if not conversation:
        sender = get_messenger_user(sender_id, platform)
        conversation_doc = frappe.get_doc({
            "doctype": "Messenger Conversation",
            "sender_id": sender_id,
            "status": "Open",
            "platform": platform,
            "sender":sender,
            "reference_doctype":reference_doctype,
            "reference_name":reference_name
        })
        conversation_doc.insert(ignore_permissions=True)
        if reference_doctype and reference_name:
            frappe.db.set_value(reference_doctype, reference_name, "custom_messenger_conversation", conversation_doc.name)
        return conversation_doc.name
    frappe.db.set_value("Messenger Conversation", conversation, {
        "reference_doctype": reference_doctype,
        "reference_name": reference_name
    })
    return conversation
    
def get_or_create_new_lead(conversation,sender):
    lead_exist = None
    if conversation:
        lead_exist = frappe.db.exists("CRM Lead",{"custom_messenger_conversation":conversation})
    
    if not lead_exist:
        user_name = frappe.db.get_value("Messenger User",sender,"username")
        platform = frappe.db.get_value("Messenger User",sender,"platform")
        user_id = frappe.db.get_value("Messenger User",sender,"user_id")
        lead = frappe.get_doc({
            "doctype": "CRM Lead",
            "first_name": user_name if user_name else f'lead from {platform}({user_id})',
            "last_name":"",
            "source": platform,
            "custom_messenger_conversation":conversation,
            "status": "New"
        })
        lead.insert(ignore_permissions=True)
        frappe.db.commit()
        return lead.name
    return lead_exist

def get_messenger_user(sender_id, platform):
    return frappe.db.get_value("Messenger User", {"user_id": sender_id, "platform": platform})


def get_cached_setting(fieldname):
    cached_settings = frappe.cache().get_value("messenger_settings_cache")
    
    if not cached_settings:
        cached_settings = frappe.db.get_value("Messenger Settings", None, "*", as_dict=True)
        frappe.cache().set_value("messenger_settings_cache", cached_settings)
    
    return cached_settings.get(fieldname)


# @frappe.whitelist(allow_guest=True)
# def fetch_all_messages():
# 	settings = frappe.get_single("Messenger Settings")
# 	print("Hii worked ",settings.url)
	

# 	if not settings.enabled:
# 		return
# 	url = f"{settings.url}/{settings.version}/{settings.page_id}/conversations"
# 	token = settings.get_password("access_token")
# 	params = {
# 		"access_token": token,
# 		"fields": "messages{message,from,to,created_time,id}",
# 		"platform":"messenger"
# 	}
# 	response = requests.get(url, params=params)
# 	if response.status_code != 200:
# 		frappe.log_error(response.text, "Messenger Fetch Error")
# 		return
# 	data = response.json()
# 	conversations = data.get('data', [])
# 	for convo in conversations:
# 		convo_id = convo['id']
# 		messages = convo.get('messages', {}).get('data', [])
# 		print("messages[-1][created_time]",messages[-1]["created_time"])
# 		created_time = parser.parse(messages[0]["created_time"]).replace(tzinfo=None)
# 		print("Created TIME = > ",created_time )

# 		existing_convo = frappe.db.exists("Messenger Conversation", {"conversation_id": convo_id})
# 		if existing_convo:
# 			conversation_doc = frappe.get_doc("Messenger Conversation", existing_convo)
# 			frappe.db.set_value("Messenger Conversation", existing_convo, "last_message", messages[0]["message"])
# 		else:	
# 			conversation_doc = frappe.get_doc({
# 				"doctype": "Messenger Conversation",
# 				"conversation_id":convo_id,
# 				"platform": "Messenger",
# 				"sender_id": messages[-1]["from"]["id"],
# 				"last_message": messages[0]["message"],
# 				"last_message_time": created_time,
# 				"status": "Open"
# 			})
# 			conversation_doc.insert(ignore_permissions=True)

# 		for message in messages:
# 			message_id = message.get('id')
			
# 			if frappe.db.exists("Messenger Message", {"message_id": message_id}):
# 				continue

# 			message_text = message.get("message", "")
# 			from_id = message.get('from', {}).get('id')
# 			to_data = message.get('to', {}).get('data', [])
# 			created_time =parser.parse(message.get('created_time')).replace(tzinfo=None)
			
# 			frappe.get_doc({
# 				"doctype": "Messenger Message",
# 				"message_direction":"Incoming" if from_id != settings.page_id else "Outgoing",
# 				"conversation": conversation_doc.name,
# 				"sender_id": from_id,
# 				"message": message_text,
# 				"timestamp": created_time,
# 				"message_id": message_id
# 			}).insert(ignore_permissions=True)
# 			from_user = message.get('from', {})
# 			if from_user:
# 				create_or_update_messenger_user(
#                     user_id=from_user.get('id'),
#                     user_name=from_user.get('name'),
#                     platform="Messenger"
#                 )

# //////////////////////////
# def create_or_update_messenger_user(user_id, user_name, platform):
#     if not user_id:
#         return

#     if frappe.db.exists("Messenger User", {"user_id": user_id, "platform": platform}):
#         # Already exists, maybe update username if changed
#         user_doc = frappe.get_doc("Messenger User", {"user_id": user_id, "platform": platform})
#         if user_doc.username != user_name:
#             user_doc.username = user_name
#             user_doc.save(ignore_permissions=True)
#             return user_doc.name
#     else:
#         # Create new
#         user_doc=frappe.get_doc({
#             "doctype": "Messenger User",
#             "user_id": user_id,
#             "username": user_name,
#             "platform": platform
#         }).insert(ignore_permissions=True)
#         return user_doc.name

def create_or_update_messenger_user(user_id, platform=None, user_name=None):
    if not user_id:
        return

    # Get Messenger Settings
    settings = frappe.get_single("Messenger Settings")
    token = settings.get_password("access_token")
    frappe.log_error("Platform", platform)

    # Choose fields based on platform
    if platform == "instagram":
        fields = "name,profile_pic"
    else:  # Default to Messenger
        fields = "first_name,last_name,profile_pic"

    url = f"{settings.url}/{settings.version}/{user_id}?fields={fields}&access_token={token}"

    # Fetch user details from Meta
    try:
        response = requests.get(url)
        frappe.log_error("Response NWWw ", response)
        if response.status_code == 200:
            data = response.json()
            if platform == "instagram":
                user_name = data.get("name", "") or user_name
            else:
                fetched_name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
                user_name = fetched_name or user_name

            profile_pic = data.get("profile_pic", "")
        else:
            frappe.log_error("Messenger User Sync", f"Failed to fetch user info: {response.text}")
            profile_pic = ""
    except Exception:
        frappe.log_error("Messenger User API Error", frappe.get_traceback())
        profile_pic = ""

    # Check if user exists
    if frappe.db.exists("Messenger User", {"user_id": user_id, "platform": platform}):
        user_doc = frappe.get_doc("Messenger User", {"user_id": user_id, "platform": platform})
        frappe.log_error("User Doc", user_doc)
        updated = False

        if user_doc.username != user_name:
            user_doc.username = user_name
            updated = True

        if profile_pic and not user_doc.profile:
            user_doc.profile = profile_pic
            updated = True

        if updated:
            user_doc.save(ignore_permissions=True)

        return user_doc.name
    else:
        # Create new
        user_doc = frappe.get_doc({
            "doctype": "Messenger User",
            "user_id": user_id,
            "username": user_name,
            "platform": platform,
            "profile": profile_pic
        }).insert(ignore_permissions=True)
        return user_doc.name



def fetch_messages_for_conversation(convo_id, token, version, local_tz, platform, page_id, conversation_doc):
    url = f"https://graph.facebook.com/{version}/{convo_id}/messages"
    params = {
        "access_token": token,
        "fields": "message,from,to,created_time,id",
        "limit": 100
    }
    latest_created_time = None
    latest_message = ""

    while url:
        response = requests.get(url, params=params).json()
        for message in response.get("data", []):
            message_id = message.get('id')
            if frappe.db.exists("Messenger Message", {"message_id": message_id}):
                continue

            message_text = message.get("message", "")
            from_id = message.get("from", {}).get("id")
            from_username = message.get("from", {}).get("name") if platform == "messenger" else message.get("from", {}).get("username")
            created_time_utc = parser.parse(message["created_time"])
            created_time = created_time_utc.astimezone(local_tz).replace(tzinfo=None)
            to_id = message.get("to", {}).get("id")

            direction = "Incoming" if from_id != page_id else "Outgoing"

            frappe.get_doc({
                "doctype": "Messenger Message",
                "message_direction": direction,
                "conversation": conversation_doc.name,
                "sender_id": from_id,
                "recipient_id": to_id,
                "message": message_text,
                "timestamp": created_time,
                "message_id": message_id
            }).insert(ignore_permissions=True)

            if from_id:
                create_or_update_messenger_user(
                    user_id=from_id,
                    user_name=from_username,
                    platform=platform   
                )
            if not latest_created_time or created_time > latest_created_time:
                latest_created_time = created_time
                latest_message = message_text

        url = response.get("paging", {}).get("next")
        params = {}  # Use full URL from 'next'
    if latest_created_time:
        conversation_doc.db_set("last_message", latest_message, update_modified=False)
        conversation_doc.db_set("last_message_time", latest_created_time, update_modified=False)


@frappe.whitelist(allow_guest=True)
def fetch_all_messages():
    settings = frappe.get_single("Messenger Settings")
    if not settings.enabled:
        return

    token = settings.get_password("access_token")
    timezone = frappe.db.get_single_value("System Settings", "time_zone")
    local_tz = pytz.timezone(timezone)

    for platform in ["messenger", "instagram"]:
        page_id = settings.page_id if platform == "messenger" else settings.instagram_page_id
        url = f"{settings.url}/{settings.version}/{ settings.page_id}/conversations"
        params = {
            "access_token": token,
            "fields": "participants{name,id,profile_pic}",  # Don't fetch nested messages here
            "platform": platform,
            "limit": 100
        }

        response = requests.get(url, params=params)
        frappe.log_error(f"Fetch All Messages {platform}",f"Fetch All Messages {response} from {platform}")
        if response.status_code != 200:
            frappe.log_error(f"{platform.capitalize()} Fetch Error ok", response.text)
            continue

        data = response.json()
        conversations = data.get('data', [])
        for convo in conversations:
            convo_id = convo.get('id')
            participants = convo.get("participants", {}).get("data", [])

            existing_convo = frappe.db.exists("Messenger Conversation", {"conversation_id": convo_id})
            if existing_convo:
                conversation_doc = frappe.get_doc("Messenger Conversation", existing_convo)
            else:
                sender_id = participants[0].get("id") if platform == "messenger" else participants[1].get("id")
                conversation_doc = frappe.get_doc({
                    "doctype": "Messenger Conversation",
                    "conversation_id": convo_id,
                    "platform": platform.capitalize(),
                    "sender_id": sender_id,
                    "status": "Open"
                })
                conversation_doc.insert(ignore_permissions=True)

            # Fetch all messages for this conversation
            fetch_messages_for_conversation(convo_id, token, settings.version, local_tz, platform, page_id, conversation_doc)



def send_message_on_creation(doc,method):
	print("Sending Message on Creation",doc)
	frappe.log_error("Sending Message on Creation",f"Sending Message on Creation {doc}")
	if doc.message_direction != "Outgoing":
		return
	send_message(doc.recipient_id,doc.message )



@frappe.whitelist()
def send_message(recipient_id,message):
	# recipient_id = "9780239182022706"
	# message = "HIIIII test"
	print("Sending Message",f"Sending Message to {recipient_id} with message {message}")
	frappe.log_error("Sending Message",f"Sending Message to {recipient_id} with message {message}")
	settings = frappe.get_single("Messenger Settings")
	url = f"{settings.url}/{settings.version}/me/messages"
	token = settings.get_password("access_token")
	print("token", token)
	params = {
        "access_token": token
    }
	payload = {
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message
        }
    }
	response = requests.post(url, params=params, json=payload)
	print("RESPONSE",response)
	if response.status_code != 200:
		frappe.log_error("Messenger Send Message Error",response.text)
		frappe.throw("Failed to send message")