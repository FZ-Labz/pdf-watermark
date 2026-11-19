const proof = document.querySelector('#proof');
const proofLink = document.querySelector('#proof-link');
const recipients = document.querySelectorAll('.choice');
const copyStatus = document.querySelector('#copy-status');
const proofDescription = document.querySelector('.issue-preview').dataset.description;

function isPlainClick(event) {
  return event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey;
}

for (const recipient of recipients) {
  recipient.addEventListener('click', (event) => {
    if (!isPlainClick(event)) return;
    event.preventDefault();
    const name = recipient.textContent.trim();
    for (const item of recipients) item.removeAttribute('aria-current');
    recipient.setAttribute('aria-current', 'true');
    proof.src = recipient.href;
    proof.alt = `${proofDescription} Watermarked for ${name}.`;
    proofLink.href = recipient.href;
    proofLink.setAttribute('aria-label', `Open full-size drawing for ${name}`);
    copyStatus.textContent = `Showing the copy issued to ${name}.`;
  });
}

const steps = Array.from(document.querySelectorAll('.step'));
const appImage = document.querySelector('#app-image');
const imageLink = document.querySelector('#image-link');
const fullImage = document.querySelector('#full-image');
const caption = document.querySelector('#caption');
const screenLabel = document.querySelector('#screen-label');

function selectScreenshot(step) {
  for (const item of steps) item.removeAttribute('aria-current');
  step.setAttribute('aria-current', 'step');
  appImage.src = step.href;
  appImage.alt = step.dataset.alt;
  imageLink.href = step.href;
  fullImage.href = step.href;
  screenLabel.textContent = step.querySelector('strong').textContent;
  caption.textContent = step.dataset.caption;
}

for (const [index, step] of steps.entries()) {
  step.addEventListener('click', (event) => {
    if (!isPlainClick(event)) return;
    event.preventDefault();
    selectScreenshot(step);
  });
  step.addEventListener('keydown', (event) => {
    const next = {
      ArrowLeft: (index + steps.length - 1) % steps.length,
      ArrowRight: (index + 1) % steps.length,
      Home: 0,
      End: steps.length - 1
    }[event.key];
    if (next === undefined) return;
    event.preventDefault();
    steps[next].focus();
    selectScreenshot(steps[next]);
  });
}
