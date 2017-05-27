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


### Install ES on Ubuntu

https://www.digitalocean.com/community/tutorials/how-to-set-up-a-production-elasticsearch-cluster-on-ubuntu-14-04

https://www.elastic.co/guide/en/elasticsearch/reference/current/deb.html

```
sudo add-apt-repository -y ppa:webupd8team/java
sudo apt-get update
sudo apt-get -y install oracle-java8-installer
```

```
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
sudo apt-get install apt-transport-https
echo "deb https://artifacts.elastic.co/packages/5.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-5.x.list
sudo apt-get update
sudo apt-get install elasticsearch
```

### Configure Es

`sudo vi /etc/elasticsearch/elasticsearch.yml`

* cluster.name: otrs-es
* node.name: ${HOSTNAME}
* bootstrap.memory_lock: true
* network.host: 127.0.0.1
* http.port: 9200

### Install nginx as reverse proxy for ES, Kibana and to host elasticsearch-HQ

Secure nginx config reference: https://gist.github.com/plentz/6737338

```
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y dist-upgrade
sudo apt-get install nginx apache2-utils
```

#### dhparam.pem file

``` 
sudo mkdir /etc/nginx/ssl
sudo openssl dhparam -out /etc/nginx/ssl/dhparam.pem 2048
```

#### optional: create self signed cert

```
cd /etc/nginx/ssl
```

`vi req.conf`

```
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no
[req_distinguished_name]
C = DE
ST = Hessen
L = Frankfurt
O = Example.com
OU = Example.com Testing
CN = server.example.com
[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = server.example.com
IP.2 = 192.168.0.20
```

# create certificate

```
sudo openssl req -x509 -nodes -days 1095 -newkey rsa:2048 -keyout server.example.com.key -out server.example.com.pem -config req.conf -extensions 'v3_req'
```
 
#### create basic auth user account

```
sudo htpasswd -c /etc/nginx/.htpasswd username
sudo chmod 640 /etc/nginx/.htpasswd
```

#### ES reverse Proxy + elasticsearch-HQ

**/etc/nginx/sites-available/elasticsearch.conf**

```
server {
    listen *:443;
    server_name server.example.com;

    root /var/www/html/otrs-es;

    access_log /var/log/nginx/otrs_es.access.log;
    error_log /var/log/nginx/otrs_es.error.log;

    ssl on;
    ssl_certificate /etc/nginx/ssl/server.example.com.pem;
    ssl_certificate_key /etc/nginx/ssl/server.example.com.key;

    # enable session resumption to improve https performance
    # http://vincent.bernat.im/en/blog/2011-ssl-session-reuse-rfc5077.html
    ssl_session_cache shared:SSL:50m;
    ssl_session_timeout 5m;

    # Diffie-Hellman parameter for DHE ciphersuites, recommended 2048 bits
    ssl_dhparam /etc/nginx/ssl/dhparam.pem;

    # enables server-side protection from BEAST attacks
    # http://blog.ivanristic.com/2013/09/is-beast-still-a-threat.html
    ssl_prefer_server_ciphers on;
    # disable SSLv3(enabled by default since nginx 0.8.19) since it's less secure then TLS http://en.wikipedia.org/wiki/Secure_Sockets_Layer#SSL_3.0
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    # ciphers chosen for forward secrecy and compatibility
    # http://blog.ivanristic.com/2013/08/configuring-apache-nginx-and-openssl-for-forward-secrecy.html
    ssl_ciphers "ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES256-GCM-SHA384:AES128-GCM-SHA256:AES256-SHA256:AES128-SHA256:AES256-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4";

    #add_header Strict-Transport-Security max-age=15552000; # 180 days

    auth_basic           "OTRS ES";
    auth_basic_user_file /etc/nginx/.htpasswd;

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

# redirect all http traffic to https
server {
  listen 80;
  server_name server.example.com;
  return 301 https://$host$request_uri;
}
```

`sudo ln -s /etc/nginx/sites-available/elasticsearch.conf /etc/nginx/sites-enabled`

**/etc/nginx/sites-available/kibana.conf**

```
server {
    listen *:8443;
    server_name server.example.com;

    access_log /var/log/nginx/otrs_kibana.access.log;
    error_log /var/log/nginx/otrs_kibana.error.log;

    ssl on;
    ssl_certificate /etc/nginx/ssl/server.example.com.pem;
    ssl_certificate_key /etc/nginx/ssl/server.example.com.key;

    # enable session resumption to improve https performance
    # http://vincent.bernat.im/en/blog/2011-ssl-session-reuse-rfc5077.html
    ssl_session_cache shared:SSL:50m;
    ssl_session_timeout 5m;

    # Diffie-Hellman parameter for DHE ciphersuites, recommended 2048 bits
    ssl_dhparam /etc/nginx/ssl/dhparam.pem;

    # enables server-side protection from BEAST attacks
    # http://blog.ivanristic.com/2013/09/is-beast-still-a-threat.html
    ssl_prefer_server_ciphers on;
    # disable SSLv3(enabled by default since nginx 0.8.19) since it's less secure then TLS http://en.wikipedia.org/wiki/Secure_Sockets_Layer#SSL_3.0
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    # ciphers chosen for forward secrecy and compatibility
    # http://blog.ivanristic.com/2013/08/configuring-apache-nginx-and-openssl-for-forward-secrecy.html
    ssl_ciphers "ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES256-GCM-SHA384:AES128-GCM-SHA256:AES256-SHA256:AES128-SHA256:AES256-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4";

    #add_header Strict-Transport-Security max-age=15552000; # 180 days

    auth_basic           "OTRS ES - Kibana";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        # Send everything to the Elasticsearch endpoint
        proxy_pass http://127.0.0.1:5601;
        proxy_read_timeout 90;
    }
}

```

`sudo ln -s /etc/nginx/sites-available/kibana.conf /etc/nginx/sites-enabled`

### Install HQ "Plugin

```
wget https://github.com/royrusso/elasticsearch-HQ/archive/v2.0.3.zip -o /tmp/v2.0.3.zip
unzip -d /tmp /tmp/v2.0.3.zip 
mkdir /var/www/html/otrs-es
cp -a /tmp/royrusso-elasticsearch-HQ-eb117d4/var/www/html/otrs-es/elasticsearch-HQ
chown -R apache:apache /var/www/html/elasticsearch-HQ
```


