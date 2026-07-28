# Face Authentication AI

---

# Overview

**Face Authentication AI** is a multi-step identity verification API.

The system verifies the user's identity through a secure pipeline:

```

    JWT Login
        |
        ▼
┌───────────────┐
│   Upload ID   │
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
│       +       │ 
│   Text Check  │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   Verified    │
└───────────────┘

```


## API Documentation

You can access the API documentation and test the available endpoints using Swagger:

```bash
/swagger
```