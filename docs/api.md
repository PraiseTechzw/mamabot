# API

## Browser

`GET /` serves the local browser chat. `POST /webhook/test` is enabled only in Flask testing mode unless `ALLOW_TEST_WEBHOOK=true` is explicitly configured.

Request:

```json
{ "message": "Hello MamaBot", "sender": "local-browser", "language": "en" }
```

Response fields are `text`, `language`, `intent`, `confidence`, and `escalation`.

## SMS

`POST /sms/inbound` accepts the internal adapter payload `{ "from": "...", "message": "..." }`. The configured provider normalizes it, the shared dialogue service processes it, and the provider sends the response. Production SMSPOP field mapping must follow the vendor's current documentation.

## WhatsApp

`POST /whatsapp/webhook` follows the same internal payload contract. Signature verification and vendor payload mapping are provider hooks; no undocumented WhatsApp API endpoint is assumed.

## Health and admin

`GET /health` is the liveness endpoint. `GET /admin/status` accepts `X-Admin-Token` when `ADMIN_TOKEN` is configured and the application is not in testing mode.
