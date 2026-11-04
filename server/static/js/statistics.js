document.addEventListener("DOMContentLoaded", () => {
  const shooter_selector = document.getElementById("shooter_selector");
  const api_shooters = "/api/shooters/name/all";

  async function get_all_shooters() {
    const request = await fetch(api_shooters);
    const reponse = await request.json();
    console.log(reponse);
    reponse.shooters_number.forEach(append_shooter_name);
  }
  function append_shooter_name(item) {
    const new_option = document.createElement("option");
    new_option.value = item;
    new_option.text = item;

    shooter_selector.appendChild(new_option);
  }

  get_all_shooters();
});
