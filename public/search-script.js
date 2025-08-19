const sInput = document.getElementById('search-input');
const sButton = document.getElementById('search-button');
const sResults = document.getElementById('search-results');
const sSkeleton = document.getElementById('search-skeleton');

function showSearchSkeleton() {
  if (!sSkeleton) return;
  sSkeleton.classList.remove('hidden');
  sSkeleton.innerHTML = '';
  for (let i = 0; i < 10; i++) {
    const s = document.createElement('div');
    s.className = 's';
    sSkeleton.appendChild(s);
  }
}

async function performSearch() {
  const q = sInput.value.trim();
  if (!q) return;
  
  showSearchSkeleton();
  if (sResults) sResults.innerHTML = '';

  try {
    const res = await fetch(`/api/search?query=${encodeURIComponent(q)}`);
    const data = await res.json();
    
    if (sSkeleton) sSkeleton.classList.add('hidden');
    if (!sResults) return;

    if (data.error || !Array.isArray(data)) {
        sResults.innerHTML = '<div class="info-card">Search failed. Please try again.</div>';
        return;
    }

    if (data.length === 0) {
        sResults.innerHTML = '<div class="info-card">No results found for that query.</div>';
        return;
    }

    sResults.innerHTML = data.map(anime => `
      <article class="card">
        <a href="/anime.html?id=${anime.id}">
          <img class="thumb" src="${anime.image}" alt="${anime.title}" loading="lazy" />
          <div class="meta">
            <div class="title">${anime.title}</div>
          </div>
        </a>
      </article>
    `).join('');
  } catch (e) {
    console.error(e);
    if (sSkeleton) sSkeleton.classList.add('hidden');
    if (sResults) sResults.innerHTML = '<div class="info-card">An error occurred during the search.</div>';
  }
}

if (sButton) sButton.addEventListener('click', performSearch);
if (sInput) sInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') performSearch(); });
