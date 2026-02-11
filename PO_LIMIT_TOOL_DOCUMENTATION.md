# PO Submission Limit Tool - Documentation

**Version:** 1.0.0
**App:** po (PO Limiter)
**Last Updated:** February 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Installation & Setup](#installation--setup)
5. [User Guide](#user-guide)
6. [Managing Director Guide](#managing-director-guide)
7. [Technical Reference](#technical-reference)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)
10. [File Structure](#file-structure)

---

## Overview

The PO Submission Limit Tool enforces management approval by ensuring that no purchase user can submit a Purchase Order (PO) unless the Managing Director (MD) explicitly grants a submission limit.

### Key Principles

- **Default Deny:** All new users have submission rights revoked by default
- **Explicit Approval:** MD must explicitly grant PO submission limits
- **Dual Limits:** Enforces both Per-PO and Per-Month limits
- **Session-Based Validation:** Validates against the current logged-in user (`frappe.session.user`)
- **Transparent Tracking:** Monthly usage is tracked and visible to MD

---

## Features

### For End Users

- ✅ Create and edit Purchase Orders
- ✅ Save POs as Draft
- ❌ Submit POs (without MD approval)
- 📝 Request PO limit increases
- 📊 View current submission limits

### For Managing Directors

- 👥 View all purchase users
- 💰 Assign per-PO and per-month limits
- ⚖️ Approve/reject limit increase requests
- 📈 Track monthly usage per user
- 🔒 Revoke limits at any time
- 📋 View all limits in a centralized table

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         COMPONENT ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   USER PO LIMIT      │ ← Stores submission limits per user/company
│   (DocType)          │
└──────────────────────┘
           │
           │ validates
           ▼
┌──────────────────────┐
│   Purchase Order     │ ← Submit button controlled by limits
└──────────────────────┘
           │
           │ requests
           ▼
┌──────────────────────────┐
│ PO Limit Increase Request│ ← Users request higher limits
│   (DocType)              │
└──────────────────────────┘
           │
           │ approves
           ▼
┌──────────────────────┐
│  PO Limiter Tool     │ ← MD manages limits
│    (Page)            │
└──────────────────────┘
```

### Data Flow

```
User Creates PO → Client Checks Limit → Server Validates on Submit → Usage Updated
     ↓                 ↓                         ↓                        ↓
  Draft Only     Show/Hide Button      Block/Allow Submit         Update Counter
```

---

## Installation & Setup

### Prerequisites

- Frappe/ERPNext installed
- `po` app installed in bench
- Administrator access

### Step 1: Install the App

```bash
cd /path/to/frappe-bench
bench get-app po https://github.com/your-org/po  # or local path
bench install-app po
bench build
bench restart
```

### Step 2: Create "Managing Director" Role

```bash
bench --site your-site console
```

```python
# Create the MD role
md_role = frappe.get_doc({
    "doctype": "Role",
    "role_name": "Managing Director",
    "desk_access": 1,
    "is_custom": 1
})
md_role.insert()

# Assign to MD user
frappe.get_doc("User", "md@example.com").append_roles("Managing Director")

exit()
```

### Step 3: Verify Installation

```bash
bench --site your-site migrate
bench build
```

### Step 4: Access the Tool

- Navigate to: `http://your-site/app/po_limiter`
- Only accessible to users with "Managing Director" or "System Manager" role

---

## User Guide

### Default Behavior (New Users)

When a new user is created with PO creation access:

| Action | Allowed |
|--------|---------|
| Create PO | ✅ Yes |
| Edit PO | ✅ Yes |
| Save as Draft | ✅ Yes |
| Submit PO | ❌ **No** - Submit button hidden |

### Understanding Limits

#### Per PO Limit
The maximum amount allowed for a single Purchase Order.

**Example:** If Per PO Limit = $50,000
- PO for $30,000 → ✅ Allowed
- PO for $75,000 → ❌ Blocked

#### Per Month Limit
The maximum total amount allowed across all POs in a calendar month.

**Example:** If Per Month Limit = $200,000
- Submitted this month: $150,000
- Try to submit PO for $60,000 → ❌ Blocked (total would be $210,000)

### Requesting a Limit Increase

1. Click "Request Limit" button in the warning message
2. Fill in the "PO Limit Increase Request" form:
   - Requested Per PO Limit
   - Requested Per Month Limit
   - Reason for increase
3. Submit → Status changes to "Pending Approval"
4. MD will review and approve/reject

---

## Managing Director Guide

### Accessing the PO Limiter Tool

**URL:** `http://your-site/app/po_limiter`

**Roles Required:** Managing Director or System Manager

### Tool Features

#### 1. Pending Requests Section

Displays all pending limit increase requests with:
- User name
- Company
- Requested limits
- Reason
- Actions: Approve / Reject / View Details

#### 2. By User Tab

Quickly assign or update limits for a specific user:

1. Select User from dropdown
2. Select Company
3. Set:
   - **Status:** Active or Revoked
   - **Per PO Limit:** Maximum per PO (e.g., 50000)
   - **Per Month Limit:** Maximum per month (e.g., 200000)
4. Click "Save Limit"

#### 3. All Limits Tab

View all user limits in a table with:
- User
- Company
- Status (Active/Revoked)
- Per PO Limit
- Per Month Limit
- Current Monthly Usage
- Last Updated By
- Last Updated Date
- Actions: Edit

### Approval Workflow

```
User Submits Request → Status: Pending Approval
                            ↓
                    MD Reviews Request
                            ↓
                ┌───────────┴───────────┐
                │                       │
            Approve                 Reject
                │                       │
                ▼                       ▼
        Status: Approved          Status: Rejected
        Limits Updated           Rejection Reason Required
        User Notified            User Notified
```

### Best Practices

1. **Start Conservative:** Assign lower limits initially, increase as needed
2. **Monitor Usage:** Review monthly usage regularly
3. **Set Appropriate Limits:** Consider role and seniority
4. **Document Decisions:** Users provide reasons, keep records of approvals
5. **Regular Reviews:** Periodically review and adjust limits

---

## Technical Reference

### Validation Logic

#### Client-Side (JavaScript)
**File:** `apps/po/po/po_limiter/purchase_order_client.js`

```javascript
// Checks on PO form refresh
frappe.call({
    method: 'po.po_limiter.po_validation.get_user_po_limit_status',
    args: {
        user: frappe.session.user,  // Current logged-in user
        company: frm.doc.company
    },
    callback: function(r) {
        if (r.message.status === 'Revoked' || r.message.per_po_limit <= 0) {
            // Hide submit button, show warning
        } else {
            // Show submit button, display limits
        }
    }
});
```

#### Server-Side (Python)
**File:** `apps/po/po/po_limiter/po_validation.py`

```python
def validate_po_limits(doc, method=None):
    """
    Validates PO submission against current user's limits.
    Uses frappe.session.user (not doc.owner)
    """
    user = frappe.session.user  # Current logged-in user
    company = doc.company
    po_amount = flt(doc.base_grand_total)

    # Get user's limits
    user_limit = get_user_po_limit(user, company)

    # Check 1: No limit assigned
    if not user_limit:
        frappe.throw("PO submission requires MD approval.")

    # Check 2: Status is Revoked
    if user_limit.status == "Revoked":
        frappe.throw("PO submission requires MD approval.")

    # Check 3: PO amount > Per PO Limit
    if po_amount > user_limit.per_po_limit:
        frappe.throw("PO amount exceeds your approved submission limit.")

    # Check 4: Monthly limit exceeded
    if method == "on_submit":
        monthly_usage = get_monthly_po_usage(user, company)
        if (monthly_usage + po_amount) > user_limit.per_month_limit:
            frappe.throw("PO amount exceeds your approved submission limit.")

    # Update monthly usage
    update_monthly_usage(user_limit.name, monthly_usage + po_amount)
```

### Document Events

| Event | Hook | Function | Purpose |
|-------|------|----------|---------|
| User.after_insert | User Hooks | `create_default_po_limit()` | Creates default zero limit for new users |
| PO.validate | Doc Events | `validate_po_limits()` | Pre-submit validation check |
| PO.on_submit | Doc Events | `validate_po_limits()` | Final validation + usage update |
| PO.on_cancel | Doc Events | `update_monthly_usage_on_po_cancel()` | Subtract from monthly usage |

### Permission Model

#### User PO Limit DocType

| Role | Create | Read | Write | Delete | Submit |
|------|--------|------|-------|--------|--------|
| Managing Director | ✅ | ✅ | ✅ | ✅ | N/A |
| System Manager | ✅ | ✅ | ✅ | ✅ | N/A |
| All Users | ❌ | ✅ | ❌ | ❌ | N/A |

#### PO Limit Increase Request DocType

| Role | Create | Read | Write | Delete | Submit |
|------|--------|------|-------|--------|--------|
| Managing Director | ✅ | ✅ | ✅ | ✅ | ✅ |
| System Manager | ✅ | ✅ | ✅ | ✅ | ✅ |
| All Users | ✅ | ✅ | ✅ (own) | ✅ (own) | ✅ (submit for approval) |

#### PO Limiter Page

| Role | Access |
|------|--------|
| Managing Director | ✅ |
| System Manager | ✅ |
| All Users | ❌ |

---

## API Reference

### Whitelisted Functions

#### `get_user_po_limit_status(user, company)`

Get a user's PO limit status for client-side validation.

**Parameters:**
- `user` (str): User email/ID
- `company` (str): Company name

**Returns:**
```json
{
    "status": "Active",
    "per_po_limit": 50000,
    "per_month_limit": 200000
}
```

**Used by:** Purchase Order client script

---

#### `approve_request(request_name)`

Approve a PO limit increase request.

**Parameters:**
- `request_name` (str): Name of the PO Limit Increase Request

**Returns:** Success message

**Used by:** PO Limiter page (Approve button)

---

#### `reject_request(request_name, rejection_reason)`

Reject a PO limit increase request.

**Parameters:**
- `request_name` (str): Name of the PO Limit Increase Request
- `rejection_reason` (str): Reason for rejection

**Returns:** Success message

**Used by:** PO Limiter page (Reject button)

---

#### `update_user_limit(user, company, per_po_limit, per_month_limit, status)`

Update or create a user's PO limit.

**Parameters:**
- `user` (str): User email/ID
- `company` (str): Company name
- `per_po_limit` (float): Per PO limit amount
- `per_month_limit` (float): Per month limit amount
- `status` (str): "Active" or "Revoked"

**Returns:**
```json
{
    "success": True
}
```

**Used by:** PO Limiter page (Save Limit button)

---

#### `get_user_limit_details(user, company)`

Get detailed limit information for a user.

**Parameters:**
- `user` (str): User email/ID
- `company` (str): Company name

**Returns:**
```json
{
    "name": "limit-record-name",
    "per_po_limit": 50000,
    "per_month_limit": 200000,
    "status": "Active",
    "monthly_usage": 75000,
    "last_reset_date": "2026-02-01",
    "last_updated_by": "md@example.com",
    "last_updated_date": "2026-02-10 10:30:00"
}
```

**Used by:** PO Limiter page (Edit button)

---

#### `get_purchase_users()`

Get all users who have access to create Purchase Orders.

**Returns:** Array of user objects with name, full_name, email

**Used by:** PO Limiter page

---

#### `get_all_user_limits()`

Get all user PO limits.

**Returns:** Array of all User PO Limit records

**Used by:** PO Limiter page (All Limits tab)

---

#### `get_pending_limit_requests()`

Get all pending PO limit increase requests.

**Returns:** Array of pending PO Limit Increase Request records

**Used by:** PO Limiter page (Pending Requests section)

---

## Troubleshooting

### Issue: Submit button not showing for users with limits

**Possible Causes:**
1. Status is "Revoked" instead of "Active"
2. Per PO Limit is 0
3. Client cache needs refresh

**Solutions:**
```python
# Check user's limit status
bench --site your-site console

limit = frappe.get_doc("User PO Limit", {"user": "user@example.com", "company": "Your Company"})
print(f"Status: {limit.status}")
print(f"Per PO Limit: {limit.per_po_limit}")
```

### Issue: Validation not working

**Check hooks are registered:**
```bash
bench --site your-site console
frappe.get_hooks("doc_events")
```

Look for:
```python
"Purchase Order": {
    "validate": "po.po_limiter.po_validation.validate_po_limits",
    "on_submit": "po.po_limiter.po_validation.validate_po_limits"
}
```

### Issue: MD cannot access PO Limiter page

**Check user has MD role:**
```python
bench --site your-site console

user = frappe.get_doc("User", "md@example.com")
print(user.roles)  # Should include "Managing Director"
```

### Issue: Monthly usage not updating

**Check the reset date:**
```python
limit = frappe.get_doc("User PO Limit", {"user": "user@example.com"})
print(f"Last Reset: {limit.last_reset_date}")
```

Monthly usage resets automatically when the month changes.

### Issue: "ModuleNotFoundError: No module named 'po.user_po_limit'"

This is a sync issue. Run:
```bash
bench --site your-site migrate
bench build --app po
bench restart
```

---

## File Structure

```
apps/po/
├── po/
│   ├── po_limiter/
│   │   ├── doctype/
│   │   │   ├── user_po_limit/
│   │   │   │   ├── user_po_limit.json          # DocType definition
│   │   │   │   ├── user_po_limit.py            # Controller
│   │   │   │   └── __init__.py
│   │   │   └── po_limit_increase_request/
│   │   │       ├── po_limit_increase_request.json  # DocType definition
│   │   │       ├── po_limit_increase_request.py    # Controller
│   │   │       ├── po_limit_increase_request.js    # Client script
│   │   │       └── __init__.py
│   │   ├── page/
│   │   │   └── po_limiter/
│   │   │       ├── po_limiter.py                # Page server logic
│   │   │       ├── po_limiter.html              # Page template
│   │   │       ├── po_limiter.js                # Page client logic
│   │   │       ├── po_limiter.json              # Page definition
│   │   │       └── __init__.py
│   │   ├── po_validation.py                     # Main validation logic
│   │   ├── purchase_order_client.js             # PO form client script
│   │   ├── user_hooks.py                        # User creation hooks
│   │   ├── utils.py                             # Utility functions
│   │   └── __init__.py
│   ├── public/
│   │   └── css/
│   │       └── po_limiter.css                   # Page styles
│   ├── config/
│   │   └── desktop.py                           # Desktop icons
│   ├── hooks.py                                 # App hooks
│   ├── modules.txt                              # Module definitions
│   ├── patches.txt                              # Patches
│   ├── __init__.py
│   ├── app_name.py
│   ├── app_title.py
│   ├── app_description.py
│   ├── app_publisher.py
│   ├── app_email.py
│   ├── app_license.py
│   └── setup.py
├── licenses/
├── .gitignore
├── README.md
├── LICENSE
├── requirements.txt
└── pyproject.toml
```

---

## Database Schema

### User PO Limit (`tabUser PO Limit`)

| Field | Type | Required | Default |
|-------|------|----------|---------|
| name | Link | Yes | Auto |
| user | Link | Yes | |
| company | Link | Yes | |
| status | Select | Yes | Revoked |
| per_po_limit | Currency | No | 0 |
| per_month_limit | Currency | No | 0 |
| monthly_usage | Currency | No | 0 |
| last_reset_date | Date | No | Today |
| last_updated_by | Link | No | |
| last_updated_date | Datetime | No | |

### PO Limit Increase Request (`tabPO Limit Increase Request`)

| Field | Type | Required | Default |
|-------|------|----------|---------|
| name | Link | Yes | Auto |
| user | Link | Yes | Owner |
| company | Link | Yes | |
| current_per_po_limit | Currency | No | 0 (Read Only) |
| current_per_month_limit | Currency | No | 0 (Read Only) |
| requested_per_po_limit | Currency | Yes | |
| requested_per_month_limit | Currency | Yes | |
| reason | Text | Yes | |
| status | Select | Yes | Draft |
| approved_by | Link | No | (Read Only) |
| approval_date | Datetime | No | (Read Only) |
| rejection_reason | Text | No | |
| amended_from | Link | No | |

---

## Changelog

### Version 1.0.0 (February 2026)
- Initial release
- User PO Limit DocType
- PO Limit Increase Request DocType
- PO Limiter Tool page for MD
- Client-side submit button control
- Server-side validation
- Monthly usage tracking
- Per-PO and per-month limits

---

## Support

For issues, questions, or contributions:

- **App Repository:** `https://github.com/your-org/po`
- **Documentation:** `README.md`
- **Issue Tracker:** GitHub Issues

---

## License

MIT License - See LICENSE file for details

---

**Copyright (c) 2026, Lassod**
