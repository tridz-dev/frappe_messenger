// Copyright (c) 2024, Tridz Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Messenger Notification Log', {
	refresh: function(frm) {
		// Format JSON in meta_data field for better readability
		if (frm.doc.meta_data) {
			try {
				let formatted = JSON.stringify(JSON.parse(frm.doc.meta_data), null, 2);
				frm.set_value('meta_data', formatted);
			} catch (e) {
				console.error('Error formatting JSON:', e);
			}
		}
	}
}); 