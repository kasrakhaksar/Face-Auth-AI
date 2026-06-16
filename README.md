# Face Authentication AI

<p align="center">

AI-powered identity verification system built with **Django REST Framework**.

</p>

---

## Overview

**Face Authentication AI** is a multi-step identity verification API.

The system verifies a user's identity through a secure pipeline:

```
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

#  Features

- National ID card verification  
- Face matching between selfie and ID card  
- Video-based liveness verification  
- Speech challenge validation  
- Async AI processing with Celery  
- Background task monitoring  
- REST API architecture  
- Swagger API documentation  

---

#  Verification Process

## 1️⃣ ID Card Verification

User uploads a photo of their national ID card.

The system processes the image and starts verification.

### Request

```
POST /id_card/
```

Content-Type:

```
multipart/form-data
```

### Body

| Field | Type | Description |
|---|---|---|
| username | string | User identifier |
| photo | image | ID card image |

Example:

```
username=john
photo=id_card.jpg
```



Maximum size:

```
5 MB
```

---

## 🔄 Check

AI processing runs in background.

Check the result:

```
GET /id_card/task-status/{task_id}/
```

Example:

```
GET /id_card/task-status/9f82a1/
```

Response:

```json
{
    "status": "PENDING"
}
```

or:

```json
{
    "status": "SUCCESS"
}
```

or:

```json
{
    "status": "FAILED"
}
```

---

# 2️⃣ Face Verification

After successful ID verification,
the user uploads a selfie.

The system compares:

```
       Selfie
          │
          ▼
   Face Recognition AI
          │
          ▼
    ID Card Portrait
```

---

## Upload Face Image

```
POST /face/
```

Content-Type:

```
multipart/form-data
```

Body:

| Field | Type | Description |
|---|---|---|
| username | string | User identifier |
| photo | image | User selfie |

Example:

```
username=john
photo=selfie.png
```


Maximum size:

```
5 MB
```

---

## 🔄 Check

```
GET /face/task-status/{task_id}/
```

Continue to video verification after success.

---

# 3️⃣ Video Liveness Verification

The user records a short video
while saying a generated sentence.

The API validates:

-  Video file
-  Spoken text
-  User presence

---

## Upload Video

```
POST /video/
```

Content-Type:

```
multipart/form-data
```

Body:

| Field | Type | Description |
|---|---|---|
| username | string | User identifier |
| video | file | Verification video |
| randomCheck | string | Sentence user must say |

Example:

```
username=john

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

## 🔄 Check

```
GET /video/task-status/{task_id}/
```


---

# User Verification Status

Get final verification result:

```
POST /userstatus/
```

### Body

| Field | Type | Description |
|---|---|---|
| username | string | User identifier |


Example:


```json
{
    "username": "john",
    "user_idcard_status": true,
    "user_face_status": true,
    "user_video_status": true,
}
```

---

# Async Processing

All AI-heavy operations are handled asynchronously.

Flow:

```
API Request
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

# ⚠️ Important Notes

- Images are validated before processing.
- Videos have size and format restrictions.
- Every AI operation runs asynchronously.
- Always wait for `SUCCESS` before moving to the next step.