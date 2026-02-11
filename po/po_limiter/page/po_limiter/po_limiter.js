// Copyright (c) 2026, Lassod
// License: MIT

frappe.pages['po-limiter'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'PO Limiter Tool',
		single_column: true
	});

	// Load the HTML content
	$(page.main).find('.page-content').html(
		frappe.render_template('po_limiter', {
			companies: [],
			users: [],
			user_limits: [],
			pending_requests: []
		})
	);

	// Load initial data
	load_data(page);

	// Setup event handlers
	setup_event_handlers(page);
};

function load_data(page) {
	// Show loading
	page.main.find('.po-limiter-container').html('<div class="text-center">Loading...</div>');

	// Get data from server
	frappe.call({
		method: 'po.po_limiter.page.po_limiter.po_limiter.get_context',
		args: {},
		callback: function(r) {
			if (r.message) {
				// Re-render with data
				var context = r.message;
				$(page.main).find('.po-limiter-container').replaceWith(
					frappe.render_template('po_limiter', context)
				);

				// Re-setup event handlers after re-render
				setup_event_handlers(page);
			}
		}
	});
}

function setup_event_handlers(page) {
	var container = page.main.find('.po-limiter-container');

	// User selection change
	container.find('#user-select').on('change', function() {
		var user = $(this).val();
		if (user) {
			// Show company selection
			container.find('.company-selection').show();

			// Store selected user
			container.data('selected-user', user);
		} else {
			container.find('.company-selection').hide();
			container.find('#limit-editor').hide();
		}
	});

	// Company selection change
	container.find('#company-select').on('change', function() {
		var user = container.data('selected-user');
		var company = $(this).val();

		if (user && company) {
			// Load user's current limit
			load_user_limit(user, company);
		} else {
			container.find('#limit-editor').hide();
		}
	});

	// Save limit button
	container.find('#save-limit-btn').on('click', function() {
		var user = container.data('selected-user');
		var company = container.find('#company-select').val();
		var status = container.find('#limit-status').val();
		var per_po_limit = container.find('#per-po-limit').val();
		var per_month_limit = container.find('#per-month-limit').val();

		if (!user || !company) {
			frappe.msgprint('Please select a user and company');
			return;
		}

		// Save limit
		frappe.call({
			method: 'po.po_limiter.page.po_limiter.po_limiter.update_user_limit',
			args: {
				user: user,
				company: company,
				per_po_limit: per_po_limit,
				per_month_limit: per_month_limit,
				status: status
			},
			callback: function(r) {
				if (r.message && r.message.success) {
					// Reload data
					load_data(page);
				}
			}
		});
	});

	// Reset button
	container.find('#reset-limit-btn').on('click', function() {
		container.find('#limit-status').val('Active');
		container.find('#per-po-limit').val('0');
		container.find('#per-month-limit').val('0');
		container.find('#current-usage').hide();
	});

	// Edit limit from all limits table
	container.find('.btn-edit-limit').on('click', function() {
		var user = $(this).data('user');
		var company = $(this).data('company');

		// Switch to by-user tab
		container.find('a[href="#by-user"]').tab('show');

		// Set user and company
		container.find('#user-select').val(user);
		container.data('selected-user', user);
		container.find('.company-selection').show();
		container.find('#company-select').val(company);

		// Load limit details
		load_user_limit(user, company);
	});

	// Approve request button
	container.find('.btn-approve').on('click', function() {
		var request_name = $(this).data('request');

		frappe.confirm('Approve this limit increase request?', function() {
			frappe.call({
				method: 'po.po_limiter.doctype.po_limit_increase_request.po_limit_increase_request.approve_request',
				args: {
					request_name: request_name
				},
				callback: function(r) {
					if (r.message) {
						load_data(page);
					}
				}
			});
		});
	});

	// Reject request button
	container.find('.btn-reject').on('click', function() {
		var request_name = $(this).data('request');

		frappe.prompt([
			{
				fieldname: 'reason',
				fieldtype: 'Text',
				label: 'Rejection Reason',
				reqd: 1
			}
		], function(values) {
			frappe.call({
				method: 'po.po_limiter.doctype.po_limit_increase_request.po_limit_increase_request.reject_request',
				args: {
					request_name: request_name,
					rejection_reason: values.reason
				},
				callback: function(r) {
					if (r.message) {
						load_data(page);
					}
				}
			});
		}, 'Reject Request', 'Reject');
	});
}

function load_user_limit(user, company) {
	var container = $('.po-limiter-container');

	frappe.call({
		method: 'po.po_limiter.page.po_limiter.po_limiter.get_user_limit_details',
		args: {
			user: user,
			company: company
		},
		callback: function(r) {
			if (r.message) {
				var limit = r.message;

				// Populate form
				container.find('#limit-status').val(limit.status || 'Active');
				container.find('#per-po-limit').val(limit.per_po_limit || 0);
				container.find('#per-month-limit').val(limit.per_month_limit || 0);

				// Show current usage
				if (limit.monthly_usage) {
					container.find('#monthly-usage').text(
						frappe.format(limit.monthly_usage, {fieldtype: 'Currency'})
					);
					container.find('#current-usage').show();
				}

				container.find('#limit-editor').show();
			} else {
				// No existing limit - show empty form
				container.find('#limit-status').val('Active');
				container.find('#per-po-limit').val(0);
				container.find('#per-month-limit').val(0);
				container.find('#current-usage').hide();
				container.find('#limit-editor').show();
			}
		}
	});
}
