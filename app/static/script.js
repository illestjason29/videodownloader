const form = document.querySelector('#fetch-form');
const urlInput = document.querySelector('#video-url');
const resultSection = document.querySelector('#result');
const loadingSection = document.querySelector('#loading');
const errorSection = document.querySelector('#error');
const videoOptions = document.querySelector('#video-options');
const audioOptions = document.querySelector('#audio-options');
const videoTitle = document.querySelector('#video-title');
const videoAuthor = document.querySelector('#video-author');
const videoDescription = document.querySelector('#video-description');
const videoThumbnail = document.querySelector('#video-thumbnail');
const videoDuration = document.querySelector('#video-duration');
const formatAlert = document.querySelector('#format-alert');

function toggleLoading(isLoading) {
  loadingSection.classList.toggle('hidden', !isLoading);
  form.querySelector('button').disabled = isLoading;
}

function showError(message) {
  errorSection.textContent = message;
  errorSection.classList.remove('hidden');
  resultSection.classList.add('hidden');
}

function hideError() {
  errorSection.classList.add('hidden');
}

function formatDuration(seconds) {
  if (!seconds && seconds !== 0) {
    return '';
  }
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${minutes}:${secs}`;
}

function formatFilesize(bytes) {
  if (!bytes) return '—';
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(size >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

function createOption({ label, subLabel, action }) {
  const wrapper = document.createElement('div');
  wrapper.className = 'option';

  const labelEl = document.createElement('div');
  labelEl.className = 'option-label';
  labelEl.innerHTML = `<strong>${label}</strong>`;
  if (subLabel) {
    const span = document.createElement('span');
    span.textContent = subLabel;
    labelEl.appendChild(span);
  }

  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = 'Download';
  button.addEventListener('click', action);

  wrapper.appendChild(labelEl);
  wrapper.appendChild(button);
  return wrapper;
}

function buildVideoOptions(metadata, apiUrl) {
  videoOptions.innerHTML = '';
  metadata.formats
    .sort((a, b) => (b.preference || 0) - (a.preference || 0))
    .forEach((format) => {
      const label = `${format.resolution || format.format_note || format.ext.toUpperCase()} • ${
        format.ext
      }`;
      const subLabel = `Size: ${formatFilesize(format.filesize)} · ${format.fps ? `${format.fps} fps` : 'Adaptive'}`;
      const downloadUrl = `${apiUrl}/download?url=${encodeURIComponent(metadata.webpage_url)}&format_id=${encodeURIComponent(
        format.format_id
      )}&filename=${encodeURIComponent(metadata.title)}`;
      videoOptions.appendChild(
        createOption({
          label,
          subLabel,
          action: () => window.open(downloadUrl, '_blank'),
        })
      );
    });

  if (!metadata.formats.length) {
    videoOptions.innerHTML = '<p class="empty">No video formats were found for this link.</p>';
  }
}

function buildAudioOptions(metadata, apiUrl) {
  audioOptions.innerHTML = '';

  metadata.audio_formats.forEach((format) => {
    const label = `${format.ext.toUpperCase()} • ${format.abr ? `${format.abr} kbps` : 'Audio'}`;
    const subLabel = `Size: ${formatFilesize(format.filesize)}`;
    const downloadUrl = `${apiUrl}/audio?url=${encodeURIComponent(metadata.webpage_url)}&format_id=${encodeURIComponent(
      format.format_id
    )}&filename=${encodeURIComponent(metadata.title)}`;

    audioOptions.appendChild(
      createOption({
        label,
        subLabel,
        action: () => window.open(downloadUrl, '_blank'),
      })
    );
  });

  // Generic MP3 option regardless of specific formats
  const mp3Url = `${apiUrl}/audio?url=${encodeURIComponent(metadata.webpage_url)}&filename=${encodeURIComponent(
    metadata.title
  )}`;
  audioOptions.appendChild(
    createOption({
      label: 'MP3 (best)',
      subLabel: 'Auto converts using best available audio track',
      action: () => window.open(mp3Url, '_blank'),
    })
  );
}

function updateMetadata(metadata, apiUrl) {
  videoTitle.textContent = metadata.title;
  videoAuthor.textContent = metadata.creator ? `by ${metadata.creator}` : '';
  videoDescription.textContent = metadata.description || '';
  videoThumbnail.src = metadata.thumbnail || '';
  videoDuration.textContent = formatDuration(metadata.duration);

  if (metadata.watermark_free_available) {
    formatAlert.textContent = 'Watermark-free video available! Choose a format labeled without watermark.';
    formatAlert.classList.remove('hidden');
  } else {
    formatAlert.classList.add('hidden');
  }

  buildVideoOptions(metadata, apiUrl);
  buildAudioOptions(metadata, apiUrl);

  resultSection.classList.remove('hidden');
}

async function fetchMetadata(url) {
  const apiUrl = `${window.location.origin}/api`;
  const response = await fetch(`${apiUrl}/metadata?url=${encodeURIComponent(url)}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: 'Unable to fetch video details.' }));
    throw new Error(data.detail || 'Unable to fetch video details.');
  }
  const metadata = await response.json();
  updateMetadata(metadata, apiUrl);
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const url = urlInput.value.trim();
  if (!url) return;

  hideError();
  resultSection.classList.add('hidden');
  toggleLoading(true);

  try {
    await fetchMetadata(url);
  } catch (err) {
    showError(err.message);
  } finally {
    toggleLoading(false);
  }
});
