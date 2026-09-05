# MamaBot Architecture

MamaBot is a Flask application with one transport-neutral conversation core.

```text
Browser / SMS / WhatsApp
	-> provider adapter and Flask route
	-> preprocessing, language detection, intent model, entity extraction
	-> DialogueManager
	-> repository and response catalog
	-> normalized provider response
```

`DialogueManager` receives text, sender, preferred language, and channel. It owns conversational state and calls the shared NLP pipeline. It does not import SMSPOP or WhatsApp code. Routes and messaging adapters normalize provider payloads into `InboundMessage` and send `OutboundMessage` values back through provider interfaces.

MySQL is the production repository. The in-memory repository is a deliberate local/test implementation of the same core contract. Registration sessions are process-local; deployments needing multiple workers should move session storage to Redis or use one worker until that boundary is implemented.

The reminder engine reads scheduled appointments from the repository, selects the user's language and channel, sends through a provider mapping, and records `sent` or `failed` status. APScheduler is started only when `ENABLE_REMINDER_SCHEDULER=true`.
