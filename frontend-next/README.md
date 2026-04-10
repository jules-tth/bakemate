# BakeMate frontend-next

Parallel Next.js scaffold proof only.

What this proves:
- current form-encoded auth request compatibility
- current localStorage token key compatibility (`token`)
- authenticated `/ops` shell connectivity using the existing API

What this does not claim:
- replacement of the current frontend
- `/orders` parity
- order-detail parity

## Run

```bash
cd frontend-next
npm install
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001/api/v1 npm run dev
```

Then open:
- `/login` to prove auth/token compatibility
- `/ops` to prove authenticated shell connectivity
