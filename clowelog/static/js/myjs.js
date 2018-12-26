/**
 * Created by Administrator on 2018/12/18.
 */
$('#myDropzone').addEventListener("queuecomplete",
    function redirect(){
    window.location.href='/main/upload/text';
}
    );