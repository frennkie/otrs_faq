#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2017 frennkie (https:/github.com/frennkie)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import print_function
from __future__ import unicode_literals

import pymysql.cursors
import pymysql
import tika
from tika import parser
import elasticsearch
import config
# import certifi  # could also be used for SSL/TLS verification


# Connect to the database
connection = pymysql.connect(host=config.MYSQL_HOST,
                             user=config.MYSQL_USER,
                             password=config.MYSQL_PASS,
                             db=config.MYSQL_DB,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

faq_object_list = list()

try:
    with connection.cursor() as cur:
        # Create a new record
        sql = """SELECT DISTINCT(faq_item.id)
                    FROM faq_item
                    ORDER BY id ASC"""
        cur.execute(sql)

    # sample for unique_faq_ids: [{u'id': 1}, {u'id': 2}, {u'id': 3}]
    unique_faq_ids = list(cur.fetchall())

    with connection.cursor() as cur:
        for faq in unique_faq_ids:
            print("### Working on FAQ #{0} ###".format(faq['id']))
            # instantiate new clean dict
            faq_object = dict()
            faq_object.update({"faq_id": faq['id']})

            # get FAQ details
#            sql = """SELECT i.f_name, i.f_language_id, i.f_subject as subject, i.created, i.created_by, i.changed,
#                        i.changed_by, i.category_id, i.state_id, c.name, s.name, l.name, i.f_keywords as keywords,
#                        i.approved, i.valid_id, i.content_type, i.f_number, st.id, st.name,
#                        i.f_field1 as field1, i.f_field2 as field2, i.f_field3 as field3,
#                        i.f_field4 as field4, i.f_field5 as field5, i.f_field6 as field6
#                    FROM faq_item i, faq_category c, faq_state s, faq_state_type st, faq_language l
#                    WHERE i.state_id = s.id
#                        AND s.type_id = st.id
#                        AND i.category_id = c.id
#                        AND i.f_language_id = l.id
            sql = """SELECT i.f_subject as subject, i.f_keywords as keywords,
                        i.f_field1 as field1, i.f_field2 as field2, i.f_field3 as field3,
                        i.f_field4 as field4, i.f_field5 as field5, i.f_field6 as field6
                    FROM faq_item i
                    WHERE i.id = %(faq_id)s"""
            cur.execute(sql, {"faq_id": faq['id']})

            faq_object.update(cur.fetchone())

            sql = """SELECT filename, content_type, content_size, content
                         FROM faq_attachment
                         WHERE faq_id = %(faq_id)s"""
            cur.execute(sql, {"faq_id": faq['id']})

            faq_attachments = list()
            for faq_attachment in cur.fetchall():
                faq_attachment_dict = dict()
                faq_attachment_dict.update({"filename": faq_attachment['filename']}),
                faq_attachment_dict.update({"content_type": faq_attachment['content_type']}),
                faq_attachment_dict.update({"content_size": faq_attachment['content_size']}),

                # faq_attachment_dict.update(parser.from_buffer(faq_attachment['content'], 'http://192.168.92.77:9080/tika'))

                parsed_dict = parser.from_buffer(faq_attachment['content'], config.TIKA_URL)

                parsed_content = parsed_dict['content'].replace("-\n", "")
                parsed_content = parsed_content.replace("\n\n", "")
                parsed_content = parsed_content.replace("\n", " ")

                parsed_dict.pop('content')
                parsed_dict['content'] = parsed_content

                faq_attachment_dict.update(parsed_dict)

                faq_attachments.append(faq_attachment_dict)
            faq_object.update({"attachments": faq_attachments})

            faq_object_list.append(faq_object)

finally:
    connection.close()

# Open Elasticsearch connection and input data
if config.ES_USER and config.ES_PASS:
    es = elasticsearch.Elasticsearch([config.ES_HOST],
                                     http_auth=(config.ES_USER, config.ES_PASS),
                                     port=config.ES_PORT,
                                     use_ssl=config.ES_USE_SSL,
                                     verify_certs=False)
    # ca_certs=config.ES_CA_CERTS)
else:
    es = elasticsearch.Elasticsearch([config.ES_HOST], port=config.ES_PORT)

ic = elasticsearch.client.IndicesClient(es)

print("### remove any existing indexes ###")
es.indices.delete(index=config.ES_INDEX, ignore=[400, 404])

with open(config.ES_INDEX_SETTING_MAPPING_FILE, 'r') as f:
    es_index_setting_mapping = f.read()


print("### create index with settings and mapping ###")
ic.create(index=config.ES_INDEX, body=es_index_setting_mapping)


print("### build new index ###")
for item in faq_object_list:
    es.index(index=config.ES_INDEX, doc_type=config.ES_DOC_TYPE, id=item['faq_id'], body=item)


# EOF
