const detailRoot = document.getElementById('detail-root');
const episodeList = document.getElementById('episode-list');
const videoContainer = document.getElementById('video-player-container');
let currentAnimeId = '';

function getParam(name) {
  return new URLSearchParams(location.search).get(name);
}

async function loadEpisode(episodeId) {
  if (!videoContainer) return;
  videoContainer.innerHTML = '<p style="text-align: center; padding: 20px;">Loading episode...</p>';

  try {
    const fullEpisodeId = `${currentAnimeId},${episodeId}`;
    const response = await fetch(`/api/stream/${fullEpisodeId}`);
    const data = await response.json();

    if (data.error || !data.stream_url) {
      videoContainer.innerHTML = `<p style="text-align: center; color: var(--brand-primary); padding: 20px;">${data.error || 'No video source was found for this episode.'}</p>`;
      return;
    }

    videoContainer.innerHTML = '<video id="player" controls autoplay style="width: 100%; border-radius: 8px; aspect-ratio: 16/9;"></video>';
    const video = document.getElementById('player');

    if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(data.stream_url);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = data.stream_url;
      video.addEventListener('loadedmetadata', () => video.play());
    }
  } catch (err) {
    console.error('Error loading episode:', err);
    videoContainer.innerHTML = '<p style="text-align: center; padding: 20px;">Could not load the episode. The API might be down.</p>';
  }
}

async function loadDetails() {
  currentAnimeId = getParam('id');
  if (!currentAnimeId) return;

  if (detailRoot) detailRoot.innerHTML = '<div class="grid-skeleton"><div class="s"></div></div>';

  try {
    const res = await fetch(`/api/details/${currentAnimeId}`);
    const anime = await res.json();

    if (anime.error) {
        if (detailRoot) detailRoot.innerHTML = `<div class="info-card">${anime.error}</div>`;
        return;
    }

    if (detailRoot) {
      detailRoot.innerHTML = `
        <div class="detail-wrap">
            <img class="poster" src="${anime.image}" alt="${anime.title} poster" />
            <div class="info-card-details">
                <h1 style="margin-top:0">${anime.title}</h1>
                <p class="description">${anime.description || 'No description available.'}</p>
            </div>
        </div>
      `;
    }

    if (episodeList) {
      episodeList.innerHTML = '';
      if (anime.episodes && anime.episodes.length > 0) {
        anime.episodes.forEach(episode => {
          const button = document.createElement('button');
          button.className = 'badge';
          button.style.cursor = 'pointer';
          button.textContent = `Episode ${episode.number}`;
          button.onclick = () => loadEpisode(episode.id);
          episodeList.appendChild(button);
        });
      } else {
        episodeList.innerHTML = 'No episodes found.';
      }
    }
  } catch (e) {
    console.error(e);
    if (detailRoot) detailRoot.innerHTML = '<div class="info-card">Failed to load details.</div>';
  }
}

document.addEventListener('DOMContentLoaded', loadDetails);