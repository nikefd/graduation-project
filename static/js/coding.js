var dom = require("ace/lib/dom");
var Range = require("ace/range").Range;
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
editor.setBehavioursEnabled(0);
document.getElementById('editor').style.fontSize='16px';
var a = editor.getValue();
doc = editor.getSession().doc;
var send = 1;
var allsend = 1;
opMap = {
      'insertText': 1,
      'insertLines': 2,
      'removeText': 3,
      'removeLines':4
};


$(document).ready(function() {
    $("#messageform").on("keypress", function(e) {
        if (e.keyCode == 13) {
       	    updater.socket.send(ToBase64("talking" + $("#message").val()));
	    $("#message").val('');
            return false;
        }
    });
doc.on("change", function(event) {
var data = event.data;
var op = opMap[data.action];
var changeData = {"op":op, "srow":data.range.start.row, "scolumn":data.range.start.column, "erow":data.range.end.row, "ecolumn":data.range.end.column ,"text":data.text, "lines":data.lines};
changeData = JSON.stringify(changeData);
//alert(changeData);
message = "work" + changeData;
if (allsend == 0){
    return;
}
if (send == 0){
    send = 1;
    return;
}
if (op == 1){
send = 0;
updater.socket.send(ToBase64(message));
doc.remove(new Range(data.range.start.row, data.range.start.column, data.range.end.row, data.range.end.column));
}
else if (op == 2){
send = 0;
updater.socket.send(ToBase64(message));
doc.remove(new Range(data.range.start.row, data.range.start.column, data.range.end.row, data.range.end.column));
}
else if (op == 3){
send = 0;
updater.socket.send(ToBase64(message));
doc.insert({row:data.range.start.row, column:data.range.start.column} , data.text);
}
else if (op == 4){
send = 0;
updater.socket.send(ToBase64(message));
doc.insert({row:data.range.start.row, column:data.range.start.column} , data.nl);
}
});
updater.start();
});
function Reset(){
    editor.setValue("");
}

 function ToBase64(data){
str = window.btoa(unescape(encodeURIComponent(data)));
    return str;
}

function ToString(data){
    str = decodeURIComponent(escape(window.atob(data)));
    return str;
}

var updater = {
socket: null,

start: function() {
    //var url = "ws://180.160.25.115:8889/websocket";
    host = $("#ip").data('ip');
    var url = "ws://localhost:8000/websocket";
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
if (message.substr(0,7) == "talking"){
message = message.substring(7);
index = message.indexOf(": ");
user = message.substr(0, index + 2);
message = ToString(message.substring(index + 2));
message = user + message
node = "<div>" + message + "</div>";
$("#box").append(node);
box.scrollTop = box.scrollHeight;
return;
}
allsend = 1;
if (message == "new_user"){
initvalue = editor.getValue();
message = "initvalue" + initvalue;
updater.socket.send(ToBase64(message));
return;
}
if (message.substr(0,9) == "initvalue"){
//alert(message);
initvalue = message.substring(9);
allsend = 0;
editor.setValue(ToString(initvalue));
return;
}
message = ToString(message);
        rec = JSON.parse(message);
if (rec.op == 1){
send = 0;
doc.insert({row:rec.srow, column:rec.scolumn} , rec.text);
}
else if (rec.op == 2){
send = 0;
doc.insert({row:rec.srow, column:rec.scolumn} , rec.lines);
}
else if (rec.op == 3){
send = 0;
doc.remove(new Range(rec.srow, rec.scolumn, rec.erow, rec.ecolumn));
}
else if (rec.op == 4){
send = 0;
doc.remove(new Range(rec.srow, rec.scolumn, rec.erow, rec.ecolumn));
}

}

};

