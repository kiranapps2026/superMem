# R3 Route Sweep Results

**Timestamp:** 2026-09-24T16:11:31.253Z

| Route | HTTP Status | Console Errors | Verdict |
|---|---|---|---|
| / | 200 | none | renders |
| /_not-found | 200 | 1: ["Failed to load resource: the server responded with a status of 404 (Not Found) | renders-with-errors |
| /auth/login | 200 | none | renders |
| /auth/register | 200 | none | renders |
| /dashboard | 200 | none | renders |
| /projects | 200 | none | renders |
| /settings | 200 | none | renders |
| /settings/api-keys | 200 | none | renders |
| /settings/profile | 200 | none | renders |
| /settings/storage | 200 | none | renders |
| /projects/b5dd6758/chat | 200 | none | renders |
| /projects/b5dd6758/decisions | 200 | none | renders |
| /projects/b5dd6758/facts | 200 | none | renders |
| /projects/b5dd6758/graph | 200 | none | renders |
| /projects/b5dd6758/ingest | 200 | none | renders |
| /projects/b5dd6758/memory | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /projects/b5dd6758/provenance | 200 | none | renders |
| /projects/b5dd6758/search | 200 | none | renders |
| /projects/b5dd6758/sessions | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /projects/b5dd6758/sessions/{pid} | 200 | none | renders |
| /projects/b5dd6758/settings | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /projects/b5dd6758/timeline | 200 | none | renders |

**Summary:** 21 renders, 1 renders-with-errors, 0 fails (22 total)