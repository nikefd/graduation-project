var jqconsole = $('#console').jqconsole();
  $(function () {
    var startPrompt = function () {
      // Start the prompt with history enabled.
      jqconsole.Prompt(true, function (input) {
        console.log(input);
        // Restart the prompt.
        startPrompt();
      });
    };
    startPrompt();
  });
 
var dom = require("ace/lib/dom");

//add command to all new editor instaces
require("ace/commands/default_commands").commands.push({
name: "Toggle Fullscreen",
    bindKey: "F11",
exec: function(editor) {
    dom.toggleCssClass(document.body, "fullScreen")
    dom.toggleCssClass(editor.container, "fullScreen")
    editor.resize()
}
})
var editor = ace.edit("editor");
editor.setTheme("ace/theme/tomorrow_night");
editor.getSession().setMode("ace/mode/c_cpp");
document.getElementById('editor').style.fontSize='16px';
var a = editor.getValue();


$(document).ready(function() {
updater.start();
});

function DispatchText(){
    jqconsole.Reset();
    var message = editor.getValue();
    message = "code" + message;
    message = Tobase64(message);
    updater.socket.send(message);
}
function Reset(){
    editor.setValue("");
}
function Changemode(){
    var obj = document.getElementById('mode');
    var length = obj.options.length - 1;
    for (var i = length; i >= 0; i--){
        if (obj[i].selected == true){
            editor.getSession().setMode("ace/mode/"+obj[i].value);
        }
    }
}
function Changedoc(){
    var mode = document.getElementById('mode');
    var docs = "docs";
    switch(jQuery("#mode option:selected").val()){
        case "c_cpp":
            docs = docs + "cpp";
            break;
        case "javascript":
            docs = docs + "js";
            break;
        case "java":
            docs = docs + "java";
            break;
        case "html":
            docs = docs + "html";
            break;
        case "python":
            docs = docs + "py";
            break;
        case "php":
            docs = docs + "php";
            break;
        default:
            break;
    }
    docs = Tobase64(docs);
    updater.socket.send(docs);

}
 function Tobase64(data){
str = window.btoa(unescape(encodeURIComponent(data)));
    return str;
}
var updater = {
socket: null,

start: function() {
    //var url = "ws://180.160.25.115:8889/websocket";
    var url = "ws://localhost:8889/websocket";
    updater.socket = new WebSocket(url);
    updater.socket.onopen = function(event) {
    }
    updater.socket.onmessage = function(event) {
	updater.showMessage(event.data);
    }
    updater.socket.onerror = function(event) {
	alert("error");
    }
    updater.socket.onclose = function(event) {
    }
},

showMessage: function(message) {
    if (message.substr(0, 4) == "code"){             //如果收到的信息是输出结果
        message = message.substr(4);
        jqconsole.Write(message);
    }
    else if (message.substr(0, 4) == "docs"){       //如果收到的信息是示例
        message = message.substr(4);
        editor.setValue(message);
    }
    else if (message == "input"){                   //如果收到的是输入请求
        jqconsole.Enable();
        jqconsole.Prompt(true, function(input) {
            message = jqconsole.GetHistory().pop();
            message = "inpt" + message;
            message = Tobase64(message);
            updater.socket.send(message);
        });
    }
    else if (message == "end"){                     //如果收到的是结束标识
        jqconsole.Disable();
    }
}

};

