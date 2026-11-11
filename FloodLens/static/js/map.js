/**
 * FLOODLENS - Interactive Leaflet & NASA GIBS Geospatial Engine
 * Configured with 100% Free, Public Basemaps (ZERO API Key Required)
 */

const FLOOD_MAP = {
  map: null,
  activeMarker: null,
  reportsLayerGroup: null,
  gibsLayerGroup: null,
  gibsLayer: null,
  currentLayerId: 'MODIS_Terra_CorrectedReflectance_Bands721',
  currentDate: null,

  getDefaultDate() {
    // Yesterday in UTC (YYYY-MM-DD)
    const d = new Date();
    d.setUTCDate(d.getUTCDate() - 1);
    return d.toISOString().split('T')[0];
  },

  createGibsTileLayer(layerId, dateStr) {
    const id = layerId || this.currentLayerId;
    const date = dateStr || this.currentDate || this.getDefaultDate();
    let matrixSet = "GoogleMapsCompatible_Level9";
    let format = "jpg";

    if (id === "IMERG_Precipitation_Rate") {
      matrixSet = "GoogleMapsCompatible_Level6";
      format = "png";
    }

    const tileUrl = `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${id}/default/${date}/${matrixSet}/{z}/{y}/{x}.${format}`;

    return L.tileLayer(tileUrl, {
      attribution: 'NASA GIBS',
      maxZoom: 9,
      opacity: 0.85,
      transparent: format === 'png'
    });
  },

  init(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container || typeof L === 'undefined') return;

    const loc = FLOODLENS.getLocation();
    const zoomLevel = options.zoom || 11;
    this.currentDate = this.getDefaultDate();

    // 1. BASE LAYER DEFINITIONS (100% Free - NO API KEY REQUIRED)
    // A. Esri Dark Gray Canvas - Perfect dark slate GIS basemap (NO API KEY)
    const esriDark = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
      maxZoom: 16
    });

    // B. High-resolution Esri World Satellite Imagery (NO API KEY)
    const esriSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP',
      maxZoom: 18
    });

    // C. Dark Mode OpenStreetMap (OSM with custom dark CSS filter - NO API KEY)
    const osmDark = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      className: 'dark-osm-tiles',
      maxZoom: 19
    });

    // D. Standard OpenStreetMap (NO API KEY)
    const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19
    });

    // Initialize Leaflet map with zoom control positioned cleanly at bottom-left
    // to prevent overlap with the floating station HUD card
    this.map = L.map(containerId, {
      center: [loc.lat, loc.lon],
      zoom: zoomLevel,
      zoomControl: false,
      layers: [esriDark]
    });

    // Add zoom control at bottom-left
    L.control.zoom({ position: 'bottomleft' }).addTo(this.map);

    // 2. Layer Groups & Controls
    const baseMaps = {
      "Dark Slate (Esri)": esriDark,
      "Dark OpenStreetMap": osmDark,
      "Esri Satellite": esriSat,
      "OpenStreetMap Standard": osm
    };

    this.reportsLayerGroup = L.layerGroup().addTo(this.map);
    this.gibsLayerGroup = L.layerGroup();

    // Create default GIBS layer and add to group
    this.gibsLayer = this.createGibsTileLayer();
    this.gibsLayerGroup.addLayer(this.gibsLayer);

    // If on satellite page or requested, activate GIBS overlay by default
    if (options.enableGibsByDefault) {
      this.gibsLayerGroup.addTo(this.map);
    }

    const overlayMaps = {
      "NASA GIBS Satellite": this.gibsLayerGroup,
      "Community Reports": this.reportsLayerGroup
    };

    L.control.layers(baseMaps, overlayMaps, { position: 'topright' }).addTo(this.map);

    // 3. Add active monitoring marker
    this.updateActiveMarker(loc.lat, loc.lon, loc.name);

    // 4. Load community flood report pins
    this.loadCommunityReports();

    // 5. Click on map to select and re-evaluate location
    if (options.enableClickSelection !== false) {
      this.map.on('click', (e) => {
        const lat = parseFloat(e.latlng.lat.toFixed(4));
        const lon = parseFloat(e.latlng.lng.toFixed(4));
        const customName = `Location (${lat}°, ${lon}°)`;
        FLOODLENS.setLocation(lat, lon, customName);
        this.updateActiveMarker(lat, lon, customName);
        FLOODLENS.showToast(`Monitoring shifted to coordinates: ${lat}, ${lon}`, 'info');
      });
    }

    // Listen to global location changes
    window.addEventListener('fl:locationChanged', (e) => {
      const { lat, lon, name } = e.detail;
      this.updateActiveMarker(lat, lon, name);
      this.map.panTo([lat, lon]);
    });

    return this.map;
  },

  // Update center marker with pulsing beacon style
  updateActiveMarker(lat, lon, name) {
    if (!this.map) return;

    if (this.activeMarker) {
      this.map.removeLayer(this.activeMarker);
    }

    const iconHtml = `
      <div style="position:relative; width:24px; height:24px;">
        <div style="position:absolute; width:100%; height:100%; border-radius:50%; background:#00f0ff; opacity:0.8; animation: beacon-pulse 2s infinite;"></div>
        <div style="position:absolute; top:4px; left:4px; width:16px; height:16px; border-radius:50%; background:#0284c7; border:2px solid #ffffff;"></div>
      </div>
    `;

    const customIcon = L.divIcon({
      className: 'custom-beacon-marker',
      html: iconHtml,
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });

    this.activeMarker = L.marker([lat, lon], { icon: customIcon })
      .addTo(this.map)
      .bindPopup(`
        <div style="font-family:'Inter',sans-serif; padding:4px;">
          <h6 style="color:#38bdf8; margin:0 0 4px 0; font-size:0.9rem;">${name}</h6>
          <p style="margin:0; font-size:0.75rem; color:#94a3b8;">
            Coordinates: <strong>${lat}°, ${lon}°</strong><br>
            Active monitoring focus.
          </p>
        </div>
      `);
  },

  // Set or switch NASA GIBS WMTS Layer
  setGibsLayer(layerId, dateStr) {
    if (!this.map) return;
    this.currentLayerId = layerId || this.currentLayerId;
    this.currentDate = dateStr || this.currentDate || this.getDefaultDate();

    // Clear and rebuild within gibsLayerGroup
    if (this.gibsLayerGroup) {
      this.gibsLayerGroup.clearLayers();
      this.gibsLayer = this.createGibsTileLayer(this.currentLayerId, this.currentDate);
      this.gibsLayerGroup.addLayer(this.gibsLayer);
      
      // Ensure group is on map
      if (!this.map.hasLayer(this.gibsLayerGroup)) {
        this.gibsLayerGroup.addTo(this.map);
      }
    }
  },

  // Fetch and display community reports as interactive markers
  loadCommunityReports() {
    if (!this.reportsLayerGroup) return;

    fetch('/api/reports')
      .then(res => res.json())
      .then(data => {
        if (!data.success || !data.reports) return;

        this.reportsLayerGroup.clearLayers();

        data.reports.forEach(report => {
          let color = '#38bdf8';
          if (report.severity === 'Minor') color = '#10b981';
          else if (report.severity === 'Moderate') color = '#f59e0b';
          else if (report.severity === 'Severe') color = '#f97316';
          else if (report.severity === 'Critical') color = '#ef4444';

          const markerIcon = L.divIcon({
            className: 'report-pin',
            html: `
              <div style="background:${color}; width:16px; height:16px; border-radius:50%; border:2px solid #ffffff; box-shadow:0 0 10px ${color};"></div>
            `,
            iconSize: [16, 16],
            iconAnchor: [8, 8]
          });

          const marker = L.marker([report.latitude, report.longitude], { icon: markerIcon });
          marker.bindPopup(`
            <div style="max-width:240px; font-family:'Inter',sans-serif;">
              <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
                <span class="badge" style="background:${color}; color:#fff; font-size:0.7rem;">${report.severity}</span>
                <span style="font-size:0.65rem; color:#f87171; border:1px solid #f87171; padding:1px 4px; border-radius:4px;">Unverified</span>
              </div>
              <strong style="color:#ffffff; font-size:0.85rem; display:block; margin-bottom:4px;">${report.location_name}</strong>
              <p style="font-size:0.75rem; color:#cbd5e1; margin-bottom:6px;">${report.description}</p>
              <div style="font-size:0.7rem; color:#94a3b8; border-top:1px solid rgba(255,255,255,0.1); padding-top:4px;">
                <span>Depth: <strong>${report.water_depth}</strong></span><br>
                <span>Reported: ${report.time_ago}</span>
              </div>
            </div>
          `);

          this.reportsLayerGroup.addLayer(marker);
        });
      })
      .catch(err => console.error("Error loading community reports:", err));
  }
};
