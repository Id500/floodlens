/**
 * FLOODLENS - Core Dashboard & State Management
 */

const FLOODLENS = {
  // Defaults
  DEFAULT_LAT: 13.0827,
  DEFAULT_LON: 80.2707,
  DEFAULT_NAME: "Chennai, Tamil Nadu, India",

  // Retrieve current active location from sessionStorage
  getLocation() {
    const lat = parseFloat(sessionStorage.getItem('fl_lat')) || this.DEFAULT_LAT;
    const lon = parseFloat(sessionStorage.getItem('fl_lon')) || this.DEFAULT_LON;
    const name = sessionStorage.getItem('fl_name') || this.DEFAULT_NAME;
    return { lat, lon, name };
  },

  // Save new active location and dispatch update event
  setLocation(lat, lon, name) {
    sessionStorage.setItem('fl_lat', lat);
    sessionStorage.setItem('fl_lon', lon);
    sessionStorage.setItem('fl_name', name);
    this.updateTopbarUI();

    // Broadcast event for active page scripts (map, charts, risk engine)
    window.dispatchEvent(new CustomEvent('fl:locationChanged', {
      detail: { lat, lon, name }
    }));
  },

  // Update topbar display elements
  updateTopbarUI() {
    const loc = this.getLocation();
    const nameEl = document.getElementById('current-location-text');
    const coordsEl = document.getElementById('current-coords-text');

    if (nameEl) {
      // Shorten long administrative names for topbar chip
      const shortName = loc.name.split(',').slice(0, 2).join(', ');
      nameEl.textContent = shortName;
      nameEl.title = loc.name;
    }
    if (coordsEl) {
      coordsEl.textContent = `${loc.lat.toFixed(4)}°, ${loc.lon.toFixed(4)}°`;
    }
  },

  // Format numbers cleanly
  formatNum(val, decimals = 1) {
    if (val === null || val === undefined || isNaN(val)) return '—';
    return Number(val).toFixed(decimals);
  },

  // Show Toast / Notification
  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : (type === 'success' ? 'success' : 'info')} position-fixed top-0 end-0 m-4 shadow-lg`;
    toast.style.zIndex = '9999';
    toast.style.minWidth = '280px';
    toast.innerHTML = `<i class="bi bi-info-circle me-2"></i> ${message}`;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.4s ease';
      setTimeout(() => toast.remove(), 400);
    }, 3500);
  }
};

// Initialize Topbar & Search when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  FLOODLENS.updateTopbarUI();

  // Search input geocoding with debounce
  const searchInput = document.getElementById('global-search-input');
  const searchResults = document.getElementById('search-results-box');
  let debounceTimer = null;

  if (searchInput && searchResults) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      clearTimeout(debounceTimer);

      if (query.length < 2) {
        searchResults.style.display = 'none';
        searchResults.innerHTML = '';
        return;
      }

      debounceTimer = setTimeout(() => {
        fetch(`/api/geocode?q=${encodeURIComponent(query)}`)
          .then(res => res.json())
          .then(data => {
            searchResults.innerHTML = '';
            if (data.results && data.results.length > 0) {
              data.results.forEach(item => {
                const div = document.createElement('div');
                div.className = 'search-result-item';
                div.innerHTML = `<i class="bi bi-geo-alt-fill text-info me-2"></i><strong>${item.name}</strong>`;
                div.addEventListener('click', () => {
                  FLOODLENS.setLocation(item.latitude, item.longitude, item.name);
                  searchResults.style.display = 'none';
                  searchInput.value = '';
                  FLOODLENS.showToast(`Monitoring shifted to ${item.name.split(',')[0]}`, 'success');
                });
                searchResults.appendChild(div);
              });
              searchResults.style.display = 'block';
            } else {
              searchResults.innerHTML = '<div class="p-3 text-muted small">No matches found. Try entering city name.</div>';
              searchResults.style.display = 'block';
            }
          })
          .catch(() => {
            searchResults.style.display = 'none';
          });
      }, 350);
    });

    // Close dropdown on click outside
    document.addEventListener('click', (e) => {
      if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.style.display = 'none';
      }
    });
  }

  // Sidebar toggle for mobile devices
  const sidebarToggle = document.getElementById('sidebar-toggle-btn');
  const sidebar = document.querySelector('.app-sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('show');
    });
  }
});

