export function bindForm(selector, handler) {
  const form = document.querySelector(selector);
  form?.addEventListener('submit', async event => {
    event.preventDefault();
    const submit = form.querySelector('button[type=submit]');
    const error = form.querySelector('[role=alert]');
    submit.disabled = true;
    error.textContent = '';
    try {
      await handler(Object.fromEntries(new FormData(form)));
    } catch (failure) {
      error.textContent = failure.message;
    } finally {
      submit.disabled = false;
    }
  });
}
