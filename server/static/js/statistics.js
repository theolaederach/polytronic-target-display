document.addEventListener("DOMContentLoaded", () => {
  const shooter_selector = document.getElementById("shooter_selector");
  const api_shooters = "/api/shooters/name/all";

  async function get_all_shooters() {
    const request = await fetch(api_shooters);
    const reponse = await request.json();
    reponse.shooters_number.forEach(append_shooter_name);
  }
  function append_shooter_name(item) {
    const new_option = document.createElement("option");
    new_option.value = item[0];
    new_option.text = item[2];

    shooter_selector.appendChild(new_option);
  }

  get_all_shooters();

  const form = shooter_selector.closest("form");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const shooter = shooter_selector.value;
    if (shooter) {
      window.location.href = `/statistics/${shooter}`;
    }
  });
});
