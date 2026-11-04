# GQT HRMS — Phase 4: Upload Security & Private Storage Architecture

## 1. Threat Model & Security Objectives

Asset uploads represent a potential entry vector for malicious binaries, disguised scripts (polyglot files), directory traversal, and stored cross-site scripting (XSS).

To defend the platform, the Creative Studio architecture enforces a defense-in-depth model across five security controls:

```
[Incoming File Upload]
        │
        ▼
[Control 1: Extension Whitelist & Sanitization]
        │
        ▼
[Control 2: File Size Enforcement (Max 15MB)]
        │
        ▼
[Control 3: Deep Magic-Byte Inspection]
        │
        ▼
[Control 4: Cryptographic Checksum (SHA-256)]
        │
        ▼
[Control 5: Isolated Private Storage & Proxy Streaming]
```

---

## 2. Five-Layer Upload Security Controls

### 2.1 Extension Whitelist & Path Sanitization
- Only extensions `.png`, `.jpg`, `.jpeg`, `.webp`, and `.pdf` are permitted.
- Double extensions (e.g. `flyer.php.png` or `banner.html.jpg`) are detected and stripped or rejected.
- Path traversal sequences (`../`, `..\`, null bytes `\0`) are eliminated using strict normalization routines.
- Filenames on disk are randomized using UUIDs:
  `{year}/{request_id}/{version_id}_{sanitized_basename}.{ext}`

### 2.2 File Size Enforcement
- Maximum permitted upload size: **15 MB** (`15 * 1024 * 1024` bytes).
- Uploads exceeding this threshold are immediately rejected with `400 Bad Request` prior to disk writing.

### 2.3 Deep Magic-Byte / Signature Inspection
File extensions can easily be falsified. The backend inspects the actual leading header bytes:

| File Type | Expected Header Signature (Magic Bytes) | Validated MIME Type |
| :--- | :--- | :--- |
| **PNG** | `89 50 4E 47 0D 0A 1A 0A` | `image/png` |
| **JPEG** | `FF D8 FF` | `image/jpeg` |
| **WEBP** | `52 49 46 46 ... 57 45 42 50` | `image/webp` |
| **PDF** | `25 50 44 46` (`%PDF-`) | `application/pdf` |

- Disallowed content types (such as SVG files containing executable `<script>` tags, HTML, PHP, or Windows PE binaries) are rejected with `400 Bad Request` ("File signature does not match permitted image or PDF formats").

### 2.4 Cryptographic Checksum (SHA-256)
- The SHA-256 digest is calculated as the file is processed into storage.
- The hash is stored in `CreativeAssetVersion.sha256_hash` (unique 64-character hex string).
- This ensures asset integrity and guarantees that no silent modification or tampering occurs in transit or storage.

### 2.5 Isolated Private Storage & Authenticated Proxy Streaming
- Assets are stored exclusively in `PRIVATE_MEDIA_ROOT` outside the web server's static root (`STATIC_ROOT` and public `MEDIA_ROOT`).
- Direct URL access to asset files is prevented at the web server and application levels.
- File viewing and downloading are served strictly through the authenticated Django endpoint:
  `GET /api/v1/creatives/versions/{id}/download/`
- Every request sends the following defensive HTTP response headers:
  - `X-Content-Type-Options: nosniff` (prevents browser MIME-type sniffing)
  - `Content-Security-Policy: default-src 'none'; sandbox` (for PDF/image rendering)
  - `Cache-Control: private, no-cache, no-store, must-revalidate`

---

## 3. Storage Directory Hierarchy

```
<BASE_DIR>/
└── media/
    └── private/
        └── creatives/
            └── 2026/
                └── <request_uuid>/
                    ├── <version_uuid_1>_Infosys_Flyer_v1.png
                    └── <version_uuid_2>_Infosys_Flyer_v2.png
```

This clean hierarchical partitioning avoids inode exhaustion and isolates assets by calendar year and requisition identifier.

