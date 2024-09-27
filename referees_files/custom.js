const id_number = parseInt(window.location.pathname.split('/').pop().split('_')[0], 10);
const name = $("h2").eq(1).text();
$(document).prop('title', id_number + ' - ' + name);

$('#history').hide();
$('#toggle').click(function (e) {
    $('.blink_off').toggleClass('blink');
    $('#history').toggle();

    const text = $('#toggle').text();
    $('#toggle').text(
        text == "Show History" ? "Hide History" : "Show History");
});

function daysInMonth(year, month) {
    return new Date(year, month, 0).getDate();
}

function calcDate(date1, date2){
    /*
    * calcDate() : Calculates the difference between two dates
    * @date1 : "First Date"
    * @date2 : "Second Date"
    * return : String giving the time difference between the two dates
    */

    const year1 = date1.getFullYear();
    const year2 = date2.getFullYear();
    const month1 = date1.getMonth();
    const month2 = date2.getMonth();
    const days1 = date1.getDate();
    const days2 = date2.getDate();

    const monthDiffPassed = days2 >= days1;
    const birthdayPassed = month2 > month1 || (month2 == month1 && monthDiffPassed);

    const years_passed = year2 - year1 - (birthdayPassed ? 0 : 1);

    let months_passed = month2 - month1;
    if (month1 >= month2 && !birthdayPassed) {
	months_passed += 12;
    }
    if (!monthDiffPassed) {
        months_passed -= 1;
    }

    let days_passed = days2 - days1;
    if (!monthDiffPassed) {
        days_passed += daysInMonth(year2, month2);
	 
    }

    //Set up custom text
    const yrsTxt = ["year", "years"];
    const mnthsTxt = ["month", "months"];
    const daysTxt = ["day", "days"];

    //Convert to days and sum together
    const total_days = (years_passed * 365) + (months_passed * 30.417) + days_passed;

    //display result with custom text
    const result = ((years_passed == 1) ? years_passed + ' ' + yrsTxt[0] : (years_passed > 1) ?
        years_passed + ' ' + yrsTxt[1] : '') +
        ((months_passed == 1) ? ", " + months_passed + ' ' + mnthsTxt[0] : (months_passed > 1) ?
            ", " + months_passed + ' ' + mnthsTxt[1] : '') +
        ((days_passed == 1) ? ", " + days_passed + ' ' + daysTxt[0] : (days_passed > 1) ?
            ", " + days_passed + ' ' + daysTxt[1] : '');

    //return the result
    return result.trim() + " old";
}


function getAge() {
    const today = new Date();
    const dateString = $(".birthdate").eq(0).attr('iso');
    const birthDate = new Date(dateString);
    return calcDate(birthDate, today);
}

$("<h5>" + getAge() + "</h5>").insertAfter($("h4").eq(0));
