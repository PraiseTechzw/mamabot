const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#send-button");
const errorMessage = document.querySelector("#error-message");

function addMessage(text, role, meta = "") {
  const item = document.createElement("article");
  item.className = `message ${role}`;
  item.innerHTML = `<p></p>${meta ? `<small>${meta}</small>` : ""}`;
  item.querySelector("p").textContent = text;
  messages.appendChild(item);
  messages.scrollTop = messages.scrollHeight;
}

function setLoading(isLoading) {
  input.disabled = isLoading;
  sendButton.disabled = isLoading;
  sendButton.querySelector("span").textContent = isLoading ? "Sending" : "Send";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || sendButton.disabled) return;

  errorMessage.hidden = true;
  addMessage(message, "user", "You");
  input.value = "";
  setLoading(true);

  try {
    const response = await fetch("/webhook/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        sender: "local-browser",
        language: "en",
      }),
    });
    const data = await response.json();
    if (!response.ok)
      throw new Error(
        data.error || "The local service could not process that message.",
      );
    addMessage(data.text, "bot", `MamaBot · ${data.language}`);
  } catch (error) {
    errorMessage.textContent =
      error.message ||
      "The local service is unavailable. Start Flask and try again.";
    errorMessage.hidden = false;
  } finally {
    setLoading(false);
    input.focus();
  }
});
