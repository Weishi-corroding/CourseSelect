/**
 * 设置未来(全局)的AJAX请求默认选项
 * 主要设置了AJAX请求遇到Session过期的情况
 */
$.ajaxSetup({
    type: 'POST',
    contentType:"application/x-www-form-urlencoded;charset=utf-8",
    complete: function(xhr,status) {
        var sessionStatus = xhr.getResponseHeader('sessionstatus');
        var relogin = xhr.getResponseHeader('relogin');
        if(sessionStatus == 'timeout') {
            // if (window.parent) {
            //     window.parent.location.href = relogin;
            // } else {
                window.location.href = relogin;
            // }
        }
    }
});

$.ajaxSetup({
    type: 'GET',
    contentType:"application/x-www-form-urlencoded;charset=utf-8",
    complete: function(xhr,status) {
        var sessionStatus = xhr.getResponseHeader('sessionstatus');
        var relogin = xhr.getResponseHeader('relogin');
        if(sessionStatus == 'timeout') {
            window.location.href = relogin;
        }
    }
});

/**
 * datatable是否弹出错误窗口设置
 */
function showDatataleWarning() {
    // DataTable.ext.sErrMode = 'alert';
}
function hideDatataleWarning() {
    // DataTable.ext.sErrMode = 'none';
}
hideDatataleWarning();
