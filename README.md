# Face Authentication AI

<p align="center">

AI-powered identity verification system built with **Django REST Framework**.

</p>

---

# Overview

**Face Authentication AI** is a multi-step identity verification API.

The system uses JWT-based authentication and verifies the user's identity through a secure pipeline:

```

JWT Login
|
▼
┌───────────────┐
│  Upload ID    │
│     Card      │
└───────┬───────┘
│
▼
┌───────────────┐
│ Face Validate │
└───────┬───────┘
│
▼
┌───────────────┐
│ Upload Selfie │
└───────┬───────┘
│
▼
┌───────────────┐
│ Face Matching │
└───────┬───────┘
│
▼
┌───────────────┐
│ Upload Video  │
│ + Text Check  │
└───────┬───────┘
│
▼
┌───────────────┐
│   Verified    │
└───────────────┘

```

---


## Get Token

```
POST /api/token/
```

Body:

```json
{
    "username": "username",
    "password": "password"
}
```


Response:

```json
{
    "access": "jwt-access-token",
    "refresh": "jwt-refresh-token"
}
```




---

# Features

* JWT authentication
* National ID card verification
* Face matching between selfie and ID card
* Video-based liveness verification
* Speech challenge validation
* Async AI processing with Celery
* Background task monitoring
* REST API architecture
* Swagger API documentation

---

# Verification Process

## 1️⃣ ID Card Verification

Authenticated user uploads their national ID card.

---

## Upload ID Card

```
POST /api/id_card/
```

Content-Type:

```
multipart/form-data
```

Headers:

```
Authorization: Bearer <token>
```

Body:

| Field | Type  | Description   |
| ----- | ----- | ------------- |
| photo | image | ID card image |

Example:

```
photo=id_card.jpg
```

Maximum size:

```
5 MB
```

---

## Processing

The request creates a Celery task.

Response:

```json
{
    "ok": true,
    "task_id": "9f82a1",
    "message": "Processing started"
}
```

---

## Check Status

```
GET /api/id_card/task-status/{task_id}/
```

Example:

```
GET /api/id_card/task-status/9f82a1/
```

Response:

```json
{
    "state": "PENDING",
    "ok": null
}
```

or:

```json
{
    "state": "SUCCESS",
    "ok": true
}
```

---

# 2️⃣ Face Verification

After successful ID verification,
the authenticated user uploads a selfie.

The system compares:

```
Selfie
   |
   ▼
Face Recognition AI
   |
   ▼
ID Card Face
```

---

## Upload Face Image

```
POST /api/face/
```

Content-Type:

```
multipart/form-data
```

Headers:

```
Authorization: Bearer <token>
```

Body:

| Field | Type  | Description |
| ----- | ----- | ----------- |
| photo | image | User selfie |

Example:

```
photo=selfie.png
```

Maximum size:

```
5 MB
```

---

## Check Status

```
GET /api/face/task-status/{task_id}/
```

---

# 3️⃣ Video Liveness Verification

The user records a video while saying
a generated challenge sentence.

The API validates:

* Video file
* Spoken words
* User presence

---

## Upload Video

```
POST /api/video/
```

Content-Type:

```
multipart/form-data
```

Headers:

```
Authorization: Bearer <token>
```

Body:

| Field       | Type   | Description         |
| ----------- | ------ | ------------------- |
| video       | file   | Verification video  |
| randomCheck | string | Words user must say |

Example:

```
video=verification.mp4

randomCheck=
"my verification code is seven four two"
```

Supported formats:

```
.mp4
.mov
.avi
.mkv
```

Maximum size:

```
100 MB
```

---

## Check Status

```
GET /api/video/task-status/{task_id}/
```

---

# User Verification Status

Get verification progress:

```
GET /api/userstatus/
```

Headers:

```
Authorization: Bearer <token>
```

Example response:

```json
{
    "username" : "username",
    "user_idcard_status": true,
    "user_face_status": true,
    "user_video_status": true
}
```

---

# Async Processing

All AI-heavy operations run asynchronously.

Flow:

```
API Request
     |
     ▼
JWT Authentication
     |
     ▼
Create Celery Task
     |
     ▼
Return Task ID
     |
     ▼
Background AI Processing
     |
     ▼
Check Task Status
```

The API never waits for AI processing.

---

# API Documentation

Swagger UI:

```
GET /swagger/
```

---

# Important Notes

* All APIs require JWT authentication.
* User identity comes from JWT token.
* No username is sent from the client.
* Images are validated before processing.
* Videos have size and format restrictions.
* AI processing runs in Celery workers.
* Always wait for SUCCESS before moving to the next step.
