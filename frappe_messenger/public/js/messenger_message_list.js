frappe.listview_settings['Messenger Message'] = {
    onload: function(listview) {
        console.log("Hello list view loaded");
        listview.page.add_inner_button('Fetch Messages', () => {
            console.log("Hello");
            frappe.call({
                method: 'frappe_messenger.utils.webhook.fetch_all_messages',
                freeze: true,  // <-- This freezes the UI
                freeze_message: "Fetching messages...",  
                callback: function(r) {
                    if (!r.exc) {
                        frappe.msgprint('Action completed successfully!');
                        listview.refresh();
                    }
                }
            });
        });
    }
};