(function ($) {
    $.fn.folderless_change_list = function () {
        this.each(function () {
            var _self = $(this);
            var upload_button = _self.find(".folderless_uploader");
            var upload_info = _self.find(".folderless_upload_info");
            var upload_errors_link = _self.find(".upload_errors");
            var upload_errors_info = _self.find(".error_info");
            var files_total = 0;
            var files_uploaded = 0;
            var files_upload_error = 0;
            var file_input = _self.find(".folderless_fileinput");

            var reload = function() {
                document.location.reload();
            };

            var check_finished = function() {
                if (files_uploaded + files_upload_error == files_total) {
                    if (files_uploaded == files_total) {
                      reload();
                    } else {
                      alert(upload_errors_info.html());
                      reload();
                    }
                }
            }

            var init = function () {
                // uploader instead of classic "add"
                upload_errors_link.click(function (e) {
                    e.preventDefault();
                    alert(upload_errors_info.html());
                });
                upload_button.click(function (e) {
                    e.preventDefault();
                    file_input.click();
                });
                file_input.fileupload({
                      dataType: 'json',
                      replaceFileInput: false,
                      sequentialUploads: true,
                      add: function (e, data) {
                          upload_info.show(0);
                          files_total += 1;
                          upload_info.find(".total").html(files_total);
                          data.submit();
                      },
                      send: function (e, data) {

                      },
                      done: function (e, data) {
                          files_uploaded += 1;
                          upload_info.find(".uploaded").html(files_uploaded);
                          check_finished();
                      },
                      fail: function (e, data) {
                          files_upload_error += 1;
                          var info = jQuery.parseJSON(data.jqXHR.responseText);
                          upload_errors_link.show(0).find("span").html(files_upload_error);
                          upload_errors_info.append(info.message + "\n\n");
                          check_finished();
                      },
                      progressall: function (e, data) {
                          var progress = parseInt(data.loaded / data.total * 100, 10);
                          upload_info.find(".percent").html(progress + "%");
                          if (data.loaded / data.total == 1) {
                              upload_info.find(".status").html("processing...");
                          }
                      }
                });
            };

            init();

        });
    }
})(jQuery);
