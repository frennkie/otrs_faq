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
                faq_attachment_dict.update(parser.from_buffer(faq_attachment['content']))
                faq_attachments.append(faq_attachment_dict)
            faq_object.update({"attachments": faq_attachments})

            faq_object_list.append(faq_object)

finally:
    connection.close()

# Open Elasticsearch connection and input data
es = elasticsearch.Elasticsearch()  # use default of localhost, port 9200
ic = elasticsearch.client.IndicesClient(es)

print("### remove any existing indexes ###")
es.indices.delete(index='faqs', ignore=[400, 404])

print("### create index with settings and mapping ###")
ic.create(index='faqs', body=
{
    "mappings": {
        "faq": {
            "dynamic_templates": [
                {
                    "default_for_all": {
                        "mapping": {
                            "fields": {
                                "de": {
                                    "analyzer": "german",
                                    "type": "text"
                                },
                                "en": {
                                    "analyzer": "english",
                                    "type": "text"
                                },
                                "raw": {
                                    "analyzer": "standard",
                                    "type": "text"
                                },
                                "keyword": {
                                    "ignore_above": 50,
                                    "type": "keyword"
                                }
                            },
                            "type": "text",
                            "analyzer": "trigrams"
                        },
                        "match": "*",
                        "match_mapping_type": "string"
                    }
                }
            ]
        }
    },
    "settings": {
        "analysis": {
            "analyzer": {
                "trigrams": {
                    "filter": [
                        "lowercase",
                        "trigrams_filter"
                    ],
                    "tokenizer": "standard",
                    "type": "custom"
                }
            },
            "filter": {
                "trigrams_filter": {
                    "max_gram": 3,
                    "min_gram": 3,
                    "type": "ngram"
                }
            }
        }
    }
}
)


print("### build new index ###")
for item in faq_object_list:
    es.index(index='faqs', doc_type='faq', id=item['faq_id'], body=item)


# EOF
