$(document).on('turbolinks:before-render', function(event) {
  $(event.originalEvent.data.newBody).find('[data-turbolinks-update]').each(function() {
    var elem_id = $(this).attr('id'),
        elem_value = $(this).text()
    document.getElementById(elem_id).textContent = elem_value
  })
})
