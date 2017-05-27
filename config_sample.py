import platform
platform_distro = platform.dist()[0].lower()

# MySQL Connection Settings
MYSQL_HOST = "localhost"
MYSQL_USER = "otrs"
MYSQL_PASS = "<insert_password_here>"
MYSQL_DB = "otrs"

# ES Connection Settings
ES_HOST = "localhost"
ES_PORT = 9200
ES_USER = None
ES_PASS = None
# ES SSL/TLS Settings
ES_USE_SSL = True  # this setting is ignored.. if USER + PASS is provided then SSL will be used
ES_VERIFY_CERTS = True
if platform_distro in ["centos", "rhel"]:
    ES_CA_CERTS = "/etc/pki/tls/certs/ca-bundle.crt"
elif platform_distro in ["ubuntu", "debian"]:
    ES_CA_CERTS = "/etc/ssl/certs/ca-certificates.crt"
else:
    ES_CA_CERTS = "ca-bundle.crt"
# ES_CA_CERTS = "foobar"  # manual override here

# ES Index Settings
ES_INDEX = "faqs"
ES_DOC_TYPE = "faq"
ES_INDEX_SETTING_MAPPING_FILE = "mappings_settings.json"

# TIKA
TIKA_URL = 'http://127.0.0.1:9998/tika'

# EOF
