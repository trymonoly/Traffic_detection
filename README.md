# Traffic_detection
和朋友们出门吃饭时。朋友们说java的流量抓取很难实现。
所以写出了基于反向代理的流量检测系统demo（有些小bug，记录数据都是重复两次）
原理和nginx的反向代理很像，只是将客户端流量拷贝一份发往日记系统
![image](https://github.com/trymonoly/Traffic_detection/blob/master/images/1.png)
代码分别实现了两个系统，分别为代理服务器和日志服务器，而WEB服务器可以是随意的
效果图如下:
![image](https://github.com/trymonoly/Traffic_detection/blob/master/images/2.png)
![image](https://github.com/trymonoly/Traffic_detection/blob/master/images/3.png)
![image](https://github.com/trymonoly/Traffic_detection/blob/master/images/4.png)
![image](https://github.com/trymonoly/Traffic_detection/blob/master/images/5.png)
配置页面尚未完成，计划通过动态配置proxy_server.py文件进行启动proxy服务器
