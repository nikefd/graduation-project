双系统安装之后没有引导界面直接进入linux
    sudo update-grub

###docker的安装

1. 下载docker

    wget -qO- https://get.docker.com/ | sh

之后会出现error

    FATA[0000] Error loading docker apparmor profile: fork/exec /sbin/apparmor_parser: no such file or directory () 

    sudo apt-get install apparmor

    sudo service docker restart

之后就可以使用了

对前台和服务器传输的数据进行简单的封装，加个头标识

对数据进行编码解码，以防止传输过程中出现问题

2. 下载butterfly的docker镜像并运行

    sudo docker run --env PASSWORD=123456 --env PORT=57575 -p 127.0.0.1:57575:57575 -d garland/butterfly

    sudo docker run garland/butterfly:latest

安装python的tailer来实现tail功能
pip install tailer

记得修改ip地址

毕业设计中存在的问题及解决思路情况
1. 前后台数据传输的问题
前后台数据传输过程中因为格式问题可能会出错，而且需要区分传输的数据是做什么用的
解决思路：对传输的数据都转换成base64编码，并且对其进行简单的封装来进行区分

解决情况：已经解决

2. 前后台进行实时交互及获取运行程序状态的问题
在线编辑器需要较好的实时性，编译或解释程序的时候需要判断程序的运行状态然后在前端做出响应
解决思路：采用websocket及tornado服务框架，能满足较高的实时性，采用python自带函数及shell指令来判断运行程序的状态
解决情况：已经基本解决

3. 平台安全性问题
无法保证用户运行的程序是否会对服务器及其他用户造成损害
解决思路：利用docker进行隔离
解决情况：尚未解决

下一阶段的工作计划及研究内容
1. 解决上述存在的尚未解决的问题

2. 进行数据库的搭建，完成用户登录及文件存储等基本功能

3. 对docker进行进一步的学习，将每种编译环境配置一个docker，根据用户需求调用不同的docker

4. 对整体界面及部分功能进行进一步的优化及完善
