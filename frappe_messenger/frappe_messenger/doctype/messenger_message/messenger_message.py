# Copyright (c) 2025, Tridz Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import requests
import json
import os
from frappe.model.document import Document
from frappe.utils import get_site_path,get_datetime



class MessengerMessage(Document):
	def after_insert(self):
		self.send_message_on_creation()
		self.open_conversation()

	def open_conversation(self):
		if self.content_type == 'flow':
			return
		if self.conversation:
			if self.message_direction == "Incoming":
				conversation = frappe.get_doc("Messenger Conversation",self.conversation)
				if conversation.status != "Open":
					conversation.status = "Open"
					conversation.append("first_response", {
						"status":"Open",
						"incoming_message":self.name,
						"incoming_message_time":self.timestamp
					})
					conversation.save(ignore_permissions=True)
				else:
					return
		else:
			frappe.log_error("Conversation not found", f"conversation not found for message {self.name}")
	
	def send_message_on_creation(self):
		if self.message_direction != "Outgoing" or self.message_id:
			return
		send_message(self,self.recipient_id,self.message )
		track_response_time(self)
		update_first_response_log(self)

def upload_messenger_large_file(file_url, file_type, token, settings):
	"""Upload large file (video, etc.) as reusable attachment to Facebook Messenger"""
	try:
		file_path = frappe.get_site_path('public', file_url.lstrip('/'))

		with open(file_path, 'rb') as f:
			files = {
				"filedata": (os.path.basename(file_path), f, "video/mp4" if file_type == "video" else "application/octet-stream")
			}

			params = {
				"access_token": token,
			}
			data = {
				"message": json.dumps({
					"attachment": {
						"type": file_type,
						"payload": {
							"is_reusable": True
						}
					}
				})
			}

			upload_url = f"{settings.url}/{settings.version}/me/message_attachments"
			response = requests.post(upload_url, params=params, data=data, files=files)

			if response.status_code != 200:
				frappe.throw(f"Failed to upload file: {response.text}")

			return response.json().get("attachment_id")

	except Exception as e:
		frappe.log_error("Messenger Video Upload", str(e))
		frappe.throw(f"Failed to upload file: {str(e)}")

@frappe.whitelist()
def send_message(self,recipient_id,message):
	platform = frappe.db.get_value("Messenger Conversation",self.conversation,"platform")
	from_meta = frappe.db.get_value("Messenger Platform",platform,"from_meta")
	if not from_meta:
		return
	if platform == "WhatsApp":
		whatsapp_msg = send_whatsapp_message(self)
		frappe.db.set_value("Messenger Message", self.name, "message_id", whatsapp_msg.message_id)
		return
	frappe.log_error("Sending Message",f"Sending Message to {recipient_id} with message {message} // {self.content_type}")
	settings = frappe.get_single("Messenger Settings")
	url = f"{settings.url}/{settings.version}/me/messages"
	token = settings.get_password("access_token")
	params = {
        "access_token": token
    }
	payload = {
        "recipient": {
            "id": recipient_id
        }
    }
	if self.content_type == "text":
		payload["message"] = {"text": message}
	elif self.content_type in ["image", "file", "video", "audio"]:
		file_url = frappe.utils.get_url(self.attach)

		# For videos, use chunked upload
		if self.content_type == "video":
			try:
				# Get file size
				file_path = frappe.get_site_path('public', self.attach.lstrip('/'))
				file_size = os.path.getsize(file_path)
				frappe.log_error("File Size",f"File Size {file_size}")
				
				# If file size is greater than 20MB, use chunked upload
				if file_size > 1 * 1024 * 1024:  # 1MB in bytes
					frappe.log_error("Uploading Large File",f"Uploading Large File {self.attach}")
					attachment_id = upload_messenger_large_file(self.attach, self.content_type, token, settings)
					payload["message"] = {
						"attachment": {
							"type": self.content_type,
							"payload": {
								"attachment_id": attachment_id
							}
						}
					}
				else:
					# Use regular upload for smaller files
					payload["message"] = {
						"attachment": {
							"type": self.content_type,
							"payload": {
								"url": file_url,
								"is_reusable": True
							}
						}
					}
			except Exception as e:
				frappe.log_error("Video Upload Error", str(e))
				frappe.throw(f"Failed to upload video: {str(e)}")
		else:
			# Regular upload for other file types
			payload["message"] = {
				"attachment": {
					"type": self.content_type,
					"payload": {
						"url": file_url,
						"is_reusable": True
					}
				}
			}
	else:
		frappe.throw(f"Unsupported content type: {self.content_type}")
	response = requests.post(url, params=params, json=payload)
	if response.status_code == 200:
		res_json = response.json()
		message_id = res_json.get("message_id")
		frappe.db.set_value("Messenger Message", self.name, "message_id", message_id)

		if self.conversation:
			frappe.db.set_value("Messenger Conversation", self.conversation, "last_message", message)
			frappe.db.set_value("Messenger Conversation", self.conversation, "last_message_time", self.creation)

	else:
		frappe.log_error("Messenger Send Message Error", response.text)
		frappe.throw("Failed to send message")

@frappe.whitelist()
def mark_messages_as_read(conversation):
	"""Mark all unread incoming messages in a conversation as read"""
	if not conversation:
		return
		
	# Update all unread incoming messages for the conversation
	frappe.db.sql("""
		UPDATE `tabMessenger Message`
		SET `is_read` = 1
		WHERE `conversation` = %s
		AND `message_direction` = 'Incoming'
		AND `is_read` = 0
	""", (conversation))
	
	frappe.db.commit()
	platform = frappe.db.get_value("Messenger Conversation",conversation,"platform")
	if platform == "Messenger":
		settings = frappe.get_single("Messenger Settings")
		url = f"{settings.url}/{settings.version}/me/messages"
		token = settings.get_password("access_token")
		sender_id = frappe.db.get_value("Messenger Conversation",conversation,"sender_id")
		params = {
			"access_token": token
		}
		payload = {
			"recipient": {
				"id": sender_id
			},
			'sender_action': 'mark_seen'
		}
		response = requests.post(url, params=params, json=payload)
	
	# Return updated unread count for the conversation
	return frappe.db.count('Messenger Message', 
		filters={
			'conversation': conversation,
			'message_direction': 'Incoming',
			'is_read': 0
		}
	)

def get_permission_query_conditions(user):
	if not user or user == "Administrator":
		return ""
	settings = frappe.get_cached_doc("Messenger Settings")

	if not settings.restrict_by_assignment:
		return ""
	
	user_roles = frappe.get_roles(user)
	unrestricted_roles = [d.role for d in settings.unrestricted_roles]
	
	if any(role in user_roles for role in unrestricted_roles):
		return ""
		
	return """(`tabMessenger Conversation`.name IN (
				SELECT reference_name
				FROM `tabToDo`
				WHERE `reference_type` = 'Messenger Conversation'
				AND `status` = 'Open' 
				AND `allocated_to` = {user}
			))
			""".format(user=frappe.db.escape(user))


def send_whatsapp_message(self):
	try:
		whatsapp_msg = frappe.new_doc("WhatsApp Message")
		whatsapp_msg.update({
            "to": self.recipient_id,
            "message": self.message,
            "content_type": self.content_type,
            "custom_message_from_messenger": 1,
			"attach":self.attach
        })
		whatsapp_msg.insert(ignore_permissions=True)

		if self.conversation:
				frappe.db.set_value("Messenger Conversation", self.conversation, {
					"last_message": self.message,
					"last_message_time": self.creation
				})

		return whatsapp_msg
	except Exception as e:
		frappe.log_error(
            title="send_whatsapp_message Error",
            message=frappe.get_traceback()
        )
		return None

def track_response_time(self):
    if self.message_direction != "Outgoing":
        return

    last_outgoing = frappe.db.get_all(
        "Messenger Message",
        filters={
            "conversation": self.conversation,
            "message_direction": "Outgoing",
            "creation": ["<", self.creation]
        },
        fields=["name", "creation"],
        order_by="creation desc",
        limit=1
    )

    last_outgoing_time = get_datetime(last_outgoing[0]["creation"]) if last_outgoing else None

    incoming_filters = {
        "conversation": self.conversation,
        "message_direction": "Incoming",
        "creation": ["<", self.creation],
    }

    if last_outgoing_time:
        incoming_filters["creation"] = [">", last_outgoing_time, "<", self.creation]

    incoming_messages = frappe.db.get_all(
        "Messenger Message",
        filters=incoming_filters,
        fields=["name", "creation"],
        order_by="creation asc"
    )

    if not incoming_messages:
        return

    incoming_msg = incoming_messages[0]
    incoming_time = get_datetime(incoming_msg["creation"])
    outgoing_time = get_datetime(self.creation)
    response_time = (outgoing_time - incoming_time).total_seconds()


    conversation = frappe.get_doc("Messenger Conversation", self.conversation)
    conversation.append("response_times", {
        "incoming_message": incoming_msg["name"],
        "outgoing_message": self.name,
        "response_time": response_time,
        "user": frappe.session.user
    })

    total = 0
    count = 0
    for row in conversation.response_times:
        total += row.response_time or 0
        count += 1
    if count > 0:
        conversation.avg_response_time = round(total / count, 2)
        
    conversation.save(ignore_permissions=True)
    frappe.db.commit()

def update_first_response_log(self):
	if self.message_direction != "Outgoing":
		return
	
	rows = frappe.db.get_all(
        'Messenger First Response Details',
        filters={
            'parent': self.conversation,
            'status': 'Open',
            'outgoing_message': ['=', ''],  # empty outgoing field
        },
        fields=['name', 'incoming_message', 'incoming_message_time', 'parent'],
        order_by='incoming_message_time asc',
        limit_page_length=1
    )

	if not rows:
		return
	
	row = rows[0]
	incoming_time = get_datetime(row.incoming_message_time)
	outgoing_time = get_datetime(self.creation)
	response_seconds = (outgoing_time - incoming_time).total_seconds()

	frappe.db.set_value(
        'Messenger First Response Details',
        row.name,
        {
            'outgoing_message': self.name,
            'outgoing_message_time': self.creation,
            'response_time_in_seconds': response_seconds,
			'user':frappe.session.user
        },
        update_modified=False
    )

	update_avg_response_time(self.conversation)


def update_avg_response_time(convo_name):
    rows = frappe.db.get_all(
        'Messenger First Response Details',
        filters={
            'parent': convo_name,
            'response_time_in_seconds': ['>', 0]
        },
        fields=['response_time_in_seconds']
    )
    if not rows:
        return

    total = sum(r.response_time_in_seconds for r in rows)
    avg = round(total / len(rows), 2)
    frappe.db.set_value(
        'Messenger Conversation',
        convo_name,
        'avg_first_response_time',
        avg
    )

