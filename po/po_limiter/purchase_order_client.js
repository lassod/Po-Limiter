// Copyright (c) 2026, Lassod
// License: MIT

frappe.ui.form.on('Purchase Order', {
	refresh: function(frm) {
		// Only check limits for unsaved/draft documents
		if (frm.doc.docstatus !== 0) {
			return;
		}

		// Get current PO amount
		var po_amount = parseFloat(frm.doc.base_grand_total) || 0;

		// Check user's PO limit status
		// This runs on form load to show/hide the submit button
		frappe.call({
			method: 'po.po_limiter.po_validation.get_user_po_limit_status',
			args: {
				user: frappe.session.user,
				company: frm.doc.company
			},
			callback: function(r) {
				if (r.message) {
					var limit_status = r.message.status;
					var per_po_limit = parseFloat(r.message.per_po_limit) || 0;
					var per_month_limit = parseFloat(r.message.per_month_limit) || 0;

					// Remove any existing warning messages first
					$('[data-fieldname="po_limit_warning"]').remove();
					$('[data-fieldname="po_limit_exceeded"]').remove();
					$('[data-fieldname="po_limit_info"]').remove();

					var can_submit = true;
					var message = '';
					var message_type = '';

					// Rule 1: No limit assigned or status is Revoked
					if (limit_status === 'Revoked') {
						can_submit = false;
						message_type = 'warning';
						message = '<strong>PO Limit Restriction:</strong> PO submission requires MD approval. ' +
									'Please contact the Managing Director to request a PO submission limit. ' +
									'<a href="#Form/PO Limit Increase Request/PO Limit Increase Request" class="btn btn-xs btn-default" style="margin-left: 10px;">Request Limit</a>';
					}
					// Rule 2: Per PO Limit is 0 or not set
					else if (per_po_limit <= 0) {
						can_submit = false;
						message_type = 'warning';
						message = '<strong>PO Limit Restriction:</strong> You do not have a Per PO submission limit. ' +
									'Please contact the Managing Director to request a PO submission limit. ' +
									'<a href="#Form/PO Limit Increase Request/PO Limit Increase Request" class="btn btn-xs btn-default" style="margin-left: 10px;">Request Limit</a>';
					}
					// Rule 3: Per Month Limit is 0 or not set
					else if (per_month_limit <= 0) {
						can_submit = false;
						message_type = 'warning';
						message = '<strong>PO Limit Restriction:</strong> You do not have a Monthly submission limit. ' +
									'Please contact the Managing Director to set your monthly submission limit. ' +
									'<a href="#List/User PO Limit" class="btn btn-xs btn-default" style="margin-left: 10px;">View Limits</a>';
					}
					// Rule 4: PO amount exceeds Per PO limit
					else if (po_amount > per_po_limit) {
						can_submit = false;
						message_type = 'danger';
						message = '<strong>PO Limit Exceeded:</strong><br>' +
									'Your PO Amount: <strong>' + frappe.format(po_amount, {fieldtype: 'Currency'}) + '</strong><br>' +
									'Your Per PO Limit: <strong>' + frappe.format(per_po_limit, {fieldtype: 'Currency'}) + '</strong><br>' +
									'Excess Amount: <strong>' + frappe.format(po_amount - per_po_limit, {fieldtype: 'Currency'}) + '</strong><br>' +
									'Please reduce the PO amount or request MD approval. ' +
									'<a href="#Form/PO Limit Increase Request/PO Limit Increase Request" class="btn btn-xs btn-default" style="margin-left: 10px;">Request Limit Increase</a>';
					}
					// Rule 5: All checks passed - show submit button and info
					else {
						can_submit = true;
					}

					// Hide or show Submit button based on validation
					if (!can_submit) {
						// Hide the Submit button
						frm.page.set_primary_action();

						// Add warning/error message
						$(frm.wrapper).find('.form-page').prepend(
							'<div class="alert alert-' + message_type + '" data-fieldname="po_limit_warning" style="margin: 15px 0;">' +
							message +
							'</div>'
						);
					} else {
						// Restore the Submit button
						if (frm.page.btn_primary) {
							frm.page.set_primary_action();
						}

						// Add info message showing current limits and remaining amount
						var remaining = per_po_limit - po_amount;
						$(frm.wrapper).find('.form-page').prepend(
							'<div class="alert alert-success" data-fieldname="po_limit_info" style="margin: 15px 0;">' +
							'<strong>✓ Ready to Submit</strong><br>' +
							'<strong>Your Limits:</strong> ' + frappe.format(per_po_limit, {fieldtype: 'Currency'}) + ' per PO, ' +
							frappe.format(per_month_limit, {fieldtype: 'Currency'}) + ' per month<br>' +
							'<strong>This PO:</strong> ' + frappe.format(po_amount, {fieldtype: 'Currency'}) +
							' | <strong>Remaining:</strong> ' + frappe.format(remaining, {fieldtype: 'Currency'}) +
							'</div>'
						);
					}
				}
			}
		});
	},

	company: function(frm) {
		// Re-check limits when company changes
		frm.trigger('refresh');
	},

	base_grand_total: function(frm) {
		// Re-check limits when PO amount changes
		frm.trigger('refresh');
	}
});
