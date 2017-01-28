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

import elasticsearch
import config

es = elasticsearch.Elasticsearch()


test_cases = [ { "id": 1,
                 "pattern": "Einträge",
                 "field": "subject.raw"},
               { "id": 2,
                 "pattern": "Einträg",
                 "field": "subject.raw"},
               { "id": 3,
                 "pattern": "Eintrag",
                 "field": "subject.raw"},
               { "id": 4,
                 "pattern": "Einträge",
                 "field": "subject.de"},
               { "id": 5,
                 "pattern": "Einträg",
                 "field": "subject.de"},
               { "id": 6,
                 "pattern": "Eintrag",
                 "field": "subject.de"},
               { "id": 7,
                 "pattern": "Einträge",
                 "field": "subject.en"},
               { "id": 8,
                 "pattern": "Einträg",
                 "field": "subject.en"},
               { "id": 9,
                 "pattern": "Eintrag",
                 "field": "subject.en"},
               { "id": 10,
                 "pattern": "Einträge",
                 "field": "subject"},
               { "id": 11,
                 "pattern": "Einträg",
                 "field": "subject"},
               { "id": 12,
                 "pattern": "Eintrag",
                 "field": "subject"}
               ]

for case in test_cases:
    print(u"\n### Tase Case: {0}".format(case["id"]))
    print(u"Check for {0} in {1}".format(case["pattern"], case["field"]))
    res = es.search(index="faqs", body={"query": {"match": {case["field"]: case["pattern"]}}})

    for hit in res['hits']['hits']:
        print(u"{0}: (Score: {1}) {2}".format(hit["_id"], hit["_score"], hit["_source"]["subject"]))

# EOF
