$(document).on('turbolinks:load', function() {
  $('.dropdown-button').dropdown()
  $('.modal').modal();
})

$(document).on('turbolinks:before-cache', function() {
  $('.dropdown-content').css('display', 'none');
})
