# OTRS FAQ to Elasticsearch

## Requirements

non Python Software:

* Java 8
* Apache Tika Server
* Elasticsearch

https://www.unixmen.com/install-oracle-java-jdk-8-centos-76-56-4/


wget http://www-eu.apache.org/dist/tika/tika-server-1.14.jar

https://www.it-rem.ru/avtozagruzka-apache-tika-v-centos-7.html

Edit `vi /etc/systemd/system/tika.service`

```
[Unit]
Description=Apache Tika Server
Requires=network.target
After=network.target

[Service]
ExecStart=/bin/java -jar /opt/tika/tika-server-1.14.jar
SuccessExitStatus=143
Type=simple

[Install]
WantedBy=multi-user.target
```

Copy to /opt/tika/ - Enable and Start

```
mkdir /opt/tika
cp tika-server-1.14.jar /opt/tika/
systemctl daemon-reload
systemctl enable tika.service
systemctl start tika.service
systemctl status tika
```



rpm -ivh elasticsearch-1.7.3.noarch.rpm



Libs

* elasticsearch
* tika

```
pip install elasticsearch tika
```
