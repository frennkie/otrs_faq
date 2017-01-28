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

from elasticsearch import Elasticsearch, RequestsHttpConnection, serializer, compat, exceptions
import config
import json
import argparse

### Versioning
__version_info__ = ('0', '1', '1')
__version__ = '.'.join(__version_info__)


SUBJECT = ["subject"]
FIELDS = ["field1", "field2", "field3", "field4", "field5", "field6"]
ATTACHMENTS = ["attachments.content"]

SUBJECT_EXACT = ["subject.raw"]
FIELDS_EXACT = ["field1.raw", "field2.raw", "field3.raw", "field4.raw", "field5.raw", "field6.raw"]
ATTACHMENTS_EXACT = ["attachments.content.raw"]

#class JSONSerializerPython2(serializer.JSONSerializer):
#    """Override elasticsearch library serializer to ensure it encodes utf characters during json dump.
#    See original at: https://github.com/elastic/elasticsearch-py/blob/master/elasticsearch/serializer.py#L42
#    A description of how ensure_ascii encodes unicode characters to ensure they can be sent across the wire
#    as ascii can be found here: https://docs.python.org/2/library/json.html#basic-usage
#    """
#    def dumps(self, data):
#        # don't serialize strings
#        if isinstance(data, compat.string_types):
#            return data
#        try:
#            return json.dumps(data, default=self.default, ensure_ascii=True)
#        except (ValueError, TypeError) as e:
#            raise exceptions.SerializationError(data, e)
#
def main():

    ### set up command line argument parsing
    parser = argparse.ArgumentParser(description="OTRS FAQ - ES search")
    parser.add_argument("-V", "--version",
                        help="print version",
                        action="version", version=__version__)
    parser.add_argument("-v", "--verbose",
                        help="debug output verbosity",
                        action="count")

    parser.add_argument("pattern",
                        help="what to search for",
                        action="store")

    parser.add_argument("--fuzzy",
                        help="do fuzzy search instead of exact word matches",
                        action="store_true")

    parser.add_argument("--exclude-subject",
                        help="iexclude subject line",
                        action="store_true")

    parser.add_argument("--exclude-body",
                        help="exclude FAQ body fields",
                        action="store_true")

    parser.add_argument("--include-attachments",
                        help="include attachments",
                        action="store_true")

    args = parser.parse_args()

    search_fields = list()
    if args.fuzzy:
        if not args.exclude_subject:
            search_fields += SUBJECT
        if not args.exclude_body:
            search_fields += FIELDS
        if args.include_attachments:
            search_fields += ATTACHMENTS
    else:
        if not args.exclude_subject:
            search_fields += SUBJECT_EXACT
        if not args.exclude_body:
            search_fields += FIELDS_EXACT
        if args.include_attachments:
            search_fields += ATTACHMENTS_EXACT

    print("Searching for \"{0}\" in {1}".format(args.pattern, ",".join(search_fields)))

    # Python2
    #es = Elasticsearch(serializer=JSONSerializerPython2())
    es = Elasticsearch()

    res = es.search(index="faqs", body={
        "query": {
            "multi_match": {
                "query": args.pattern,
                "operator": "and",
                "fields": search_fields
            }
        }
    })

    for hit in res['hits']['hits']:
        print(u"{0}: (Score: {1}) {2}".format(hit["_id"], hit["_score"], hit["_source"]["subject"]))

if __name__ == "__main__":
    main()

# EOF
