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

// Full-size viewer: cycle through the app screenshots, close with X, Esc or a click outside.
const viewer = document.createElement('dialog');
viewer.className = 'viewer';
viewer.setAttribute('aria-label', 'App screenshots');
viewer.innerHTML = `
  <button class="viewer-close" type="button" aria-label="Close">&times;</button>
  <button class="viewer-nav viewer-prev" type="button" aria-label="Previous screenshot">&#8249;</button>
  <figure class="viewer-frame">
    <img class="viewer-image" alt="">
    <figcaption class="viewer-caption"><strong></strong><span></span><em></em></figcaption>
  </figure>
  <button class="viewer-nav viewer-next" type="button" aria-label="Next screenshot">&#8250;</button>`;
document.body.append(viewer);

const viewerImage = viewer.querySelector('.viewer-image');
const viewerTitle = viewer.querySelector('.viewer-caption strong');
const viewerText = viewer.querySelector('.viewer-caption span');
const viewerCount = viewer.querySelector('.viewer-caption em');
let viewerIndex = 0;

function showInViewer(index) {
  viewerIndex = (index + steps.length) % steps.length;
  const step = steps[viewerIndex];
  viewerImage.src = step.href;
  viewerImage.alt = step.dataset.alt;
  viewerTitle.textContent = step.querySelector('strong').textContent;
  viewerText.textContent = step.dataset.caption;
  viewerCount.textContent = `${viewerIndex + 1} / ${steps.length}`;
  selectScreenshot(step);
}

function openViewer(event) {
  if (!isPlainClick(event)) return;
  event.preventDefault();
  const current = steps.findIndex((step) => step.getAttribute('aria-current') === 'step');
  showInViewer(current < 0 ? 0 : current);
  viewer.showModal();
  document.documentElement.classList.add('viewer-open');
}

function closeViewer() { viewer.close(); }
viewer.addEventListener('close', () => document.documentElement.classList.remove('viewer-open'));

imageLink.addEventListener('click', openViewer);
fullImage.addEventListener('click', openViewer);
viewer.querySelector('.viewer-close').addEventListener('click', closeViewer);
viewer.querySelector('.viewer-prev').addEventListener('click', () => showInViewer(viewerIndex - 1));
viewer.querySelector('.viewer-next').addEventListener('click', () => showInViewer(viewerIndex + 1));
viewer.addEventListener('click', (event) => {
  if (event.target === viewer || event.target.classList.contains('viewer-frame')) closeViewer();
});
viewer.addEventListener('keydown', (event) => {
  if (event.key === 'ArrowLeft') { event.preventDefault(); showInViewer(viewerIndex - 1); }
  if (event.key === 'ArrowRight') { event.preventDefault(); showInViewer(viewerIndex + 1); }
});

let touchStartX = null;
viewer.addEventListener('touchstart', (event) => { touchStartX = event.touches[0].clientX; }, { passive: true });
viewer.addEventListener('touchend', (event) => {
  if (touchStartX === null) return;
  const dx = event.changedTouches[0].clientX - touchStartX;
  touchStartX = null;
  if (Math.abs(dx) > 40) showInViewer(viewerIndex + (dx < 0 ? 1 : -1));
});
