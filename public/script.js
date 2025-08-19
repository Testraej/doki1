const grid = document.getElementById('anime-list');
const gridSkeleton = document.getElementById('grid-skeleton');

function renderSkeletons(container, count = 12) {
  if (!container) return;
  container.innerHTML = '';
  for (let i = 0; i < count; i++) {
    const s = document.createElement('div');
    s.className = 's';
    container.appendChild(s);
  }
}

async function loadRecent() {
  try {
    renderSkeletons(gridSkeleton, 12);
    const res = await fetch('/api/recent');
    const data = await res.json();
    
    if (gridSkeleton) gridSkeleton.classList.add('hidden');
    if (!grid) return;

    if (data.error || !Array.isArray(data) || data.length === 0) {
        grid.innerHTML = `<div class="info-card">Failed to load recent episodes. The source might be down.</div>`;
        return;
    }

    grid.innerHTML = data.map(anime => `
      <article class="card" role="article">
        <a href="/anime.html?id=${anime.id}" aria-label="Open ${anime.title}">
          <img class="thumb" src="${anime.image}" alt="${anime.title}" loading="lazy" />
          <div class="meta">
            <div class="title">${anime.title}</div>
            <p style="color: var(--text-secondary); font-size: 14px; margin-top: 4px;">${anime.episode_title}</p>
          </div>
        </a>
      </article>
    `).join('');
  } catch (err) {
    console.error(err);
    if (grid) grid.innerHTML = `<div class="info-card">An error occurred while loading data.</div>`;
  }
}

document.addEventListener('DOMContentLoaded', loadRecent);
