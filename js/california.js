

Douban.init_unfolder = function(o){
    $(o).click(function(){
        var rid = $(o).attr('id').split('-')[1];
        var url = '/j/review/'+rid+'/fullinfo';
        $.getJSON(url, function(r) {
            $('#review_'+rid).hide();
            $('#review_'+rid).html(r.html);
            $('#review_'+rid).show();
            $('#af-'+rid).hide();
            $('#au-'+rid).show();
            //load_event_monitor($('#review_'+rid+'_full'));
        });
        return false;
    }).hover_fold('unfolder');
}

Douban.init_folder = function(o){
    $(o).click(function(){
        var rid = $(o).attr('id').split('-')[1];
        $('#r_'+rid).hide();
        $(o).hide();
    }).hover_fold('folder');
}

