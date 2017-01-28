#!/usr/bin/env python3
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

from elasticsearch import Elasticsearch
import config
import json
import sys
import argparse

### Versioning
__version_info__ = ('0', '1', '1')
__version__ = '.'.join(__version_info__)

if sys.version_info <= (3, 2):
    sys.stdout.write("Sorry, requires Python >3.2, not Python 2.x\n")
    sys.exit(1)

SUBJECT = ["subject"]
FIELDS = ["field1", "field2", "field3", "field4", "field5", "field6"]
ATTACHMENTS = ["attachments.content"]

SUBJECT_EXACT = ["subject.raw"]
FIELDS_EXACT = ["field1.raw", "field2.raw", "field3.raw", "field4.raw", "field5.raw", "field6.raw"]
ATTACHMENTS_EXACT = ["attachments.content.raw"]


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

    parser.add_argument("-d", "--disable-exact",
                        help="disable exact word matching",
                        action="store_true")

    parser.add_argument("-f", "--fuzzy",
                        help="enable fuzzy (typo) matching (default: 0)",
                        type=str, choices=['AUTO', '0', '1', '2'],
                        default="0", action="store")

    parser.add_argument("-s", "--exclude-subject",
                        help="exclude subject line",
                        action="store_true")

    parser.add_argument("-b", "--exclude-body",
                        help="exclude FAQ body fields",
                        action="store_true")

    parser.add_argument("-a", "--include-attachments",
                        help="include attachments",
                        action="store_true")

    args = parser.parse_args()

    search_fields = list()

    if args.disable_exact:
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

    if args.verbose:
        print("Searching for \"{0}\" in {1}".format(args.pattern, ",".join(search_fields)))

    es = Elasticsearch()

    if args.fuzzy:
        res = es.search(index="faqs", body={
            "query": {
                "multi_match": {
                    "query": args.pattern,
                    "fuzziness": args.fuzzy,
                    "operator": "and",
                    "fields": search_fields
                }
            }
        })
    else:
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
        print(u"{0} - Score: {1:.3f}: {2}".format(hit["_id"], hit["_score"], hit["_source"]["subject"]))

    print("\n")

if __name__ == "__main__":
    main()

# EOF
