"use strict";

/*
 * Groups page : click on a group to edit or delete it in a popup.
 * The popup is a native <dialog> : Escape closes it, the focus stays inside,
 * and the page behind cannot be clicked while it is open.
 */
(() => {
    const dialog = document.getElementById("group-dialog");
    if (!dialog) return;

    const editForm = document.getElementById("edit-group-form");
    const deleteForm = document.getElementById("delete-group-form");
    const deleteButton = document.getElementById("delete-group-button");
    const idBadge = document.getElementById("group-dialog-id");

    const DELETE_LABEL = deleteButton.textContent.trim();
    const CONFIRM_LABEL = "Click again to confirm";
    const CONFIRM_DELAY_MS = 4000;
    let confirmTimer = null;

    /** Put the delete button back to its first state (not armed). */
    function resetDeleteButton() {
        clearTimeout(confirmTimer);
        delete deleteButton.dataset.armed;
        deleteButton.classList.remove("armed");
        deleteButton.textContent = DELETE_LABEL;
    }

    /**
     * Fill the popup with the data of a table row, then open it.
     * @param {HTMLTableRowElement} row - row with the data-* attributes of a group.
     */
    function openFromRow(row) {
        const data = row.dataset;

        // each form posts to the URL of this group
        editForm.action = data.editUrl;
        deleteForm.action = data.deleteUrl;

        editForm.elements["name"].value = data.name;
        editForm.elements["society"].value = data.societyId;
        JSON.parse(data.shooters).forEach((number, index) => {
            editForm.elements[`shooter_${index + 1}`].value =
                number === null ? "" : number;
        });

        // errors of a previous submit do not belong to this group
        const errors = dialog.querySelector("[data-edit-errors]");
        if (errors) errors.remove();

        idBadge.textContent = `#${data.groupId}`;
        resetDeleteButton();
        dialog.showModal();

        // with a mouse : ready to type. On a touch screen we do not focus the
        // field, because the keyboard would hide half of the popup.
        if (window.matchMedia("(hover: hover)").matches) {
            editForm.elements["name"].focus();
        }
    }

    // one listener on the table (event delegation) : works for every row
    document.querySelector(".groups-table").addEventListener("click", (event) => {
        const row = event.target.closest("tr[data-group-id]");
        if (row) openFromRow(row);
    });

    // close with the X and Cancel buttons
    dialog.querySelectorAll("[data-close]").forEach((button) => {
        button.addEventListener("click", () => dialog.close());
    });

    // close with a click on the dark background (the dialog has no padding,
    // so a click that targets the dialog itself is outside of its content)
    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) dialog.close();
    });

    dialog.addEventListener("close", resetDeleteButton);

    // Deleting needs two clicks : the first one only asks for a confirmation.
    // Without JavaScript, the form is simply sent.
    deleteForm.addEventListener("submit", (event) => {
        if (deleteButton.dataset.armed === "true") return; // 2nd click : send

        event.preventDefault();
        deleteButton.dataset.armed = "true";
        deleteButton.classList.add("armed");
        deleteButton.textContent = CONFIRM_LABEL;
        confirmTimer = setTimeout(resetDeleteButton, CONFIRM_DELAY_MS);
    });

    // the server sends the page with the popup already filled when the edit
    // has errors : we only have to open it
    if (dialog.hasAttribute("data-autoopen")) dialog.showModal();
})();
