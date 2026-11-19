const proof = document.querySelector('#proof');
const proofLink = document.querySelector('#proof-link');
const recipients = document.querySelectorAll('.choice');
const copyStatus = document.querySelector('#copy-status');

function isPlainClick(event) {
  return event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey;
}

for (const recipient of recipients) {
  recipient.addEventListener('click', (event) => {
    if (!isPlainClick(event)) return;
    event.preventDefault();
    const name = recipient.dataset.name;
    for (const item of recipients) item.removeAttribute('aria-current');
    recipient.setAttribute('aria-current', 'true');
    proof.src = recipient.href;
    proof.alt = `Architectural drawing of a sawtooth-roof pavilion with ${name} stamped diagonally across the page.`;
    proofLink.href = recipient.href;
    proofLink.setAttribute('aria-label', `Open full-size drawing for ${name}`);
    copyStatus.textContent = `Showing the copy issued to ${name}.`;
  });
}

const stages = {
  files: {
    title: 'Files preview',
    description: 'The Files screen lists three drawings in a sample tender pack.',
    caption: 'Check the PDFs included in your pack.'
  },
  design: {
    title: 'Design preview',
    description: 'The Design screen shows recipient settings beside a watermarked tender drawing.',
    caption: 'Preview the watermark on your drawing.'
  },
  export: {
    title: 'Export preview',
    description: 'The Export screen summarises the source documents, recipients and number of output copies.',
    caption: 'Review the copy count and destination.'
  }
};

const steps = document.querySelectorAll('.step');
const play = document.querySelector('#play');
const appImage = document.querySelector('#app-image');
const imageLink = document.querySelector('#image-link');
const fullImage = document.querySelector('#full-image');
const caption = document.querySelector('#caption');
const screenLabel = document.querySelector('#screen-label');

function showPreview(src, description, title, text) {
  appImage.src = src;
  appImage.alt = description;
  imageLink.href = src;
  imageLink.setAttribute('aria-label', `Open full-size ${title}`);
  fullImage.href = src;
  screenLabel.textContent = title;
  caption.textContent = text;
}

function setPlaying(playing) {
  play.dataset.playing = String(playing);
  document.querySelector('#play-text').textContent = playing ? 'Stop demo' : 'Play demo';
}

for (const step of steps) {
  step.addEventListener('click', (event) => {
    if (!isPlainClick(event)) return;
    event.preventDefault();
    for (const item of steps) item.removeAttribute('aria-current');
    step.setAttribute('aria-current', 'step');
    setPlaying(false);
    const stage = stages[step.dataset.stage];
    showPreview(step.href, stage.description, stage.title, stage.caption);
  });
}

play.addEventListener('click', (event) => {
  if (!isPlainClick(event)) return;
  event.preventDefault();
  const playing = play.dataset.playing !== 'true';
  setPlaying(playing);
  for (const item of steps) item.removeAttribute('aria-current');
  if (playing) {
    showPreview(play.href, 'A recording of PDF Watermark adding a folder of PDFs, designing a mark and exporting copies.', 'App walkthrough', 'A sample tender pack, from files to export.');
  } else {
    showPreview('media/pdf-watermark-demo.png', 'Still from the app walkthrough showing the Design screen.', 'Walkthrough still', 'A sample tender pack in the Design step.');
  }
});
