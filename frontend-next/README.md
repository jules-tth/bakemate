# BakeMate frontend-next

Parallel Next.js scaffold proof only.

What this proves:
- public landing page for a BobbyD-testable preview front door
- current form-encoded auth request compatibility
- current localStorage token key compatibility (`token`)
- authenticated `/ops` shell connectivity using the existing API
- reachable authenticated handoff into `/orders` and order detail preview

What this does not claim:
- replacement of the current frontend
- full frontend cutover
- broader workflow parity beyond the accepted Next operator preview path

## Run

```bash
cd frontend-next
npm install
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001/api/v1 npm run dev
```

Then open:
- `/` for the public preview landing page
- `/login` to prove auth/token compatibility
- `/ops` to prove authenticated shell connectivity
- `/orders` for the authenticated queue preview
