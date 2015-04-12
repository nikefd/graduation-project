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


