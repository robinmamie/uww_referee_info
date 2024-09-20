const id_number = parseInt(window.location.pathname.split('/').pop().split('_')[0], 10);
const name = $("h2").eq(1).text();
$(document).prop('title', id_number + ' - ' + name);

$('#history').hide();
$('button#toggle').click(function (e) {
    $('.blink_me__').toggleClass('blink_me');
    $('#history').show();
});