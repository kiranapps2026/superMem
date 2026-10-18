# R3 Route Sweep Results

**Timestamp:** 2026-09-25T07:56:01.513Z

| Route | HTTP Status | Console Errors | Verdict |
|---|---|---|---|
| / | 200 | none | renders |
| /_not-found | 200 | 1: ["Failed to load resource: the server responded with a status of 404 (Not Found) | renders-with-errors |
| /auth/login | 200 | none | renders |
| /auth/register | 200 | none | renders |
| /dashboard | 200 | none | renders |
| /projects | 200 | none | renders |
| /settings | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /settings/api-keys | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /settings/profile | 200 | none | renders |
| /settings/storage | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /projects/1e2a4ea0/chat | 200 | none | renders |
| /projects/1e2a4ea0/decisions | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /projects/1e2a4ea0/facts | 200 | none | renders |
| /projects/1e2a4ea0/graph | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /projects/1e2a4ea0/ingest | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /projects/1e2a4ea0/memory | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /projects/1e2a4ea0/provenance | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /projects/1e2a4ea0/search | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /projects/1e2a4ea0/sessions | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /projects/1e2a4ea0/sessions/{pid} | 200 | none | renders |
| /projects/1e2a4ea0/settings | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |
| /projects/1e2a4ea0/timeline | 200 | 1: ["Failed to load resource: the server responded with a status of 401 (Unauthoriz | renders |

**Summary:** 21 renders, 1 renders-with-errors, 0 fails (22 total)