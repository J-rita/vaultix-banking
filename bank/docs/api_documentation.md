# Anti-Gravity Bank API Documentation

## Authentication

### Register
`POST /api/auth/register`
- **Body**: `{username, email, password, first_name, last_name}`
- **Response**: `200 OK`

### Login
`POST /api/auth/login`
- **Body**: `{username, password}`
- **Response**: `{access_token, token_type, role}`

## Accounts

### Create Account
`POST /api/accounts/create`
- **Body**: `{user_id, account_type}`
- **Header**: `Authorization: Bearer <token>`

### Get User Accounts
`GET /api/accounts/user/{user_id}`

## Transactions

### Transfer Funds
`POST /api/transactions/transfer`
- **Body**: `{sender_account_id, receiver_account_number, amount, description}`
- **Features**: Triggers Fraud Detection if amount > $10,000.

### Transaction History
`GET /api/transactions/history/{account_id}`

## Admin

### List All Users
`GET /api/admin/users`

### Update User Status
`POST /api/admin/user/{user_id}/status?status=Active`

### System Analytics
`GET /api/admin/analytics`
