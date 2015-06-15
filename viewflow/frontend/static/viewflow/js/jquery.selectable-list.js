(function ($) {
    var defaults = {
        selectedClass: "selected",
        checkSelector: "input[type=checkbox]",
        checkallSelector: "#checkall",
    };

    var SelectableList = function (table, options) {
        this.options = $.extend(defaults, options);
        this.init(table);
    };

    SelectableList.prototype = {
        init: function (table) {
            var obj = this;
            this.$table = $(table);

            if (this.options.checkallSelector) {
                this.checkall = $(this.options.checkallSelector, table);
                this.checkall.click(function (e) { obj.checkallOnClick(e, this) });
            }

            this.$table.on("click", "tbody tr", function(e) { obj.trOnClick(e, this) });

            // no selection when clicking the links
            //this.$table.on("click", "tbody tr a", function (e) {
            //    e.stopPropagation();
            //});

            this.$table.on("click", "tbody tr label", function (e) {
                e.stopPropagation();
            });

            // no text selection when using shift
            this.$table.on("mousedown", "tbody tr td", function (e) {
                if (e.shiftKey)
                    e.preventDefault();

                obj.clear = obj.getSelection().length > 0;
            });

            // highlight based on initial checkbox state
            $("tbody tr", this.$table).each(function () {
                var $tr = $(this);
                var $chk = $(obj.options.checkSelector, $tr);
                if ($chk.length > 0) {
                    var selected = $chk.prop("checked");
                    obj.toggle($tr, selected);
                }
            });
        },
		trOnClick: function (e, tr) {
                if(e.target.tagName == 'A')
                    return;

                if (this.getSelection().length > 0 || this.clear)
                    return;

				var $tr = $(tr);
				
                if ($(this.options.checkallSelector, $tr).length > 0) // click on header (no explicit tbody in markup)
                    return;

                var selected = !$tr.hasClass(this.options.selectedClass);

                this.toggle($tr, selected);

                // (un)select range with shift
                if (e.shiftKey && this.last && this.lastSelected == selected && this.last != $tr) {
                    var last = this.last.index();
                    var curr = $tr.index();
                    var start = last < curr ? this.last : $tr;
                    var end = last < curr ? $tr : this.last;
                    var obj = this;
                    start.nextUntil(end).each(function () {
                        obj.toggle($(this), selected);
                    });
                }

                this.last = $tr; // last clicked row
                this.lastSelected = selected; // last clicked row state

                this.allChecked();

                if (this.options.onCheck)
                    this.options.onCheck(this);
            },
        checkallOnClick: function (e, checkall) {
            var selected = checkall.checked;
            var obj = this;
            $("tbody tr", this.$table).each(function () {
                obj.toggle($(this), selected);
            });

            if (this.options.onCheck)
                this.options.onCheck(this);
        },
        toggle: function ($tr, selected) {
            $tr.toggleClass(this.options.selectedClass, selected);

            var $chk = $(this.options.checkSelector, $tr);

            if ($chk.length > 0 && $chk.prop("checked") != selected) // checkbox was not the target
                $chk.prop("checked", selected);
        },
        allChecked: function () {
            if (this.checkall) {
                var allchecked = $("tbody tr " + this.options.checkSelector + ":not(:checked," + this.options.checkallSelector + "):first", this.$table).length == 0;
                //allchecked &= $("tbody tr " + this.options.checkSelector + ":not(" + this.options.checkallSelector + "):first", this.$table).length > 0;
                this.checkall.prop("checked", allchecked);
            }
        },
        getSelection: function () {
            if (document.selection && document.selection.empty) {
                return document.selection.toString();
            } else if (window.getSelection) {
                var sel = window.getSelection();
                return sel.toString();
            }
        },
    };

    $.fn.selectableList = function (options) {
        return this.filter("table").each(function () {
            new SelectableList(this, options);
        });
    };
}(jQuery));