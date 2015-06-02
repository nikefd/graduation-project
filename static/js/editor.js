
var jqconsole = $('#console').jqconsole();//配置终端模块
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
//设置编辑器，按F11则全屏显示
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
    var mode = document.getElementById('mode');
    message = "dir:" + current_dir + " " + message;
    message = Tobase64(message);
    updater.socket.send(message);
}

function Reset(){
    editor.setValue("");
}

//进行Base64编码
function Tobase64(data){
str = window.btoa(unescape(encodeURIComponent(data)));
    return str;
}

var updater = {
socket: null,

start: function() {
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
    if (message.substr(0, 4) == "code"){             //如果收到的信息是输出结果
        message = message.substr(4);
        jqconsole.Write(message);
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

var current_dir = '';
$(function () {
    $(window).resize(function () {
        var h = Math.max($(window).height() - 100, 420);
        $('#container, #data, #tree, #data .content').height(h).filter('.default').css('lineHeight', h + 'px');
    }).resize();

    $('#tree')
        .jstree({
            'core' : {
                'data' : {
                    'url' : '/auth/fileop?operation=get_node',
                    'data' : function (node) {
                        return { 'id' : node.id };
                    }
                },
                'check_callback' : function(o, n, p, i, m) {
                    if(m && m.dnd && m.pos !== 'i') { return false; }
                    if(o === "move_node" || o === "copy_node") {
                        if(this.get_node(n).parent === this.get_node(p).id) { return false; }
                    }  
                    return true;
                },
                'themes' : {
                'responsive' : false,
                'variant' : 'small',
                'stripes' : true
                }
            },
            'sort' : function(a, b) {
                return this.get_type(a) === this.get_type(b) ? (this.get_text(a) > this.get_text(b) ? 1 : -1) : (this.get_type(a) >= this.get_type(b) ? 1 : -1);
            },
            'contextmenu' : {
                'items' : function(node) {
                    var tmp = $.jstree.defaults.contextmenu.items();
                    delete tmp.create.action;
                    tmp.create.label = "New";
                    tmp.create.submenu = {
                        "create_folder" : {
                            "separator_after"  : true,
                            "label"        : "Folder",
                            "action"      : function (data) {
                                var inst = $.jstree.reference(data.reference),
                                obj = inst.get_node(data.reference);
                                inst.create_node(obj, { type : "default" }, "last", function (new_node) {
                                setTimeout(function () { inst.edit(new_node); },0);
                                });
                            }
                        },
                        "create_file" : {
                            "label"        : "File",
                            "action"      : function (data) {
                                var inst = $.jstree.reference(data.reference),
                                obj = inst.get_node(data.reference);
                                inst.create_node(obj, { type : "file" }, "last", function (new_node) {
                                    setTimeout(function () { inst.edit(new_node); },0);
                                });
                            }
                        }
                    };
                    if(this.get_type(node) === "file") {
                        delete tmp.create;
                    }
                    return tmp;
                }
            },
            'types' : {
                'default' : { 'icon' : 'folder' },
                'file' : { 'valid_children' : [], 'icon' : 'file' }
            },
            'unique' : {
                'duplicate' : function (name, counter) {
                    return name + ' ' + counter;
                }
            },
            'plugins' : ['state','dnd','sort','types','contextmenu','unique']
        })
        .on('delete_node.jstree', function (e, data) {
            $.get('/auth/fileop?operation=delete_node', { 'id' : data.node.id })
                .fail(function () {
                data.instance.refresh();
                });
        })
        .on('create_node.jstree', function (e, data) {
            $.get('/auth/fileop?operation=create_node', { 'type' : data.node.type, 'id' : data.node.parent, 'text' : data.node.text })
                .done(function (d) {
                    data.instance.set_id(data.node, d.id);
                })
                .fail(function () {
                    data.instance.refresh();
                });
        })
        .on('rename_node.jstree', function (e, data) {
            $.get('/auth/fileop?operation=rename_node', { 'id' : data.node.id, 'text' : data.text })
                .done(function (d) {
                    data.instance.set_id(data.node, d.id);
                })
                .fail(function () {
                    data.instance.refresh();
                });
        })
        .on('move_node.jstree', function (e, data) {
            $.get('/auth/fileop?operation=move_node', { 'id' : data.node.id, 'parent' : data.parent })
                .done(function (d) {
                //data.instance.load_node(data.parent);
                    data.instance.refresh();
                })
                .fail(function () {
                    data.instance.refresh();
                });
        })
        .on('copy_node.jstree', function (e, data) {
            $.get('/auth/fileop?operation=copy_node', { 'id' : data.original.id, 'parent' : data.parent })
                .done(function (d) {
                //data.instance.load_node(data.parent);
                    data.instance.refresh();
                })
                .fail(function () {
                    data.instance.refresh();
                });
        })
        .on('changed.jstree', function (e, data) {
            if(data && data.selected && data.selected.length) {
                current_dir = data.selected.join(':');
                $("#file_name").text(current_dir.substring(current_dir.lastIndexOf("/") + 1));       //设置文件标签
                $.get('/auth/fileop?operation=get_content&id=' + data.selected.join(':'), function (d) {
                    if(d && typeof d.type !== 'undefined') {
                        $('#data .content').hide();
                        switch(d.type) {
                            case 'text':
                            case 'txt':
                            case 'md':
                                editor.getSession().setMode("ace/mode/markdown");
                                break;
                            case 'js':
                                editor.getSession().setMode("ace/mode/javascript");
                                break;
                            case 'json':
                                editor.getSession().setMode("ace/mode/json");
                                break;
                            case 'css':
                                editor.getSession().setMode("ace/mode/css");
                                break;
                            case 'html':
                                editor.getSession().setMode("ace/mode/html");
                                break;
                            case 'htm':
                                editor.getSession().setMode("ace/mode/html");
                                break;
                            case 'xml':
                                editor.getSession().setMode("ace/mode/xml");
                                break;
                            case 'c':
                                editor.getSession().setMode("ace/mode/c_cpp");
                                break;
                            case 'cpp':
                                editor.getSession().setMode("ace/mode/c_cpp");
                                break;
                            case 'h':
                                editor.getSession().setMode("ace/mode/c_cpp");
                                break;
                            case 'sql':
                                editor.getSession().setMode("ace/mode/sql");
                                break;
                            case 'log':
                                break;
                            case 'py':
                                editor.getSession().setMode("ace/mode/python");
                                break;
                            case 'rb':
                                editor.getSession().setMode("ace/mode/ruby");
                                break;
                            case 'php':
                                editor.getSession().setMode("ace/mode/php");
                                break;
                            case 'htaccess':
                                break;
                            case 'java':
                                editor.getSession().setMode("ace/mode/java");
                                break;
                            default:
                                break;
                        }
                        editor.setValue(d.content);
                    }
                });
            }
            else {
                $('#data .content').hide();
                $('#data .default').html('Select a file from the tree.').show();
            }
        });
});
