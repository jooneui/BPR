const stationData = window.PEAK_ATLAS_DATA?.stations ?? [];

const regionSelect = document.querySelector("#region-select");
const regionStrip = document.querySelector("#region-strip");
const yearSelect = document.querySelector("#year-select");
const yearOutput = document.querySelector("#year-output");
const legendYear = document.querySelector("#legend-year");
const regionName = document.querySelector("#region-name");
const regionBadge = document.querySelector("#region-badge");
const trendPill = document.querySelector("#trend-pill");
const headline = document.querySelector("#headline");
const summary = document.querySelector("#summary");
const amStart = document.querySelector("#am-start");
const amDuration = document.querySelector("#am-duration");
const pmStart = document.querySelector("#pm-start");
const pmDuration = document.querySelector("#pm-duration");
const shiftMagnitude = document.querySelector("#shift-magnitude");
const shiftDirection = document.querySelector("#shift-direction");
const storyCategory = document.querySelector("#story-category");
const timelineCaption = document.querySelector("#timeline-caption");
const mapCaption = document.querySelector("#map-caption");
const amBaselineBar = document.querySelector("#am-baseline-bar");
const amCurrentBar = document.querySelector("#am-current-bar");
const pmBaselineBar = document.querySelector("#pm-baseline-bar");
const pmCurrentBar = document.querySelector("#pm-current-bar");
const stationMarkers = document.querySelector("#station-markers");
const mapStationList = document.querySelector("#map-station-list");

const hoursToPercent = (hour) => ((hour - 0) / 24) * 100;
const durationToPercent = (duration) => (duration / 24) * 100;

function setBarStyles(element, segment) {
  element.style.left = `${hoursToPercent(segment.startHour)}%`;
  element.style.width = `${durationToPercent(segment.durationHour)}%`;
}

function findStation(stationId) {
  return stationData.find((station) => station.id === stationId);
}

function setActiveStationChip(stationId) {
  document.querySelectorAll(".region-chip").forEach((button) => {
    button.classList.toggle("active", button.dataset.region === stationId);
  });
  document.querySelectorAll(".station-marker").forEach((button) => {
    button.classList.toggle("active", button.dataset.region === stationId);
  });
  document.querySelectorAll(".map-station-item").forEach((button) => {
    button.classList.toggle("active", button.dataset.region === stationId);
  });
}

function syncYearOptions(station) {
  const selectedYear = yearSelect.value;
  yearSelect.innerHTML = "";

  Object.keys(station.years)
    .sort()
    .forEach((year) => {
      const option = document.createElement("option");
      option.value = year;
      option.textContent = year;
      if (year === selectedYear || (!selectedYear && year === Object.keys(station.years)[0])) {
        option.selected = true;
      }
      yearSelect.appendChild(option);
    });
}

function renderStation() {
  const station = findStation(regionSelect.value);
  if (!station) {
    return;
  }

  syncYearOptions(station);
  const selectedYear = yearSelect.value || Object.keys(station.years)[0];
  const current = station.years[selectedYear];

  yearOutput.textContent = selectedYear;
  legendYear.textContent = "PM";
  regionName.textContent = station.name;
  regionBadge.textContent = station.name;
  trendPill.textContent = station.trend;
  headline.textContent = `${station.name} shows a ${station.trend.toLowerCase()}.`;
  summary.textContent = station.summary;
  amStart.textContent = current.am.start;
  amDuration.textContent = current.am.duration;
  pmStart.textContent = current.pm.start;
  pmDuration.textContent = current.pm.duration;
  shiftMagnitude.textContent = `${current.am.coverage}%`;
  shiftDirection.textContent = `${current.pm.coverage}%`;
  storyCategory.textContent = station.dataSource;
  timelineCaption.textContent = `Median detected AM and PM peaks in ${selectedYear}`;
  mapCaption.textContent = `${station.map.corridor} · ${selectedYear} pilot summary`;

  setBarStyles(amBaselineBar, current.am);
  amCurrentBar.style.left = "0%";
  amCurrentBar.style.width = "0%";
  pmBaselineBar.style.left = "0%";
  pmBaselineBar.style.width = "0%";
  setBarStyles(pmCurrentBar, current.pm);
  setActiveStationChip(station.id);
}

if (!stationData.length) {
  headline.textContent = "No station data is loaded yet.";
  summary.textContent = "Run the site-data generator after peak outputs are available.";
} else {
  stationData.forEach((station, index) => {
    const option = document.createElement("option");
    option.value = station.id;
    option.textContent = station.name;
    if (index === 0) {
      option.selected = true;
    }
    regionSelect.appendChild(option);

    const firstYear = Object.keys(station.years).sort()[0];
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "region-chip";
    chip.dataset.region = station.id;
    chip.innerHTML = `<span>${station.storyCategory} · ${firstYear}</span><strong>${station.name}</strong>`;
    chip.addEventListener("click", () => {
      regionSelect.value = station.id;
      renderStation();
    });
    regionStrip.appendChild(chip);

    const marker = document.createElement("button");
    marker.type = "button";
    marker.className = "station-marker";
    marker.dataset.region = station.id;
    marker.title = `${station.name} · ${station.map.corridor}`;
    marker.style.left = `${station.map.x}%`;
    marker.style.top = `${station.map.y}%`;
    marker.addEventListener("click", () => {
      regionSelect.value = station.id;
      renderStation();
    });
    stationMarkers.appendChild(marker);

    const stationListItem = document.createElement("button");
    stationListItem.type = "button";
    stationListItem.className = "map-station-item";
    stationListItem.dataset.region = station.id;
    stationListItem.innerHTML = `<div><strong>${station.name}</strong><span>${station.map.corridor}</span></div><span>${station.trend}</span>`;
    stationListItem.addEventListener("click", () => {
      regionSelect.value = station.id;
      renderStation();
    });
    mapStationList.appendChild(stationListItem);
  });

  regionSelect.addEventListener("change", renderStation);
  yearSelect.addEventListener("change", renderStation);

  renderStation();
}
