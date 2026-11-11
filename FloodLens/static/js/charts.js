/**
 * FLOODLENS - Chart.js Data Visualizations
 * Dark theme customized styling for meteorological and hydrological charts
 */

const FLOOD_CHARTS = {
  // Chart instances
  hourlyChart: null,
  dailyChart: null,
  riverChart: null,
  radarChart: null,

  // Global default dark theme options
  applyDarkDefaults() {
    if (typeof Chart === 'undefined') return;
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(11, 19, 43, 0.95)';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(56, 189, 248, 0.3)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.titleColor = '#ffffff';
    Chart.defaults.plugins.tooltip.bodyColor = '#f8fafc';
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
  },

  // 1. Render 24-Hour Precipitation & Temperature Hybrid Chart
  renderHourlyChart(canvasId, hourlyData) {
    this.applyDarkDefaults();
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.hourlyChart) {
      this.hourlyChart.destroy();
    }

    this.hourlyChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: hourlyData.labels,
        datasets: [
          {
            type: 'line',
            label: 'Temperature (°C)',
            data: hourlyData.temperatures,
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.1)',
            yAxisID: 'yTemp',
            tension: 0.35,
            fill: true,
            pointRadius: 2,
            pointHoverRadius: 5
          },
          {
            type: 'bar',
            label: 'Precipitation (mm)',
            data: hourlyData.precipitations,
            backgroundColor: 'rgba(14, 165, 233, 0.65)',
            borderColor: '#0284c7',
            borderWidth: 1,
            borderRadius: 4,
            yAxisID: 'yPrecip'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#64748b', maxTicksLimit: 12 }
          },
          yTemp: {
            type: 'linear',
            position: 'left',
            title: { display: true, text: 'Temp (°C)', color: '#38bdf8' },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          },
          yPrecip: {
            type: 'linear',
            position: 'right',
            title: { display: true, text: 'Precipitation (mm)', color: '#0ea5e9' },
            grid: { drawOnChartArea: false },
            min: 0,
            suggestedMax: 10
          }
        }
      }
    });
  },

  // 2. Render 7-Day Rainfall Forecast Chart
  renderDailyChart(canvasId, dailyList) {
    this.applyDarkDefaults();
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.dailyChart) {
      this.dailyChart.destroy();
    }

    const labels = dailyList.map(d => d.date.split('-').slice(1).join('/'));
    const precipSums = dailyList.map(d => d.precipitation_sum);
    const rainProbs = dailyList.map(d => d.precipitation_probability_max);

    this.dailyChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            type: 'bar',
            label: 'Expected Rainfall (mm)',
            data: precipSums,
            backgroundColor: 'rgba(56, 189, 248, 0.65)',
            borderRadius: 6,
            yAxisID: 'yRain'
          },
          {
            type: 'line',
            label: 'Rain Probability (%)',
            data: rainProbs,
            borderColor: '#f59e0b',
            borderWidth: 2,
            borderDash: [5, 5],
            pointRadius: 4,
            pointBackgroundColor: '#f59e0b',
            yAxisID: 'yProb'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.05)' } },
          yRain: {
            type: 'linear',
            position: 'left',
            title: { display: true, text: 'Rainfall (mm)' },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          },
          yProb: {
            type: 'linear',
            position: 'right',
            max: 100,
            min: 0,
            title: { display: true, text: 'Probability (%)' },
            grid: { drawOnChartArea: false }
          }
        }
      }
    });
  },

  // 3. Render River Discharge Hydrograph (Past 7 Days + Forecast 7 Days)
  renderRiverDischargeChart(canvasId, riverChartData, historicalMean) {
    this.applyDarkDefaults();
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.riverChart) {
      this.riverChart.destroy();
    }

    const dates = riverChartData.dates || [];
    const discharge = riverChartData.discharge || [];
    const formattedDates = dates.map(d => d.split('-').slice(1).join('/'));

    // Create baseline reference line array
    const meanLine = dates.map(() => historicalMean || null);

    this.riverChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: formattedDates,
        datasets: [
          {
            label: 'Model Discharge (m³/s)',
            data: discharge,
            borderColor: '#22d3ee',
            backgroundColor: 'rgba(34, 211, 238, 0.15)',
            fill: true,
            tension: 0.3,
            borderWidth: 2.5,
            pointRadius: 3,
            pointHoverRadius: 6
          },
          {
            label: 'Historical Seasonal Baseline (m³/s)',
            data: meanLine,
            borderColor: '#f43f5e',
            borderWidth: 2,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top' }
        },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.05)' } },
          y: {
            title: { display: true, text: 'Discharge (m³/s)' },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          }
        }
      }
    });
  },

  // 4. Render Radar Chart for Multi-Factor Explainable AI Risk Attribution
  renderRiskRadar(canvasId, factors) {
    this.applyDarkDefaults();
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.radarChart) {
      this.radarChart.destroy();
    }

    const labels = factors.map(f => f.name.replace('Rainfall ', '').replace(' Antecedent', ''));
    const scores = factors.map(f => f.factor_score);

    this.radarChart = new Chart(ctx, {
      type: 'radar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Factor Hazard Score (0-100)',
          data: scores,
          backgroundColor: 'rgba(56, 189, 248, 0.25)',
          borderColor: '#38bdf8',
          borderWidth: 2,
          pointBackgroundColor: '#00f0ff',
          pointBorderColor: '#ffffff',
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
            grid: { color: 'rgba(255, 255, 255, 0.08)' },
            pointLabels: { color: '#94a3b8', font: { size: 11 } },
            ticks: { backdropColor: 'transparent', color: '#64748b', stepSize: 25 },
            min: 0,
            max: 100
          }
        }
      }
    });
  }
};

