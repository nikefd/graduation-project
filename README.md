#A online programming platform (linux)

##Description

This is an online programming platform named TJIDE which using Docker as the container of background service operation, Nginx as Reverse proxy server, Tornado as Web server framework, realizes a platform which can compile and execute codes in various programming languages(currently C/C++, Java, PHP, and Python). 

##Getting started

1. install [docker][1]

2. pull the images

		$ docker pull nikefd/tjide 
		$ docker pull nikefd/mysql
		$ docker pull nikefd/gcc		
		$ docker pull nikefd/python
		$ docker pull nikefd/php

3. run the docker

	- run the database

			$ sudo docker run -v ~/workplace/test/mysql:/var/lib/mysql -d --name mysql -e MYSQL_ROOT_PASSWORD=admin nikefd/mysql

	- run the main docker
	
			$ sudo docker run --rm -ti -v ~/workplace/userdata:/userdata -v /var/run/docker.sock:/var/run/docker.sock -v $(which docker):$(which docker) -v ~/workplace/graduation-project:/try --link mysql:tomysql --name tjide0 -p 8000:8888 nikefd/tjide
	
	- running

			$ python server.py

Then open localhost:8000 in your favorite browser and done.

## License

MIT licensed

Copyright (C) 2015 Yangbin Zhang

[1]: https://www.docker.com/
