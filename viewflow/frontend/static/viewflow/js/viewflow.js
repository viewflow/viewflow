$(document).on('turbolinks:load', function() {
  $('.dropdown-button').dropdown()
  $('.modal').modal();
  
  $("table.selectable").selectableList({
    checkallSelector: "[data-select-all]",
    onCheck: function(table) {
      $selection = table.$table.find("tr." + table.options.selectedClass);
      if ($selection.length > 0) {
        $('.selectable-action').removeClass('disabled')
      } else {
        $('.selectable-action').addClass('disabled')
      }
    }
  });

  $('.selectable-action').click(function(e) {
    e.preventDefault()

    var url = this.getAttribute("href");
    var pks = [];

    $("table.selectable tr.selected").each(function() {
      pks.push($(this).data('row-id'))
    });

    if(url.includes('?')) {
      url += '&tasks=' + pks.join(',');
    } else {
      url += '?tasks=' + pks.join(',');
    }

    window.location.href = url;
  });

})

$(document).on('turbolinks:before-cache', function() {
  $('.dropdown-content').css('display', 'none');
})
