# Carvo API Documentation

## API Base URL
```
/api/v1/
```

---

## Authentication Endpoints

### 1. Get Access Token (Login)
**Endpoint:** `POST /api/v1/token/`

**Authentication:** No

**Description:** Authenticate user and obtain JWT access and refresh tokens.

**Request Body:**
```json
{
    "username": "john_doe",
    "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "username": "john_doe",
    "email": "john@example.com"
}
```

**Error Response (401 Unauthorized):**
```json
{
    "detail": "Account is not activated. Please check your email for the activation link."
}
```

---

### 2. Refresh Access Token
**Endpoint:** `POST /api/v1/token/refresh/`

**Authentication:** No

**Description:** Refresh expired access token using refresh token.

**Request Body:**
```json
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 3. Register New Account
**Endpoint:** `POST /api/v1/register/`

**Authentication:** No

**Description:** Create a new user account. Activation email will be sent automatically.

**Request Body:**
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!"
}
```

**Validation Rules:**
- Username: Required, unique
- Email: Required, valid email format, unique
- Password: Minimum 8 characters, at least one uppercase, one lowercase, one digit, one special character

**Response (201 Created):**
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
}
```

**Error Response (400 Bad Request):**
```json
{
    "username": ["A user with that username already exists."],
    "email": ["user with this email address already exists."],
    "password": ["Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)."]
}
```

---

### 4. Activate Account
**Endpoint:** `GET /api/v1/activate/?token=<activation_token>`

**Authentication:** No

**Description:** Activate user account using token sent via email.

**Query Parameters:**
- `token` (required): Activation token received in email

**Response (200 OK):**
```json
{
    "detail": "Account activated successfully. You can now log in."
}
```

**Error Response (400 Bad Request):**
```json
{
    "detail": "Activation link has expired."
}
```

or

```json
{
    "detail": "Invalid activation token."
}
```

---

## Car Endpoints

### 5. List Available Cars
**Endpoint:** `GET /api/v1/cars/`

**Authentication:** Required (JWT Token)

**Description:** List all available cars with pagination. Optionally filter by date range.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 9, max: 100)
- `start_date` (optional): Filter cars available from this date (format: YYYY-MM-DD)
- `end_date` (optional): Filter cars available until this date (format: YYYY-MM-DD)

**Response (200 OK):**
```json
{
    "count": 15,
    "next": "http://api.example.com/api/v1/cars/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Honda Civic",
            "slug": "honda-civic",
            "brand": "Honda",
            "model_year": 2023,
            "car_type": "sedan",
            "seats": 5,
            "price_per_day": 50.00,
            "is_available": true,
            "image": "https://example.com/images/civic.jpg"
        }
    ]
}
```

---

### 6. Get Car Details
**Endpoint:** `GET /api/v1/car-detail/<slug>/`

**Authentication:** Required (JWT Token)

**Description:** Get detailed information about a specific car.

**URL Parameters:**
- `slug` (required): Car slug identifier

**Response (200 OK):**
```json
{
    "id": 1,
    "name": "Honda Civic",
    "brand": "Honda",
    "model_year": 2023,
    "car_type": "sedan",
    "transmission": "automatic",
    "fuel_type": "petrol",
    "fuel": 75,
    "seats": 5,
    "price_per_day": 50.00,
    "is_available": true,
    "description": "A reliable and fuel-efficient sedan",
    "created_at": "2023-01-15T10:30:00Z",
    "images": [
        {
            "id": 1,
            "image": "https://example.com/images/civic-1.jpg"
        },
        {
            "id": 2,
            "image": "https://example.com/images/civic-2.jpg"
        }
    ],
    "current_branch": {
        "id": 1,
        "city": "Karachi",
        "address": "123 Main Street, Karachi",
        "is_active": true
    }
}
```

**Error Response (404 Not Found):**
```json
{
    "detail": "Not found."
}
```

---

## Branch Endpoints

### 7. List All Branches
**Endpoint:** `GET /api/v1/branch-list/`

**Authentication:** Required (JWT Token)

**Description:** List all active branches.

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "city": "Karachi",
        "address": "123 Main Street, Karachi",
        "is_active": true
    },
    {
        "id": 2,
        "city": "Lahore",
        "address": "456 Liberty Road, Lahore",
        "is_active": true
    }
]
```

---

## Rental Endpoints

### 8. Create Rental
**Endpoint:** `POST /api/v1/rental/`

**Authentication:** Required (JWT Token)

**Description:** Create a new rental booking.

**Request Body:**
```json
{
    "car_id": 1,
    "start_date": "2024-06-10",
    "end_date": "2024-06-15",
    "dropoff_branch_id": 2
}
```

**Validation Rules:**
- `car_id`: Must be a valid car ID
- `start_date`: Must be in YYYY-MM-DD format
- `end_date`: Must be after start_date
- `dropoff_branch_id`: Must be a valid active branch ID
- Car must be available
- No overlapping rentals for the selected car

**Response (201 Created):**
```json
{
    "id": 5,
    "username": "john_doe",
    "car": {
        "id": 1,
        "name": "Honda Civic",
        "slug": "honda-civic",
        "brand": "Honda",
        "model_year": 2023,
        "car_type": "sedan",
        "seats": 5,
        "price_per_day": 50.00,
        "is_available": true,
        "image": "https://example.com/images/civic.jpg"
    },
    "car_id": 1,
    "start_date": "2024-06-10",
    "end_date": "2024-06-15",
    "total_price": 300.00,
    "status": "pending",
    "pickup_location": "123 Main Street, Karachi",
    "dropoff_location": "456 Liberty Road, Lahore",
    "dropoff_branch_id": 2,
    "created_at": "2024-06-05T10:30:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
    "car_id": ["Invalid pk \"999\" - object does not exist."],
    "start_date": ["This field is required."],
    "non_field_errors": ["This car is already booked for the selected dates"]
}
```

---

### 9. List User Rentals
**Endpoint:** `GET /api/v1/user/rentals/` or `GET /api/v1/user/rental/`

**Authentication:** Required (JWT Token)

**Description:** List all active, completed, and cancelled rentals for the authenticated user with pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response (200 OK):**
```json
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 5,
            "username": "john_doe",
            "car": {
                "id": 1,
                "name": "Honda Civic",
                "slug": "honda-civic",
                "brand": "Honda",
                "model_year": 2023,
                "car_type": "sedan",
                "seats": 5,
                "price_per_day": 50.00,
                "is_available": true,
                "image": "https://example.com/images/civic.jpg"
            },
            "start_date": "2024-06-10",
            "end_date": "2024-06-15",
            "total_price": 300.00,
            "status": "active",
            "created_at": "2024-06-05T10:30:00Z"
        }
    ]
}
```

---

### 10. List All Rentals (Admin/Query)
**Endpoint:** `GET /api/v1/rental/`

**Authentication:** Required (JWT Token)

**Description:** List rentals (typically for admin purposes or querying system rentals).

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response (200 OK):**
```json
{
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 5,
            "username": "john_doe",
            "car": { ... },
            "start_date": "2024-06-10",
            "end_date": "2024-06-15",
            "total_price": 300.00,
            "status": "pending",
            "pickup_location": "123 Main Street, Karachi",
            "dropoff_location": "456 Liberty Road, Lahore",
            "dropoff_branch_id": 2,
            "created_at": "2024-06-05T10:30:00Z"
        }
    ]
}
```

---

## Payment Endpoints

### 11. Create Payment
**Endpoint:** `POST /api/v1/payment/`

**Authentication:** Required (JWT Token)

**Description:** Create a payment for a rental. Supports both Stripe and Cash payment methods.

**Request Body:**
```json
{
    "rental_id": 5,
    "payment_method": "stripe"
}
```

**Payment Methods:**
- `stripe`: Redirect to Stripe checkout session
- `cash`: Direct payment confirmation

**Response (201 Created) - Stripe:**
```json
{
    "payment_id": 10,
    "checkout_url": "https://checkout.stripe.com/pay/cs_live_XXX"
}
```

**Response (201 Created) - Cash:**
```json
{
    "id": 10,
    "rental_id": 5,
    "amount": 300.00,
    "payment_method": "cash",
    "stripe_session_id": null,
    "is_paid": true,
    "paid_at": "2024-06-05T10:35:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
    "rental_id": ["Invalid pk \"999\" - object does not exist."],
    "non_field_errors": ["Not your rental."]
}
```

or

```json
{
    "non_field_errors": ["Your rental is no longer available for payment."]
}
```

or

```json
{
    "non_field_errors": ["Payment already completed."]
}
```

---

## User Profile Endpoints

### 12. Get User Profile
**Endpoint:** `GET /api/v1/user-profile/`

**Authentication:** Required (JWT Token)

**Description:** Get the authenticated user's profile information.

**Response (200 OK):**
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
}
```

---

### 13. Update User Profile
**Endpoint:** `PATCH /api/v1/user-profile/`

**Authentication:** Required (JWT Token)

**Description:** Update the authenticated user's profile information.

**Request Body:**
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "email": "newemail@example.com"
}
```

**Response (200 OK):**
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "newemail@example.com",
    "first_name": "John",
    "last_name": "Doe"
}
```

---

## Webhook Endpoints

### 14. Stripe Webhook
**Endpoint:** `POST /api/v1/stripe/webhook/`

**Authentication:** No (Verified via Stripe Signature)

**Description:** Webhook for receiving Stripe payment events. Processes payment confirmations and updates rental status.

**Headers:**
```
Stripe-Signature: t=timestamp,v1=signature
```

**Supported Events:**
- `checkout.session.completed`: Payment successful, activate rental
- `payment_intent.payment_failed`: Payment failed

---

## Error Handling

### Common Error Responses

**401 Unauthorized:**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

or

```json
{
    "detail": "Invalid token."
}
```

**403 Forbidden:**
```json
{
    "detail": "You do not have permission to perform this action."
}
```

**404 Not Found:**
```json
{
    "detail": "Not found."
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Internal server error"
}
```

---

## Request Headers

All authenticated requests should include:
```
Authorization: Bearer <your_access_token>
Content-Type: application/json
```

---

## Rental Status Lifecycle

- **pending**: Rental created, awaiting payment
- **active**: Payment received, rental is active
- **completed**: Rental period ended
- **cancelled**: Rental was cancelled

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- Pagination page size defaults to 9 for cars and 20 for rentals
- Rental expiration: Unpaid rentals expire after 5 minutes if payment not received
- Account activation: Token expires based on Django signing settings
