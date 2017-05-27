# OTRS FAQ to Elasticsearch

## Requirements

non Python Software:

* Java 8
* Apache Tika Server
* Elasticsearch

https://www.unixmen.com/install-oracle-java-jdk-8-centos-76-56-4/


`wget http://www-eu.apache.org/dist/tika/tika-server-1.14.jar`

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


`rpm -ivh elasticsearch-5.1.2.rpm`


Libs (Python3)

* PyMySQL
* tika
* elasticsearch
* + dependencies of that packages

```
pip3 install elasticsearch PyMySQL tika
```



### Install NGINX as Reverse Proxy for ES, Kibana and to host elasticsearch-HQ

sudo apt-get install ngingx

#### create basic auth user account

```
htpasswd -c /etc/nginx/htpasswd username
```

#### ES reverse Proxy + elasticsearch-HQ

**elasticsearch.conf**

```
server {
    listen *:443;
    server_name otrs-dev.home.rhab.de;

    root /var/www/html/otrs-es;

    access_log /var/log/nginx/otrs_es.access.log;
    error_log /var/log/nginx/otrs_es.error.log;

    #ssl on;
    #ssl_certificate /etc/ssl/com.example.es.crt;
    #ssl_certificate_key /etc/ssl/com.example.es.key;
    #add_header Strict-Transport-Security max-age=15552000; # 180 days

    auth_basic           "OTRS ES";
    auth_basic_user_file /etc/nginx/elasticsearch.pwd;

    location /_plugin/hq/ {
        alias /var/www/html/otrs-es/elasticsearch-HQ/;
        expires 300s;
    }

    location / {
        # Send everything to the Elasticsearch endpoint
        proxy_pass http://127.0.0.1:9200;
        proxy_read_timeout 90;
    }
}
```

**kibana.conf**

```
server {
    listen *:8443;
    server_name otrs-dev.home.rhab.de;

    root /var/www/html/otrs-es;

    access_log /var/log/nginx/otrs_kibana.access.log;
    error_log /var/log/nginx/otrs_kibana.error.log;

    #ssl on;
    #ssl_certificate /etc/ssl/com.example.es.crt;
    #ssl_certificate_key /etc/ssl/com.example.es.key;
    #add_header Strict-Transport-Security max-age=15552000; # 180 days

    auth_basic           "OTRS ES - Kibana";
    auth_basic_user_file /etc/nginx/elasticsearch.pwd;

    location / {
        # Send everything to the Elasticsearch endpoint
        proxy_pass http://127.0.0.1:5601;
        proxy_read_timeout 90;
    }
}

```

### Install HQ "Pluging"

```
wget https://github.com/royrusso/elasticsearch-HQ/archive/v2.0.3.zip -o /tmp/v2.0.3.zip
unzip -d /tmp /tmp/v2.0.3.zip 
mkdir /var/www/html/otrs-es
cp -a /tmp/royrusso-elasticsearch-HQ-eb117d4/var/www/html/otrs-es/elasticsearch-HQ
chown -R apache:apache /var/www/html/elasticsearch-HQ
```


