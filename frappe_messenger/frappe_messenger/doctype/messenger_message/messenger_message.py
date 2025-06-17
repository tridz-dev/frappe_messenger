# Copyright (c) 2025, Tridz Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import requests
import json
import os
from frappe.model.document import Document
from frappe.utils import get_site_path


class MessengerMessage(Document):
	def after_insert(self):
		# pass
		self.send_message_on_creation()
		self.open_conversation()

	def open_conversation(self):
		if self.conversation:
			conversation = frappe.get_doc("Messenger Conversation",self.conversation)
			if conversation.status != "Open":
				conversation.status = "Open"
				conversation.save(ignore_permissions=True)
			else:
				return
		else:
			frappe.log_error("Conversation not found", f"conversation not found for message {self.name}")
	
	def send_message_on_creation(self):
		# print("Sending Message on Creation",self)
		# frappe.log_error("Sending Message on Creation",f"Sending Message on Creation {self}")
		if self.message_direction != "Outgoing" or self.message_id:
			return
		send_message(self,self.recipient_id,self.message )

# def upload_messenger_large_file(file_url, file_type, token, settings):
# 	"""Handle large file uploads using Facebook's chunked upload API for Messenger"""
# 	try:
# 		# Download the file from Frappe's public directory
# 		file_content = requests.get(file_url).content
# 		file_size = len(file_content)

# 		# Start chunked upload session
# 		session_url = f"https://graph-video.facebook.com/{settings.version}/me/message_attachments"
# 		start_params = {
# 			"access_token": token,
# 			"upload_phase": "start",
# 			"file_length": file_size,
# 			"file_type": "video/mp4" if file_type == "video" else "application/octet-stream"
# 		}
		
# 		start_response = requests.post(session_url, params=start_params)
# 		if start_response.status_code != 200:
# 			frappe.throw(f"Failed to start chunked upload: {start_response.text}")
		
# 		upload_session_id = start_response.json().get("attachment_id")
		
# 		# Upload file in chunks
# 		chunk_size = 4 * 1024 * 1024  # 4MB chunks
# 		for i in range(0, file_size, chunk_size):
# 			chunk = file_content[i:i + chunk_size]
			
# 			transfer_params = {
# 				"access_token": token,
# 				"upload_phase": "transfer",
# 				"attachment_id": upload_session_id,
# 				"offset": i
# 			}
			
# 			transfer_response = requests.post(
# 				session_url,
# 				params=transfer_params,
# 				files={"video": chunk}
# 			)
			
# 			if transfer_response.status_code != 200:
# 				frappe.throw(f"Failed during chunk upload: {transfer_response.text}")
		
# 		# Finish upload
# 		finish_params = {
# 			"access_token": token,
# 			"upload_phase": "finish",
# 			"attachment_id": upload_session_id
# 		}
		
# 		finish_response = requests.post(session_url, params=finish_params)
# 		if finish_response.status_code != 200:
# 			frappe.throw(f"Failed to finish upload: {finish_response.text}")
			
# 		return finish_response.json().get("attachment_id")
		
# 	except Exception as e:
# 		frappe.log_error(f"Error in chunked upload",f"Error in chunked upload: {str(e)}")
# 		frappe.throw(f"Failed to upload large file: {str(e)}")

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
	print("PLATFORM form send.. ", platform)
	from_meta = frappe.db.get_value("Messenger Platform",platform,"from_meta")
	print("from meta",from_meta)
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
	print("token", token)
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
	print("RESPONSE",response)
	if response.status_code == 200:
		res_json = response.json()
		message_id = res_json.get("message_id")
		print("message_id ===== >>> ",message_id)
		# self.message_id = message_id
		frappe.db.set_value("Messenger Message", self.name, "message_id", message_id)

		if self.conversation:
			frappe.db.set_value("Messenger Conversation", self.conversation, "last_message", message)
			frappe.db.set_value("Messenger Conversation", self.conversation, "last_message_time", self.creation)

		# Update last message in the conversation (assuming conversation exists)
		# conversation = frappe.get_value("Messenger Conversation", {"recipient_id": recipient_id})
		# if conversation:
		# 	frappe.db.set_value("Messenger Conversation", conversation, "last_message", message)

	else:
		frappe.log_error("Messenger Send Message Error", response.text)
		frappe.throw("Failed to send message")
	# if response.status_code != 200:
	# 	frappe.log_error("Messenger Send Message Error",response.text)
	# 	frappe.throw("Failed to send message")

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
		# print("CONVERSATION .. ", conversation)
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
            "custom_message_from_messenger": 1
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