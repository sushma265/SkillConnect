# SkillConnect – Sample API Requests & Responses

Use these examples in **Postman**, **Thunder Client**, or `curl`.
Base URL: `http://127.0.0.1:5000`

---

## 🔐 Authentication

### POST /auth/signup

**Request**
```json
POST /auth/signup
Content-Type: application/json

{
  "name": "Alice Smith",
  "email": "alice@example.com",
  "password": "alice123",
  "role": "user"
}
```

**Response 201**
```json
{
  "message": "Account created successfully",
  "user": {
    "id": 4,
    "name": "Alice Smith",
    "email": "alice@example.com",
    "role": "user",
    "is_active": true,
    "created_at": "2025-07-01T10:00:00+00:00"
  }
}
```

---

### POST /auth/login

**Request**
```json
POST /auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "user123"
}
```

**Response 200**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 3,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true,
    "created_at": "2025-07-01T09:00:00+00:00"
  }
}
```

---

## 📚 Courses

### POST /courses  *(Conductor / Admin)*

**Request**
```json
POST /courses
Authorization: Bearer <conductor_token>
Content-Type: application/json

{
  "title": "Data Science with Python",
  "description": "Learn pandas, matplotlib, and scikit-learn from scratch.",
  "price": 1299,
  "duration": "6 weeks",
  "instructor": "Dr. Jane Conductor",
  "category": "Data Science"
}
```

**Response 201**
```json
{
  "message": "Course created",
  "course": {
    "id": 3,
    "title": "Data Science with Python",
    "description": "Learn pandas, matplotlib, and scikit-learn from scratch.",
    "price": 1299.0,
    "duration": "6 weeks",
    "instructor": "Dr. Jane Conductor",
    "category": "Data Science",
    "created_by": 2,
    "created_at": "2025-07-01T11:00:00+00:00",
    "updated_at": "2025-07-01T11:00:00+00:00"
  }
}
```

---

### GET /courses

**Request**
```
GET /courses
GET /courses?category=Programming
```

**Response 200**
```json
{
  "courses": [
    {
      "id": 1,
      "title": "Python for Beginners",
      "description": "Learn Python from scratch with hands-on exercises.",
      "price": 999.0,
      "duration": "4 weeks",
      "instructor": "Jane Conductor",
      "category": "Programming",
      "created_by": 2,
      "created_at": "2025-07-01T09:00:00+00:00",
      "updated_at": "2025-07-01T09:00:00+00:00"
    }
  ]
}
```

---

### PUT /courses/1  *(update)*

**Request**
```json
PUT /courses/1
Authorization: Bearer <conductor_token>
Content-Type: application/json

{
  "price": 799,
  "duration": "5 weeks"
}
```

**Response 200**
```json
{
  "message": "Course updated",
  "course": { "id": 1, "price": 799.0, "duration": "5 weeks", "..." : "..." }
}
```

---

## 📅 Events & Workshops

### POST /events  *(Conductor / Admin)*

**Request**
```json
POST /events
Authorization: Bearer <conductor_token>
Content-Type: application/json

{
  "title": "React.js Workshop",
  "description": "Build a full React app in one day.",
  "event_type": "workshop",
  "venue": "Lab 3, Block B",
  "event_date": "2025-08-20 10:00",
  "price": 199,
  "capacity": 30
}
```

**Response 201**
```json
{
  "message": "Event created",
  "event": {
    "id": 3,
    "title": "React.js Workshop",
    "event_type": "workshop",
    "venue": "Lab 3, Block B",
    "event_date": "2025-08-20T10:00:00",
    "price": 199.0,
    "capacity": 30,
    "registered_count": 0,
    "created_by": 2,
    "created_at": "2025-07-01T12:00:00+00:00"
  }
}
```

---

### POST /events/2/register  *(Free event)*

**Request**
```
POST /events/2/register
Authorization: Bearer <user_token>
```

**Response 201**
```json
{
  "message": "Registered successfully",
  "registration": {
    "id": 1,
    "user_id": 3,
    "event_id": 2,
    "event_title": "Open Source Day",
    "status": "confirmed",
    "registered_at": "2025-07-01T13:00:00+00:00"
  }
}
```

---

### GET /events/my-registrations

**Request**
```
GET /events/my-registrations
Authorization: Bearer <user_token>
```

**Response 200**
```json
{
  "registrations": [
    {
      "id": 1,
      "user_id": 3,
      "event_id": 2,
      "event_title": "Open Source Day",
      "status": "confirmed",
      "registered_at": "2025-07-01T13:00:00+00:00"
    }
  ]
}
```

---

## 💳 Payments (Razorpay)

### Step 1 – POST /payments/create-order

**Request (Course Purchase)**
```json
POST /payments/create-order
Authorization: Bearer <user_token>
Content-Type: application/json

{
  "payment_type": "course",
  "item_id": 1
}
```

**Response 201**
```json
{
  "message": "Order created. Complete payment using the Razorpay SDK.",
  "order_id": "order_PxXyZaB12345",
  "amount": 999.0,
  "amount_paise": 99900,
  "currency": "INR",
  "razorpay_key_id": "rzp_test_xxxxxxxxxxxx",
  "payment_id": 1
}
```

**Request (Event Registration)**
```json
{
  "payment_type": "event",
  "item_id": 1
}
```

---

### Step 2 – POST /payments/verify

After the user completes payment on the Razorpay checkout, send the callback data:

**Request**
```json
POST /payments/verify
Authorization: Bearer <user_token>
Content-Type: application/json

{
  "razorpay_order_id": "order_PxXyZaB12345",
  "razorpay_payment_id": "pay_AbCdEf67890",
  "razorpay_signature": "sha256_signature_from_razorpay"
}
```

**Response 200**
```json
{
  "message": "Payment verified successfully",
  "payment": {
    "id": 1,
    "user_id": 3,
    "course_id": 1,
    "event_id": null,
    "razorpay_order_id": "order_PxXyZaB12345",
    "razorpay_payment_id": "pay_AbCdEf67890",
    "amount": 999.0,
    "currency": "INR",
    "status": "paid",
    "payment_type": "course",
    "created_at": "2025-07-01T14:00:00+00:00",
    "paid_at": "2025-07-01T14:05:00+00:00"
  }
}
```

---

### GET /payments/history

**Request**
```
GET /payments/history
Authorization: Bearer <user_token>
```

**Response 200**
```json
{
  "payments": [
    {
      "id": 1,
      "amount": 999.0,
      "currency": "INR",
      "status": "paid",
      "payment_type": "course",
      "course_id": 1,
      "event_id": null,
      "paid_at": "2025-07-01T14:05:00+00:00"
    }
  ]
}
```

---

## 📢 Announcements

### POST /announcements

**Request**
```json
POST /announcements
Authorization: Bearer <conductor_token>
Content-Type: application/json

{
  "title": "New Batch Starting Soon",
  "content": "The Python Bootcamp batch 3 starts on August 1st. Register now!"
}
```

**Response 201**
```json
{
  "message": "Announcement created",
  "announcement": {
    "id": 2,
    "title": "New Batch Starting Soon",
    "content": "The Python Bootcamp batch 3 starts on August 1st. Register now!",
    "created_by": 2,
    "created_at": "2025-07-01T15:00:00+00:00"
  }
}
```

---

## ⭐ Feedback

### POST /feedback

**Request (Course Feedback)**
```json
POST /feedback
Authorization: Bearer <user_token>
Content-Type: application/json

{
  "feedback_type": "course",
  "item_id": 1,
  "rating": 5,
  "comment": "Excellent course! Very well structured and easy to follow."
}
```

**Request (Event Feedback)**
```json
{
  "feedback_type": "event",
  "item_id": 1,
  "rating": 4,
  "comment": "Great workshop, hands-on exercises were really helpful."
}
```

**Response 201**
```json
{
  "message": "Feedback submitted",
  "feedback": {
    "id": 1,
    "user_id": 3,
    "course_id": 1,
    "event_id": null,
    "rating": 5,
    "comment": "Excellent course! Very well structured and easy to follow.",
    "feedback_type": "course",
    "created_at": "2025-07-01T16:00:00+00:00"
  }
}
```

### GET /feedback

```
GET /feedback
GET /feedback?type=course&item_id=1
GET /feedback?type=event&item_id=2
```

---

## 🛡 Admin

### GET /admin/users

```
GET /admin/users
Authorization: Bearer <admin_token>
```

### PUT /admin/users/3  *(change role or deactivate)*

```json
PUT /admin/users/3
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "role": "conductor",
  "is_active": true
}
```

### GET /admin/payments  *(with optional filter)*

```
GET /admin/payments
GET /admin/payments?status=paid
Authorization: Bearer <admin_token>
```

**Response**
```json
{
  "payments": [ ... ],
  "total_revenue": 2298.0
}
```

---

## ❌ Common Error Responses

| Status | Example Body |
|--------|-------------|
| 400 | `{"error": "'email' is required"}` |
| 401 | `{"error": "Invalid email or password"}` |
| 403 | `{"error": "Access denied. Required role(s): ['admin']"}` |
| 404 | `{"error": "Course not found"}` |
| 409 | `{"error": "Email already registered"}` |
| 422 | `{"msg": "Not enough segments"}` ← missing/bad JWT |
| 502 | `{"error": "Razorpay order creation failed"}` |
