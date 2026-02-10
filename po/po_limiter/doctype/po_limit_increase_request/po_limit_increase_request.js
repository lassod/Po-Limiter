// Copyright (c) 2026, Lassod
// License: MIT

frappe.ui.form.on('PO Limit Increase Request', {
	refresh: function(frm) {
		// Add Approve button for System Manager (MD)
		if (frm.doc.status === 'Pending Approval' && frappe.user.has_role('System Manager')) {
			frm.add_custom_button(__('Approve'), function() {
				frappe.call({
					method: 'po.po_limiter.po_limit_increase_request.approve_request',
					args: {
						request_name: frm.doc.name
					},
					callback: function(r) {
						frm.reload_doc();
					}
				});
			}, __('Actions'));

			frm.add_custom_button(__('Reject'), function() {
				let rejection_reason = prompt('Please enter rejection reason:');
				if (rejection_reason) {
					frappe.call({
						method: 'po.po_limiter.po_limit_increase_request.reject_request',
						args: {
							request_name: frm.doc.name,
							rejection_reason: rejection_reason
						},
						callback: function(r) {
							frm.reload_doc();
						}
					});
				}
			}, __('Actions'));
		}
	},

	user: function(frm) {
		// Load current limits when user changes
		if (frm.doc.user && frm.doc.company) {
			frm.trigger('set_current_limits');
		}
	},

	company: function(frm) {
		// Load current limits when company changes
		if (frm.doc.user && frm.doc.company) {
			frm.trigger('set_current_limits');
		}
	},

	set_current_limits: function(frm) {
		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				doctype: 'User PO Limit',
				filters: {
					user: frm.doc.user,
					company: frm.doc.company
				},
				fieldname: ['per_po_limit', 'per_month_limit']
			},
			callback: function(r) {
				if (r.message) {
					frm.set_value('current_per_po_limit', r.message.per_po_limit || 0);
					frm.set_value('current_per_month_limit', r.message.per_month_limit || 0);
				} else {
					frm.set_value('current_per_po_limit', 0);
					frm.set_value('current_per_month_limit', 0);
				}
			}
		});
	}
});
