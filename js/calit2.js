var is_today_panel = function() {
    return $("#tab_dailyroutine").hasClass("activenavitab");
}
var is_tomorrow_panel = function() {
    return $("#tab_tomorrow").hasClass("activenavitab");
}

function showLoadingPanel() {
    $("#loadingpanel").center();
    $("#loadingpanel").fadeIn('fast');
}

function hideLoadingPanel() {
    $("#loadingpanel").fadeOut('fast');
}

function is_inbox_activated() {
    return $("#tab_inbox").hasClass("activenavitab");
}

function tabs_RemoveActive() {
    var tab_list = ['#tab_inbox', '#tab_dailyroutine', '#tab_tomorrow', '#tab_done'];
    for (i=0;i<=tab_list.length - 1;i++){
        if ($(tab_list[i]).hasClass("activenavitab")){
            $(tab_list[i]).removeClass('activenavitab');
        }
        if (!$(tab_list[i]).hasClass("navitab")){
            $(tab_list[i]).addClass('navitab');
        }
    }
}

function tabs_MakeActive(obj_div) {
    tabs_RemoveActive();
    str_divname = "#" + obj_div.id;
    $(str_divname).removeClass("navitab");
    $(str_divname).addClass('activenavitab');
}

var getItemfromData = function(data) {
    var id = data['id'];
    var item_name = data['name'];
    var item_comment = data['comment'];
    var item_expectdate = data['expectdate'];
    var item_routine = data['routine'];
    return {
        "comment": item_comment,
        "is_duetoday": data['is_duetoday'],
        "donedate": data['donedate'],
        "tags": null,
        "done": data['done'],
        "date": data['date'],
        "id": id,
        "category": data['done'],
        "duration": data['duration'],
        "name": item_name,
        "expectdate": item_expectdate,
        "routine": item_routine,
        "is_duetomorrow": data['is_duetomorrow'],
        "is_dueyesterday": data['is_dueyesterday'],
        isnottodaypanel: function() {
            return !is_today_panel();
        }
    }
}


