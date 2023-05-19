function gridedit_init() {
  window.gridedit = {
    grid_document: {
      name: "Document",
      width: 0,
      height: 0,
      contents: null,
      set_value: function (cell, value) {
        this.contents[cell[1] * this.width + cell[0]] = value;
      },
      get_value: function (cell) {
        return this.contents[cell[1] * this.width + cell[0]];
      },
      edit_mask: [],
    },
    on_update: null,
    allow_update: false,
    editing_cell: null,
    use_color_input: (function () {
      try {
        const input = document.createElement("input");
        input.type = "color";
        input.value = "!";
        return input.type === "color" && input.value !== "!";
      } catch (e) {
        return false;
      }
    })(),
    set_allow_update: function (au) {
      this.allow_update = au;

      if (this.allow_update) {
        document
          .getElementById("update-button")
          .classList.remove("button-disabled");
      } else {
        document
          .getElementById("update-button")
          .classList.add("button-disabled");
      }
    },
    update_button_click: function () {
      if (this.allow_update) {
        if (this.editing_cell !== null) {
          if (this.end_cell_edit() !== true) return;
        }

        if (this.on_update !== null)
          this.on_update({
            width: this.grid_document.width,
            height: this.grid_document.height,
            contents: this.grid_document.contents.slice(),
            edit_mask: this.grid_document.edit_mask,
            name: this.grid_document.name,
          });
      }
    },
    grid_document_valid: function () {
      if (this.grid_document.width < 1 || this.grid_document.height < 1)
        return false;

      if (!Array.isArray(this.grid_document.contents)) return false;

      if (
        this.grid_document.contents.length <
        this.grid_document.width * this.grid_document.height
      )
        return false;

      return true;
    },
    cells_equal(cell1, cell2) {
      return cell1[0] === cell2[0] && cell1[1] === cell2[1];
    },
    cell_reference_valid: function (cell) {
      if (cell.length != 2) return false;

      if (cell[0] < 0 || cell[0] >= this.grid_document.width) return false;

      if (cell[1] < 0 || cell[1] >= this.grid_document.height) return false;

      return true;
    },
    get_cell_property: function (cell, prop, def) {
      if (!this.grid_document_valid()) return def;

      if (!this.cell_reference_valid(cell)) return def;

      var actual_prop = def;

      for (let i = 0; i < this.grid_document.edit_mask.length; i++) {
        var col_applies = false;
        var row_applies = false;

        if (this.grid_document.edit_mask[i].col === null) col_applies = true;

        if (this.grid_document.edit_mask[i].row === null) row_applies = true;

        if (this.grid_document.edit_mask[i].col === cell[0]) col_applies = true;

        if (this.grid_document.edit_mask[i].row === cell[1]) row_applies = true;

        if (col_applies && row_applies) {
          /* The last edit mask rule specified applies */
          if (this.grid_document.edit_mask[i].hasOwnProperty(prop))
            actual_prop = this.grid_document.edit_mask[i][prop];
        }
      }

      return actual_prop;
    },
    end_cell_edit: function () {
      if (
        !this.grid_document_valid() ||
        !this.cell_reference_valid(this.editing_cell)
      )
        return;

      var cell_type = this.get_cell_property(this.editing_cell, "type", "text");

      if (cell_type === "color" && this.use_color_input) {
        this.grid_document.set_value(
          this.editing_cell,
          document.getElementById("color-selector").value
        );
      } else if (cell_type === "number") {
        /* First check if a number is entered */

        var cell_input = document.getElementById(
          "input-" + this.editing_cell[0] + "-" + this.editing_cell[1]
        ).value;

        if (cell_type === "color") {
          this.grid_document.set_value(this.editing_cell, cell_input);
        } else if (cell_input.trim() === "NA") {
          this.grid_document.set_value(this.editing_cell, "NA");
        } else {
          if (Number.isNaN(Number.parseFloat(cell_input))) {
            var cell = this.editing_cell.slice();
            this.editing_cell = null;

            this.begin_cell_edit(cell, true, cell_input);
            return false;
          }

          var in_bounds = true;
          var min = this.get_cell_property(this.editing_cell, "min", null);
          var max = this.get_cell_property(this.editing_cell, "max", null);

          if (min !== null && cell_input < min) in_bounds = false;

          if (max !== null && cell_input > max) in_bounds = false;

          if (!in_bounds) {
            var cell = this.editing_cell.slice();
            this.editing_cell = null;

            this.begin_cell_edit(cell, true, cell_input);
            return false;
          }

          this.grid_document.set_value(this.editing_cell, cell_input);
        }
      } else {
        this.grid_document.set_value(
          this.editing_cell,
          document.getElementById(
            "input-" + this.editing_cell[0] + "-" + this.editing_cell[1]
          ).value
        );
      }

      this.editing_cell = null;

      this.draw_grid_document();

      return true;
    },
    begin_cell_edit: function (cell, error = false, value = null) {
      if (!this.grid_document_valid() || !this.cell_reference_valid(cell))
        return;

      if (this.editing_cell !== null) {
        this.end_cell_edit(this.editing_cell);
      }
      /* Cells are editable by default */
      if (!this.get_cell_property(cell, "editable", true)) return;

      var cell_type = this.get_cell_property(cell, "type", "text");
      var cell_value = value || this.grid_document.get_value(cell);

      if (cell_type === "color" && this.use_color_input) {
        document.getElementById("color-selector").value = cell_value;

        document.getElementById("color-selector").onchange = (function (c) {
          return function (e) {
            window.gridedit.end_cell_edit();
          };
        })(cell);

        document.getElementById("color-selector").click();
      } else {
        document.getElementById("cell-" + cell[0] + "-" + cell[1]).innerHTML =
          "";
        document.getElementById(
          "cell-" + cell[0] + "-" + cell[1]
        ).style.backgroundColor = "#fff";

        var cell_input = document.createElement("input");
        cell_input.id = "input-" + cell[0] + "-" + cell[1];
        cell_input.type = cell_type === "text";
        cell_input.value = cell_value;
        cell_input.style.width =
          document.getElementById("cell-" + cell[0] + "-" + cell[1])
            .clientWidth + "px";

        /* For number inputs we need to allow people to enter floats, and include max and min (if they are defined)
                if(cell_type == "number")
                {
                    var step = this.get_cell_property(cell, 'step', '0.001');
                    var min = this.get_cell_property(cell, 'min', null);
                    var max = this.get_cell_property(cell, 'max', null);

                    cell_input.step = step;

                    if(min !== null)
                        cell_input.min = min;
                    
                    if(max !== null)
                        cell_input.max = max;
                }*/

        cell_input.onclick = function (e) {
          e.stopPropagation();
        };

        if (error)
          document
            .getElementById("cell-" + cell[0] + "-" + cell[1])
            .classList.add("editing-error");
        else
          document
            .getElementById("cell-" + cell[0] + "-" + cell[1])
            .classList.add("editing");

        /* End editing upon keying return */
        cell_input.onkeyup = (function (c) {
          return function (e) {
            e.preventDefault();

            if (e.keyCode === 13) {
              window.gridedit.end_cell_edit(c);
            }
          };
        })(cell);

        document
          .getElementById("cell-" + cell[0] + "-" + cell[1])
          .appendChild(cell_input);

        cell_input.focus();
        cell_input.select();

        cell_input.click();
      }

      this.editing_cell = cell;
    },
    draw_grid_document: function () {
      if (!this.grid_document_valid() || this.editing_cell !== null) return;

      var table = document.getElementById("grid-document");
      table.innerHTML = "";

      document.getElementById("document-name").innerText =
        this.grid_document.name;

      for (let row = 0; row < this.grid_document.height; row++) {
        var row_tr = document.createElement("tr");

        for (let col = 0; col < this.grid_document.width; col++) {
          /* For the first row, we use th elements instead of td */
          var col_td = document.createElement(row == 0 ? "th" : "td");

          col_td.id = "cell-" + col + "-" + row;

          /* For empty cells, we display a non-breaking space */
          var cell_value = this.grid_document.get_value([col, row]);

          var cell_text_contents = document.createElement("div");
          cell_text_contents.className = "text-container";

          var cell_type = this.get_cell_property([col, row], "type", "text");

          if (cell_type === "color") {
            cell_text_contents.style.backgroundColor = cell_value;
            col_td.style.backgroundColor = cell_value;
          } else {
            cell_text_contents.appendChild(document.createTextNode(cell_value));
          }

          col_td.appendChild(cell_text_contents);

          /* Allow editing */
          /*col_td.onclick = (function(c){
                        return function(e){

                            if(e.target === this && window.gridedit.editing_cell === null || !window.gridedit.cells_equal(window.gridedit.editing_cell, c))
                                window.gridedit.begin_cell_edit(c);
                        };
                    }([col, row]));*/

          if (this.get_cell_property([col, row], "editable", true)) {
            cell_text_contents.onclick = (function (c) {
              return function (e) {
                e.stopPropagation();

                var stop_reedit = true;

                var c_t = window.gridedit.get_cell_property(c, "type", "text");

                /*  This is necessary because you can't actually detect when an HTML color input is
                                    closed. Under normal circumstances, this means that if a user edits a color cell,
                                    but doesn't select a different value, they cannot immediately edit the same cell
                                    (the end cell edit process never engages, because the change event doesn't fire).

                                    To fix this, we implement this workaround that allows begin_cell_edit to be called
                                    for color inputs even if the current cell is being edited.
                                */

                if (c_t === "color" && this.use_color_input)
                  stop_reedit = false;

                if (
                  e.target === this &&
                  (window.gridedit.editing_cell === null ||
                    !stop_reedit ||
                    !window.gridedit.cells_equal(
                      window.gridedit.editing_cell,
                      c
                    ))
                ) {
                  window.gridedit.begin_cell_edit(c);
                }
              };
            })([col, row]);
          } else {
            cell_text_contents.classList.add("not-editable");
          }

          row_tr.appendChild(col_td);
        }

        table.appendChild(row_tr);
      }
    },
    init_empty_document: function (width, height) {
      if (width < 1 || height < 1) return;

      this.grid_document.width = width;
      this.grid_document.height = height;

      this.grid_document.contents = new Array(width * height);
      this.grid_document.contents.fill("");

      this.grid_document.edit_mask = [];
      this.grid_document.name = "Document";

      this.editing_cell = null;

      this.draw_grid_document();
    },
    load_document: function (doc) {
      this.grid_document.width = doc.width;
      this.grid_document.height = doc.height;
      this.grid_document.contents = doc.contents.slice();
      this.grid_document.edit_mask = doc.edit_mask.slice();
      this.grid_document.name = doc.name;

      this.editing_cell = null;

      this.draw_grid_document();
    },
  };

  document.onclick = function (e) {
    if (window.gridedit.editing_cell !== null) window.gridedit.end_cell_edit();
  };
}
