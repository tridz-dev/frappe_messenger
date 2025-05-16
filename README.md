## Frappe Messenger

Integrate and manage Facebook Messenger and Instagram messages from Frappe.

### Features

- Facebook Messenger Integration
- Instagram Messages Integration
- Message history tracking
- Platform-specific icons and titles


### Installation

1. Install using bench:
```bash
bench get-app frappe_messenger https://github.com/tridz-dev/frappe_messenger.git
```

2. Install the app on your site:
```bash
bench --site your-site.local install-app frappe_messenger
```

### Configuration

1. Go to **Messenger Settings**
2. Configure the following settings:
   - Access Token
   - URL
   - Version
   - Facebook Page ID
   - Instagram Page ID
   - App ID 
   - Webhook Verify Token

3. Set up webhook endpoints in your Facebook Developer Console:
   - Add the webhook URL provided in the settings
   - Subscribe to the following events:
     - messages
     - messaging_postbacks
     - messaging_optins

### Usage

1. **Accessing Messages**
   - Navigate to **Messenger > Messages**
   - View all incoming and outgoing messages
   - Filter messages by platform (Facebook/Instagram)
   - Search messages by content or sender

2. **Sending Messages**
   - Use the message composer in the dashboard
   - Select recipient from contacts
   - Choose platform (Facebook/Instagram)
   - Send text, images, or templates


### License

Frappe Messenger is developed and maintained by Tridz Technologies Pvt. Ltd.
