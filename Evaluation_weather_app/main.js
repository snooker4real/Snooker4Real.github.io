//Make the search button work using the content of the input
const form = document.querySelector("form");
const inputVille = document.getElementById("rechercher");
const all = document.getElementById("all");
//console.log(all);
//const searchBtn = document.("searchBtn");
const weather = document.getElementById("weather");

// Connect to an API
function getWeather(ville = null) {
  let url =
    "https://api.openweathermap.org/data/2.5/weather?q=Paris&units=metric&lang=fr&appid=7f394d5a3d238f8c628b7d28151e4bc9";

  if (ville) {
    url = `https://api.openweathermap.org/data/2.5/weather?q=${ville}&units=metric&lang=fr&appid=7f394d5a3d238f8c628b7d28151e4bc9`;
  }
  const request = new XMLHttpRequest();

  request.open("GET", url, true);

  request.onload = () => {
    data = request.response;
    data = JSON.parse(data);
    printWeather(data);
    getBg();
  };

  request.send();
}

// Render the result
function printWeather(data) {
  weather.innerHTML = `
  <br>
    <div class="card">
      <h1>${data.name}, ${data.sys.country}</h1>
      <p><strong>Etat : </strong>${data.weather[0].description}</p>
      <p><strong>Température min : </strong>${data.main.temp_min}°C</p>
      <p><strong>Ressenti : </strong>${data.main.feels_like}°C</p>
      <p><strong>Température : </strong>${data.main.temp}°C</p>
      <p><strong>Température max : </strong>${data.main.temp_max}°C</p>
      <p>Il y'aura ${data.main.humidity}% d'humidité</p>
      <p>Avec une pression atmosphérique de ${data.main.pressure} hPa</p>
      <p>Le vent soufflera à ${data.wind.speed} km/h de vent</p>
      <p>Le vent soufflera en direction du degré ${data.wind.deg} </p>

    </div>
  `;
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  getWeather(inputVille.value);
});

function getBg() {
  if (data.weather[0].id >= 200 && data.weather[0].id <= 232) {
    //document.body.style.backgroundImage = "url(./assets/img/pluie.jpg)";
    all.classList.add("foudre");
  } else if (data.weather[0].id >= 300 && data.weather[0].id <= 531) {
    //document.body.style.backgroundImage = "url(./assets/img/nuage.jpg)";
    all.classList.add("pluie");
  } else if (data.weather[0].id >= 600 && data.weather[0].id <= 622) {
    //document.body.style.backgroundImage = "url(./assets/img/neige.jpg)";
    all.classList.add("neige");
  } else if (data.weather[0].id >= 701 && data.weather[0].id <= 781) {
    all.classList.add("brume");
  } else if (data.weather[0].id === 800) {
    //document.body.style.backgroundImage = "url(./assets/img/soleil.jpg)";
    all.classList.add("soleil");
  } else if (data.weather[0].id >= 801 && data.weather[0].id <= 804) {
    //document.body.style.backgroundImage = "url(./assets/img/nuage.jpg)";
    all.classList.add("nuage");
  }
}
