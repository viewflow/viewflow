$(document).on('turbolinks:load', function() {
  $('.dropdown-button').dropdown()
  $('.modal').modal({preventScrolling: false})
  $('.collapsible').collapsible()
})

$(document).on('turbolinks:before-cache', function() {
  $('.dropdown-content').css('display', 'none')
  $('.modal').modal('destroy')
  $('.collapsible').collapsible('destroy')
  $('.dropdown-button').dropdown('destroy')
})

$(document).on('turbolinks:before-render', function(event) {
  $(event.originalEvent.data.newBody).find('[data-turbolinks-update]').each(function() {
    var elem_id = $(this).attr('id'),
        elem_value = $(this).text()
    document.getElementById(elem_id).textContent = elem_value
  })
})
