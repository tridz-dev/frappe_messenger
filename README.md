# Frappe Messenger

Frappe Messenger lets you manage and reply to messages from Facebook Messenger, Instagram, and WhatsApp — all inside your Frappe or CRM system.

## Key Features

- **Multi-Platform Messaging**: Handle conversations from Facebook Messenger, Instagram, and WhatsApp in one place. You can enable or disable each platform as needed in Messenger Platform list. 
  - *Note: WhatsApp messaging requires the [Frappe WhatsApp app](https://github.com/shridarpatil/frappe_whatsapp) to be installed and configured.*
- **Message History**: See all incoming and outgoing messages, with search and filters.
- **Assignments**: Assign conversations to team members for better tracking and follow-up.
- **Auto Assignment (with Raven)**: If enabled in settings, conversations can be automatically assigned to available users based on their status in the [Raven app](https://github.com/The-Commit-Company/raven). You must install Raven for this feature.
- **Helpdesk Ticket Creation**: Create support tickets directly from any Messenger chat (if enabled in settings). For advanced helpdesk features, see [Frappe Helpdesk](https://github.com/frappe/helpdesk). You must install Helpdesk for this feature.
- **Platform Icons**: Instantly see which platform a conversation is from.
- **Easy User Resolution**: Usernames and profiles are shown for each sender.
- **Status Tracking**: Mark conversations as Open, Resolved, or other custom statuses. Status changes are visible to all team members in real time.
- **Tags**: Add tags to conversations for easy organization and searching.
- **Block Chat**: Block specific conversations to remove from conversation list.
- **File & Media Support**: Send and receive text, images, videos, audio, and documents (platform support may vary).
- **Auto-Create Leads**: New conversations can automatically create a CRM Lead, which you can view and manage from the CRM (if enabled in settings).

## How It Works in CRM

- Messenger is available as a tab in your CRM sidebar (if enabled in settings).
- All CRM users can view, reply, and assign conversations.
- You can filter conversations by added platforms.
- Create helpdesk tickets from any chat (if allowed by admin). For advanced helpdesk features, install [Frappe Helpdesk](https://github.com/frappe/helpdesk).
- Assign chats to yourself or teammates for follow-up.
- Add tags to conversations for better organization.
- Block chats to stop unwanted messages.
- Change conversation status (e.g., Open, Resolved, Pending) to track progress.
- View leads that are automatically created from new conversations.
- Real-time updates keep everyone in sync.

## Getting Started

### 1. Install the App

```bash
bench get-app frappe_messenger https://github.com/tridz-dev/frappe_messenger.git
bench --site your-site.local install-app frappe_messenger
```

### 2. Configure Messenger Settings

- Go to **Messenger Settings** in your site.
- Fill in:
  - Access Token
  - URL
  - Version
  - Facebook Page ID
  - Instagram Page ID
  - App ID
  - Webhook Verify Token
- Enable auto-assignment to assign conversations to available users via [Raven](https://github.com/The-Commit-Company/raven).
- Enable features like auto-assign, helpdesk ticket creation, auto-create leads, or chat blocking as needed.

### 3. Set Up Facebook/Instagram Webhooks

- In your Facebook Developer Console, add the following webhook URL:

  ```
  <domain>/api/method/frappe_messenger.utils.webhook.messenger_webhook
  ```

- Add verify token on meta and update the same on Messenger Settings
- Subscribe to events: `messages`, `messaging_postbacks`, `messaging_optins`.

### 4. Using Messenger in CRM

- Open your CRM and look for the **Messenger** tab in the sidebar.
- Click any conversation to view and reply.
- Use the filter to show only Messenger, Instagram, or WhatsApp chats.
- Assign chats or create helpdesk tickets from the chat menu (3 dots).
- Add or remove tags to organize conversations.
- Block chats if needed to stop further messages from a sender.
- Change the status of a conversation (Open, Resolved, etc.) using the status dropdown.
- View leads that are auto-created from new conversations in the CRM Leads section.
- All updates happen in real time—no refresh needed.

## Notes

- Messenger features and UI follow Frappe standards for consistency.
- Only users with permission can access Messenger features.
- Helpdesk ticket creation, assignment, chat blocking, and auto-lead creation can be enabled/disabled by admins.
- *WhatsApp support requires the [Frappe WhatsApp app](https://github.com/shridarpatil/frappe_whatsapp) to be installed and configured.*
- *Auto-assignment based on user availability requires the [Raven app](https://github.com/The-Commit-Company/raven) to be installed and configured.*
- *For advanced helpdesk features, see [Frappe Helpdesk](https://github.com/frappe/helpdesk).* 

## License

Frappe Messenger is developed and maintained by Tridz Technologies Pvt. Ltd.
