# Gencharge API Documentation

**Version:** 1.0.0

**Generated on:** 2025-11-10 01:41:26


---
GenCharge - A Moblie Recharge Application
---


## `/auth/signup`

### POST: Signup

**Description:** 

**Tags:** Auth


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/auth/verify-otp-signup`

### POST: Verify Otp Signup

**Description:** 

**Tags:** Auth


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/auth/register`

### POST: Register User Route

**Description:** 

**Tags:** Auth


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/auth/login`

### POST: Login

**Description:** 

**Tags:** Auth


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/auth/verify-otp-login`

### POST: Verify Otp Login

**Description:** 

**Tags:** Auth


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/auth/logout`

### POST: Logout

**Description:** 

**Tags:** Auth


**Responses:**

- `200` — Successful Response


---


## `/auth/refresh`

### POST: Refresh Token

**Description:** 

**Tags:** Auth


**Responses:**

- `200` — Successful Response


---


## `/admin/me`

### GET: Get Self Admin

**Description:** 

**Tags:** Admin


**Responses:**

- `200` — Successful Response


---

### PATCH: Update Self Admin

**Description:** 

**Tags:** Admin


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/admin/`

### GET: List Admins

**Description:** 

**Tags:** Admin


**Parameters:**

- `name` (query) — 

- `email` (query) — 

- `phone_number` (query) — 

- `role_name` (query) — 

- `skip` (query) — 

- `limit` (query) — 

- `sort_by` (query) — 

- `sort_order` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### POST: Create Admin

**Description:** 

**Tags:** Admin


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/admin/{admin_id}`

### DELETE: Delete Admin

**Description:** 

**Tags:** Admin


**Parameters:**

- `admin_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### PATCH: Update Admin

**Description:** 

**Tags:** Admin


**Parameters:**

- `admin_id` (path) — 


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/role/`

### GET: List Roles

**Description:** 

**Tags:** Roles


**Parameters:**

- `role_name` (query) — 

- `permission_resource` (query) — 

- `skip` (query) — 

- `limit` (query) — 

- `sort_by` (query) — 

- `sort_order` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### POST: Create Role

**Description:** 

**Tags:** Roles


**Request Body Example:**


**Responses:**

- `201` — Successful Response

- `422` — Validation Error


---


## `/role/{role_id}`

### GET: Get Role

**Description:** 

**Tags:** Roles


**Parameters:**

- `role_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### PUT: Update Role Endpoint

**Description:** 

**Tags:** Roles


**Parameters:**

- `role_id` (path) — 


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### DELETE: Delete Role

**Description:** 

**Tags:** Roles


**Parameters:**

- `role_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/role/permissions/all`

### GET: List Permissions

**Description:** 

**Tags:** Roles


**Responses:**

- `200` — Successful Response


---


## `/user/admin`

### GET: List Users

**Description:** 

**Tags:** Users


**Parameters:**

- `name` (query) — 

- `status` (query) — 

- `user_type` (query) — 

- `skip` (query) — 

- `limit` (query) — 

- `sort_by` (query) — 

- `sort_order` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/user/admin/archived`

### GET: List Archived Users

**Description:** 

**Tags:** Users


**Parameters:**

- `name` (query) — 

- `status` (query) — 

- `user_type` (query) — 

- `skip` (query) — 

- `limit` (query) — 

- `sort_by` (query) — 

- `sort_order` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/user/admin/block/{user_id}`

### POST: Block User

**Description:** 

**Tags:** Users


**Parameters:**

- `user_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/user/admin/unblock/{user_id}`

### POST: Unblock User

**Description:** 

**Tags:** Users


**Parameters:**

- `user_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/user/admin/{user_id}`

### DELETE: Delete User

**Description:** 

**Tags:** Users


**Parameters:**

- `user_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/user/me`

### GET: Get My Info

**Description:** 

**Tags:** Users


**Responses:**

- `200` — Successful Response


---

### DELETE: Delete My Account

**Description:** 

**Tags:** Users


**Responses:**

- `200` — Successful Response


---


## `/user/me/email`

### PUT: Update Email

**Description:** 

**Tags:** Users


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/user/me/switch-type`

### PUT: Switch User Type

**Description:** 

**Tags:** Users


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/user/me/deactivate`

### POST: Deactivate Account

**Description:** 

**Tags:** Users


**Responses:**

- `200` — Successful Response


---


## `/user/me/reactivate`

### POST: Reactivate Account

**Description:** 

**Tags:** Users


**Responses:**

- `200` — Successful Response


---


## `/user/preference`

### GET: Update User Preferences

**Description:** 

**Tags:** Users


**Responses:**

- `200` — Successful Response


---

### PUT: Update User Preferences

**Description:** 

**Tags:** Users


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/plans/plan-group`

### POST: Create Plan Group

**Description:** 

**Tags:** Plans


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### GET: Get Plan Groups

**Description:** 

**Tags:** Plans


**Parameters:**

- `search` (query) — 

- `page` (query) — 

- `limit` (query) — 

- `order_by` (query) — 

- `order_dir` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/plans/plan-group/{group_id}`

### GET: Get Plan Group

**Description:** 

**Tags:** Plans


**Parameters:**

- `group_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### PUT: Update Plan Group

**Description:** 

**Tags:** Plans


**Parameters:**

- `group_id` (path) — 


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### DELETE: Delete Plan Group

**Description:** 

**Tags:** Plans


**Parameters:**

- `group_id` (path) — 


**Responses:**

- `204` — Successful Response

- `422` — Validation Error


---


## `/plans/plan`

### POST: Create Plan

**Description:** 

**Tags:** Plans


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### GET: Get All Plans

**Description:** 

**Tags:** Plans


**Parameters:**

- `search` (query) — 

- `type` (query) — 

- `status` (query) — 

- `page` (query) — 

- `limit` (query) — 

- `order_by` (query) — 

- `order_dir` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/plans/plan/{plan_id}`

### PUT: Update Plan

**Description:** 

**Tags:** Plans


**Parameters:**

- `plan_id` (path) — 


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### DELETE: Delete Plan

**Description:** 

**Tags:** Plans


**Parameters:**

- `plan_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### GET: Get Plan By Id

**Description:** 

**Tags:** Plans


**Parameters:**

- `plan_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/plans/public/all`

### GET: Get Active Plans For Users

**Description:** 

**Tags:** Plans


**Parameters:**

- `search` (query) — 

- `type` (query) — 

- `status` (query) — 

- `page` (query) — 

- `limit` (query) — 

- `order_by` (query) — 

- `order_dir` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/offers/offer_type`

### POST: Create Offer Type

**Description:** 

**Tags:** Offers


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### GET: List Offer Types

**Description:** 

**Tags:** Offers


**Parameters:**

- `search` (query) — 

- `order_by` (query) — 

- `order_dir` (query) — 

- `limit` (query) — 

- `offset` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/offers/offer_type/{offer_type_id}`

### GET: Get Offer Type

**Description:** 

**Tags:** Offers


**Parameters:**

- `offer_type_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### DELETE: Delete Offer Type

**Description:** 

**Tags:** Offers


**Parameters:**

- `offer_type_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/offers/offer_type{offer_type_id}`

### PUT: Update Offer Type

**Description:** 

**Tags:** Offers


**Parameters:**

- `offer_type_id` (path) — 


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/offers/offers/public`

### GET: List Public Offers

**Description:** 

**Tags:** Offers


**Parameters:**

- `search` (query) — 

- `offer_type_id` (query) — 

- `is_special` (query) — 

- `status` (query) — 

- `page` (query) — 

- `limit` (query) — 

- `order_by` (query) — 

- `order_dir` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/offers/offers`

### POST: Create Offer

**Description:** 

**Tags:** Offers


**Request Body Example:**


**Responses:**

- `201` — Successful Response

- `422` — Validation Error


---

### GET: List Offers

**Description:** 

**Tags:** Offers


**Parameters:**

- `search` (query) — 

- `offer_type_id` (query) — 

- `is_special` (query) — 

- `status` (query) — 

- `page` (query) — 

- `limit` (query) — 

- `order_by` (query) — 

- `order_dir` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/offers/offers/{offer_id}`

### PUT: Update Offer

**Description:** 

**Tags:** Offers


**Parameters:**

- `offer_id` (path) — 


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### DELETE: Delete Offer

**Description:** 

**Tags:** Offers


**Parameters:**

- `offer_id` (path) — 


**Responses:**

- `204` — Successful Response

- `422` — Validation Error


---

### GET: Get Offer

**Description:** 

**Tags:** Offers


**Parameters:**

- `offer_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/recharge/subscribe`

### POST: Subscribe

**Description:** 

**Tags:** Recharge


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/recharge/wallet/topup`

### POST: Topup

**Description:** 

**Tags:** Recharge


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/recharge/my/plans`

### GET: My Plans

**Description:** * `sort_by` – `valid_from` or `valid_to`  
* `sort_order` – `asc` or `desc` (default `desc`)

**Tags:** Recharge


**Parameters:**

- `page` (query) — 

- `size` (query) — 

- `plan_id` (query) — 

- `status` (query) — 

- `valid_from_start` (query) — 

- `valid_from_end` (query) — 

- `valid_to_start` (query) — 

- `valid_to_end` (query) — 

- `validity_days_min` (query) — 

- `validity_days_max` (query) — 

- `sort_by` (query) — 

- `sort_order` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/recharge/my/transactions`

### GET: My Transactions

**Description:** Returns a paginated list of **Transaction** with **all** requested filters.

* `size=0` → return **every** matching row (no pagination).  
* All enum fields appear as **dropdowns** in Swagger.  
* Date fields use the **date picker**.

**Tags:** Recharge


**Parameters:**

- `page` (query) — 

- `size` (query) — 

- `category` (query) — 

- `txn_type` (query) — 

- `service_type` (query) — 

- `source` (query) — 

- `status` (query) — 

- `payment_method` (query) — 

- `to_phone_number` (query) — 

- `to_phone_number_like` (query) — 

- `amount_min` (query) — 

- `amount_max` (query) — 

- `created_at_start` (query) — 

- `created_at_end` (query) — 

- `sort_by` (query) — 

- `sort_order` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/recharge/admin/active-plans`

### GET: Admin Active Plans

**Description:** * `sort_by` – `valid_from` or `valid_to`  
* `sort_order` – `asc` or `desc` (default `desc`)

**Tags:** Recharge


**Parameters:**

- `page` (query) — 

- `size` (query) — 

- `phone_number` (query) — 

- `phone_number_like` (query) — 

- `plan_id` (query) — 

- `status` (query) — 

- `valid_from_start` (query) — 

- `valid_from_end` (query) — 

- `valid_to_start` (query) — 

- `valid_to_end` (query) — 

- `validity_days_min` (query) — 

- `validity_days_max` (query) — 

- `sort_by` (query) — 

- `sort_order` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/recharge/admin/transactions`

### GET: Admin Transactions

**Description:** Returns a paginated list of **Transaction** with **all** requested filters.

* `size=0` → return **every** matching row (no pagination).  
* All enum fields appear as **dropdowns** in Swagger.  
* Date fields use the **date picker**.

**Tags:** Recharge


**Parameters:**

- `page` (query) — 

- `size` (query) — 

- `user_id` (query) — 

- `category` (query) — 

- `txn_type` (query) — 

- `service_type` (query) — 

- `source` (query) — 

- `status` (query) — 

- `payment_method` (query) — 

- `from_phone_number` (query) — 

- `from_phone_number_like` (query) — 

- `to_phone_number` (query) — 

- `to_phone_number_like` (query) — 

- `amount_min` (query) — 

- `amount_max` (query) — 

- `created_at_start` (query) — 

- `created_at_end` (query) — 

- `sort_by` (query) — 

- `sort_order` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/autopay/create_autopay`

### POST: Add Autopay

**Description:** 

**Tags:** Autopay


**Request Body Example:**


**Responses:**

- `201` — Successful Response

- `422` — Validation Error


---


## `/autopay/get_autopay/{autopay_id}`

### GET: Get One Autopay

**Description:** 

**Tags:** Autopay


**Parameters:**

- `autopay_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/autopay/get_all_autopay`

### GET: List My Autopays

**Description:** 

**Tags:** Autopay


**Parameters:**

- `page` (query) — 

- `size` (query) — 

- `status` (query) — 

- `phone_number` (query) — 

- `tag` (query) — 

- `sort` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/autopay/{autopay_id}`

### PATCH: Edit Autopay

**Description:** 

**Tags:** Autopay


**Parameters:**

- `autopay_id` (path) — 


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### DELETE: Remove Autopay

**Description:** 

**Tags:** Autopay


**Parameters:**

- `autopay_id` (path) — 


**Responses:**

- `204` — Successful Response

- `422` — Validation Error


---


## `/autopay/admin/all`

### GET: Admin List All

**Description:** 

**Tags:** Autopay


**Parameters:**

- `page` (query) — 

- `size` (query) — 

- `status` (query) — 

- `tag` (query) — 

- `phone_number` (query) — 

- `sort` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/autopay/admin/process-due`

### POST: Admin Process Due

**Description:** Executes all **regular** autopays whose `next_due_date <= now`.
Returns success/failure per autopay.

**Tags:** Autopay


**Responses:**

- `200` — Successful Response


---


## `/referrals/me`

### GET: My Referral History

**Description:** View your own referral earnings (as referrer OR referred)

**Tags:** Referrals


**Parameters:**

- `page` (query) — 

- `size` (query) — 

- `status` (query) — 

- `sort` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/referrals/admin/all`

### GET: Admin Referral History

**Description:** Admin: View all referral rewards in the system

**Tags:** Referrals


**Parameters:**

- `page` (query) — 

- `size` (query) — 

- `status` (query) — 

- `sort` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/notification/announcement`

### POST: Create Announcement

**Description:** 

**Tags:** Notification


**Request Body Example:**


**Responses:**

- `201` — Successful Response

- `422` — Validation Error


---


## `/notification/my`

### GET: Get My Notifications

**Description:** 

**Tags:** Notification


**Responses:**

- `200` — Successful Response


---


## `/notification/delete`

### DELETE: Delete Notification

**Description:** 

**Tags:** Notification


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/contact-from/contacts/`

### POST: Create Contact Endpoint

**Description:** 

**Tags:** Contact-Form


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### GET: List Contacts Endpoint

**Description:** 

**Tags:** Contact-Form


**Parameters:**

- `email` (query) — Filter by email

- `start_date` (query) — Start date for created_at (inclusive)

- `end_date` (query) — End date for created_at (inclusive)

- `order` (query) — Order by created_at: asc or desc


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/contact-from/contacts/{contact_id}/resolved`

### PATCH: Update Resolved Endpoint

**Description:** 

**Tags:** Contact-Form


**Parameters:**

- `contact_id` (path) — 24-character hex MongoDB ObjectId


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/content/admin`

### POST: Admin: Create content

**Description:** 

**Tags:** Content


**Request Body Example:**


**Responses:**

- `201` — Successful Response

- `422` — Validation Error


---

### GET: Admin: List with filters, sort, pagination

**Description:** 

**Tags:** Content


**Parameters:**

- `title` (query) — 

- `created_by` (query) — 

- `updated_by` (query) — 

- `created_at_from` (query) — 

- `created_at_to` (query) — 

- `updated_at_from` (query) — 

- `updated_at_to` (query) — 

- `order_by` (query) — 

- `order_dir` (query) — 

- `page` (query) — 

- `size` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/content/admin/{content_id}`

### PUT: Admin: Edit content

**Description:** 

**Tags:** Content


**Parameters:**

- `content_id` (path) — 


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---

### DELETE: Admin: Delete content

**Description:** 

**Tags:** Content


**Parameters:**

- `content_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/content`

### GET: Users: List public content

**Description:** 

**Tags:** Content


**Parameters:**

- `page` (query) — 

- `size` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/backup/backup/create`

### POST: Create Backup

**Description:** Perform pg_dump backup for specified tables with optional date range filtering.

- Accepts list of tables with optional `date_column`, `start_date`, `end_date`
- Uses existing `get_db()` session
- Returns backup file info on success

**Tags:** Backup, Backup


**Request Body Example:**


**Responses:**

- `201` — Successful Response

- `422` — Validation Error


---


## `/backup/backup/`

### GET: List Backups

**Description:** Retrieve all backup records from the database.

**Tags:** Backup, Backup


**Responses:**

- `200` — Successful Response


---


## `/backup/backup/{backup_id}`

### DELETE: Delete Backup

**Description:** Delete backup record from DB and optionally remove the file.

**Tags:** Backup, Backup


**Parameters:**

- `backup_id` (path) — 


**Responses:**

- `204` — Successful Response

- `422` — Validation Error


---


## `/backup/backup/{backup_id}/restore`

### POST: Restore Backup

**Description:** Restore backup using `pg_restore`. Runs in background.

**Tags:** Backup, Backup


**Parameters:**

- `backup_id` (path) — 


**Request Body Example:**


**Responses:**

- `202` — Successful Response

- `422` — Validation Error


---


## `/reports/admins-report`

### GET: Admin Report

**Description:** 

**Tags:** Reports


**Parameters:**

- `roles` (query) — List of roles to filter by

- `created_from` (query) — Filter users created after this datetime (ISO format)

- `created_to` (query) — Filter users created before this datetime (ISO format)

- `updated_from` (query) — Filter users updated after this datetime (ISO format)

- `updated_to` (query) — Filter users updated before this datetime (ISO format)

- `order_by` (query) — Field to sort by

- `order_dir` (query) — Sort direction: ascending or descending

- `limit` (query) — Number of records to limit

- `offset` (query) — Offset for pagination

- `export_type` (query) — Export file type


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/reports/autopay-report`

### GET: Autopay Report

**Description:** Request body: AutoPayReportFilter (JSON)
Returns JSON list or downloadable file (CSV/Excel/PDF).

**Tags:** Reports


**Parameters:**

- `statuses` (query) — Filter by autopay status (enabled or disabled)

- `tags` (query) — Filter by autopay tag type (onetime or regular)

- `plan_ids` (query) — Filter by one or more plan IDs

- `plan_types` (query) — Filter by plan type (prepaid or postpaid)

- `user_ids` (query) — Filter by one or more user IDs

- `phone_numbers` (query) — Filter by one or more phone numbers

- `next_due_from` (query) — Filter by next due date (from)

- `next_due_to` (query) — Filter by next due date (to)

- `created_from` (query) — Filter by creation date (from)

- `created_to` (query) — Filter by creation date (to)

- `order_by` (query) — Field to order results by

- `order_dir` (query) — Order direction: asc or desc

- `limit` (query) — 0 means no pagination

- `offset` (query) — 0 means no pagination

- `export_type` (query) — Export type for report generation


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/reports/backup-report`

### GET: Backup Report

**Description:** 

**Tags:** Reports


**Parameters:**

- `backup_data` (query) — Filter by backup data type (e.g., product, orders, users)

- `backup_status` (query) — Filter by backup status (failed or success)

- `created_from` (query) — Filter backups created after this datetime (ISO format)

- `created_to` (query) — Filter backups created before this datetime (ISO format)

- `min_size_mb` (query) — Minimum backup size in MB

- `max_size_mb` (query) — Maximum backup size in MB

- `created_by` (query) — Filter backups created by specific user IDs

- `order_by` (query) — Field to order results by

- `order_dir` (query) — Order direction: asc or desc

- `limit` (query) — Limit number of records (0 means no pagination)

- `offset` (query) — Offset for pagination (0 means no pagination)

- `export_type` (query) — Export type for report (none, csv, excel, or pdf)


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/reports/current-active-plans-report`

### GET: Current Active Plans Report

**Description:** 

**Tags:** Reports


**Parameters:**

- `ids` (query) — Filter by plan record IDs

- `user_ids` (query) — Filter by user IDs

- `plan_ids` (query) — Filter by plan IDs

- `phone_numbers` (query) — Filter by phone numbers

- `statuses` (query) — Filter by plan status (active, expired)

- `plan_types` (query) — Filter by plan type (prepaid or postpaid)

- `plan_statuses` (query) — Filter by plan activity status (active or inactive)

- `valid_from_from` (query) — Filter for valid_from >= this datetime (ISO format)

- `valid_from_to` (query) — Filter for valid_from <= this datetime (ISO format)

- `valid_to_from` (query) — Filter for valid_to >= this datetime (ISO format)

- `valid_to_to` (query) — Filter for valid_to <= this datetime (ISO format)

- `order_by` (query) — Field to order the results by

- `order_dir` (query) — Order direction (asc or desc)

- `limit` (query) — Number of records to fetch (0 means no pagination)

- `offset` (query) — Pagination offset (0 means no pagination)

- `export_type` (query) — Export type for the report (none, csv, excel, pdf)


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/reports/offers-report`

### GET: Offers Report

**Description:** Request body: OfferReportFilter
Returns: JSON list or downloadable CSV/Excel/PDF
Pagination will be skipped if either limit==0 or offset==0 (per your requirement).

**Tags:** Reports


**Parameters:**

- `offer_ids` (query) — Filter by one or more offer IDs

- `offer_names` (query) — Filter by one or more offer names

- `is_special` (query) — Filter by whether the offer is special (true/false)

- `offer_type_ids` (query) — Filter by one or more offer type IDs

- `offer_type_names` (query) — Filter by one or more offer type names

- `statuses` (query) — Filter by offer status (active/inactive)

- `created_by` (query) — Filter by IDs of creators

- `created_from` (query) — Filter offers created after this datetime (ISO format)

- `created_to` (query) — Filter offers created before this datetime (ISO format)

- `order_by` (query) — Field to order results by

- `order_dir` (query) — Order direction (asc or desc)

- `limit` (query) — Number of records to limit (0 means no pagination)

- `offset` (query) — Number of records to skip (0 means no pagination)

- `export_type` (query) — Export type for the report (none, csv, excel, pdf)


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/reports/plans-report`

### GET: Plans Report

**Description:** Request body: PlanReportFilter
Returns JSON list or downloadable CSV/Excel/PDF.
Pagination will be skipped if either limit==0 or offset==0.

**Tags:** Reports


**Parameters:**

- `plan_ids` (query) — Filter by plan IDs

- `plan_names` (query) — Filter by plan names

- `name_search` (query) — Case-insensitive partial plan name search

- `min_price` (query) — Minimum plan price

- `max_price` (query) — Maximum plan price

- `min_validity` (query) — Minimum validity in days

- `max_validity` (query) — Maximum validity in days

- `plan_types` (query) — Filter by plan type

- `plan_statuses` (query) — Filter by plan status

- `group_ids` (query) — Filter by plan group IDs

- `group_names` (query) — Filter by plan group names

- `most_popular` (query) — Filter by most popular plans

- `created_by` (query) — Filter by creator user IDs

- `created_from` (query) — Created after this datetime

- `created_to` (query) — Created before this datetime

- `order_by` (query) — 

- `order_dir` (query) — 

- `limit` (query) — 0 means no pagination

- `offset` (query) — 0 means no pagination

- `export_type` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/reports/referral-report`

### GET: Referral Report

**Description:** Request body: ReferralReportFilter
Returns JSON list or a downloadable CSV/Excel/PDF file.
Pagination is applied only when both limit>0 AND offset>0; otherwise pagination is skipped.

**Tags:** Reports


**Parameters:**

- `reward_ids` (query) — Filter by reward IDs

- `referrer_ids` (query) — Filter by referrer IDs

- `referred_ids` (query) — Filter by referred user IDs

- `referrer_phones` (query) — Filter by referrer phone numbers

- `referred_phones` (query) — Filter by referred phone numbers

- `statuses` (query) — Filter by reward status

- `min_amount` (query) — Minimum reward amount

- `max_amount` (query) — Maximum reward amount

- `created_from` (query) — Created after this datetime

- `created_to` (query) — Created before this datetime

- `claimed_from` (query) — Claimed after this datetime

- `claimed_to` (query) — Claimed before this datetime

- `order_by` (query) — 

- `order_dir` (query) — 

- `limit` (query) — 0 means no pagination

- `offset` (query) — 0 means no pagination

- `export_type` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/reports/role-permission-report`

### GET: Role Permissions Report

**Description:** Generates Role Permissions report with filters, ordering, pagination, and export options.
Pagination applies only when both limit>0 and offset>0.

**Tags:** Reports


**Parameters:**

- `role_permission_ids` (query) — Filter by role-permission IDs

- `role_ids` (query) — Filter by role IDs

- `permission_ids` (query) — Filter by permission IDs

- `role_names` (query) — Filter by role names

- `resources` (query) — Filter by resource names

- `read` (query) — Filter by read access

- `write` (query) — Filter by write access

- `edit` (query) — Filter by edit access

- `delete` (query) — Filter by delete access

- `order_by` (query) — 

- `order_dir` (query) — 

- `limit` (query) — 0 means no pagination

- `offset` (query) — 0 means no pagination

- `export_type` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/reports/sessions-report`

### GET: Sessions Report

**Description:** Request body: SessionsReportFilter
Returns JSON list or downloadable CSV/Excel/PDF.
Pagination is skipped if either limit==0 or offset==0 (i.e., applied only when limit>0 and offset>0).

**Tags:** Reports


**Parameters:**

- `session_ids` (query) — Filter by session UUIDs

- `user_ids` (query) — Filter by user IDs

- `is_active` (query) — Filter by session activity state

- `jtis` (query) — Filter by JWT IDs (JTI)

- `refresh_tokens_contains` (query) — Filter refresh tokens containing substring

- `refresh_expires_from` (query) — Refresh token expires after this datetime

- `refresh_expires_to` (query) — Refresh token expires before this datetime

- `login_time_from` (query) — Login time after this datetime

- `login_time_to` (query) — Login time before this datetime

- `last_active_from` (query) — Last active after this datetime

- `last_active_to` (query) — Last active before this datetime

- `revoked_from` (query) — Revoked after this datetime

- `revoked_to` (query) — Revoked before this datetime

- `order_by` (query) — 

- `order_dir` (query) — 

- `limit` (query) — 0 means no pagination

- `offset` (query) — 0 means no pagination

- `export_type` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/reports/transactions-report`

### GET: Transactions Report

**Description:** Request body: TransactionsReportFilter
Returns JSON list or downloadable CSV/Excel/PDF.
Pagination is skipped if either limit==0 or offset==0 (i.e., applied only when limit>0 and offset>0).

**Tags:** Reports


**Parameters:**

- `txn_ids` (query) — Filter by transaction IDs

- `user_ids` (query) — Filter by user IDs

- `categories` (query) — Filter by transaction category

- `txn_types` (query) — Filter by transaction type

- `min_amount` (query) — Minimum transaction amount

- `max_amount` (query) — Maximum transaction amount

- `service_types` (query) — Filter by service type

- `plan_ids` (query) — Filter by plan IDs

- `offer_ids` (query) — Filter by offer IDs

- `from_phone_numbers` (query) — Filter by sender phone numbers

- `to_phone_numbers` (query) — Filter by receiver phone numbers

- `sources` (query) — Filter by transaction source

- `statuses` (query) — Filter by transaction status

- `payment_methods` (query) — Filter by payment method

- `payment_transaction_id_contains` (query) — Search substring in payment transaction ID

- `created_from` (query) — Created after this datetime

- `created_to` (query) — Created before this datetime

- `order_by` (query) — 

- `order_dir` (query) — 

- `limit` (query) — 0 means no pagination

- `offset` (query) — 0 means no pagination

- `export_type` (query) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/reports/archived-users-report`

### GET: Users Archive Report

**Description:** Request body: UsersArchiveFilter
Returns JSON list or downloadable CSV/Excel/PDF.
Pagination is applied only when both limit>0 and offset>0. Otherwise returns all results / exports all results.

**Tags:** Reports


**Parameters:**

- `user_ids` (query) — Filter by user IDs

- `name_search` (query) — Partial case-insensitive name search

- `emails` (query) — Filter by user emails

- `phone_numbers` (query) — Filter by phone numbers

- `user_types` (query) — Filter by user type

- `statuses` (query) — Filter by user status

- `min_wallet` (query) — Minimum wallet balance

- `max_wallet` (query) — Maximum wallet balance

- `created_from` (query) — Filter users created after this datetime

- `created_to` (query) — Filter users created before this datetime

- `deleted_from` (query) — Filter users deleted after this datetime

- `deleted_to` (query) — Filter users deleted before this datetime

- `order_by` (query) — Field to order by

- `order_dir` (query) — Sort order (asc/desc)

- `limit` (query) — 0 means no pagination

- `offset` (query) — 0 means no pagination

- `export_type` (query) — Export format


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/reports/users-report`

### GET: Users Report

**Description:** Request body: UsersReportFilter
Returns JSON list or downloadable CSV/Excel/PDF.
Pagination applied only when both limit>0 and offset>0. Otherwise skip pagination.

**Tags:** Reports


**Parameters:**

- `user_ids` (query) — Filter by user IDs

- `name_search` (query) — Case-insensitive partial match on name

- `emails` (query) — Filter by user emails

- `phone_numbers` (query) — Filter by phone numbers

- `user_types` (query) — Filter by user type

- `statuses` (query) — Filter by status

- `min_wallet` (query) — Minimum wallet balance

- `max_wallet` (query) — Maximum wallet balance

- `created_from` (query) — Filter users created after this datetime

- `created_to` (query) — Filter users created before this datetime

- `updated_from` (query) — Filter users updated after this datetime

- `updated_to` (query) — Filter users updated before this datetime

- `order_by` (query) — Field to order by

- `order_dir` (query) — Sort direction

- `limit` (query) — 0 means no pagination

- `offset` (query) — 0 means no pagination

- `export_type` (query) — Export format


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/reports/me/transactions-report`

### GET: Transactions Report

**Description:** Request body: TransactionsReportFilter
Returns JSON list or downloadable CSV/Excel/PDF.
Pagination is skipped if either limit==0 or offset==0 (i.e., applied only when limit>0 and offset>0).

**Tags:** Reports


**Parameters:**

- `txn_ids` (query) — Filter by transaction IDs

- `categories` (query) — Filter by category (wallet/service)

- `txn_types` (query) — Filter by transaction type

- `min_amount` (query) — Minimum transaction amount

- `max_amount` (query) — Maximum transaction amount

- `service_types` (query) — Filter by service type

- `plan_ids` (query) — Filter by plan IDs

- `offer_ids` (query) — Filter by offer IDs

- `to_phone_numbers` (query) — Filter by recipient phone numbers

- `sources` (query) — Filter by transaction source

- `statuses` (query) — Filter by status

- `payment_methods` (query) — Filter by payment method

- `payment_transaction_id_contains` (query) — Search substring in payment transaction ID

- `created_from` (query) — Filter transactions created after this datetime

- `created_to` (query) — Filter transactions created before this datetime

- `order_by` (query) — Field to order results by

- `order_dir` (query) — Sort direction

- `limit` (query) — 0 means no pagination

- `offset` (query) — 0 means no pagination

- `export_type` (query) — Export format for report


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/analytics/admins`

### GET: Get Admins Report

**Description:** 

**Tags:** Analytics


**Responses:**

- `200` — Successful Response


---


## `/analytics/backup`

### GET: Get Backups Report

**Description:** 

**Tags:** Analytics


**Responses:**

- `200` — Successful Response


---


## `/analytics/current-active-plans`

### GET: Get Current Active Plans Report

**Description:** 

**Tags:** Analytics


**Responses:**

- `200` — Successful Response


---


## `/analytics/offers`

### GET: Get Offers Report

**Description:** 

**Tags:** Analytics


**Responses:**

- `200` — Successful Response


---


## `/analytics/plans`

### GET: Get Plans Report

**Description:** 

**Tags:** Analytics


**Responses:**

- `200` — Successful Response


---


## `/analytics/referrals`

### GET: Get Referrals Report

**Description:** 

**Tags:** Analytics


**Responses:**

- `200` — Successful Response


---


## `/analytics/transactions`

### GET: Get Transactions Report

**Description:** 

**Tags:** Analytics


**Responses:**

- `200` — Successful Response


---


## `/analytics/users-archive`

### GET: Get Users Archive Report

**Description:** 

**Tags:** Analytics


**Responses:**

- `200` — Successful Response


---


## `/analytics/users`

### GET: Get Users Report

**Description:** Returns a comprehensive users report with counts, trends, distributions and growth rates.

**Tags:** Analytics


**Responses:**

- `200` — Successful Response


---


## `/analytics/me/users`

### GET: Get User Insights

**Description:** 

**Tags:** Analytics


**Responses:**

- `200` — Successful Response


---


## `/test/admin/stats`

### GET: Get Admin Dashboard

**Description:** 

**Tags:** Testing


**Responses:**

- `200` — Successful Response


---


## `/test/api/content`

### POST: Create Content with Embedded Image Upload

**Description:** Receives content details (title, body) and the image file in a single
multipart/form-data request, saves the image, and links the content.

**Tags:** Testing


**Request Body Example:**


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---


## `/test/api/content/{content_id}`

### DELETE: Delete Content and Associated Image

**Description:** 

**Tags:** Testing


**Parameters:**

- `content_id` (path) — 


**Responses:**

- `200` — Successful Response

- `422` — Validation Error


---
