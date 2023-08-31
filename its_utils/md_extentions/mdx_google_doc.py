#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import re
import markdown
from markdown.util import etree


class GoogleDocProcessor(markdown.blockprocessors.BlockProcessor):

    G_DOC = re.compile(r'\[g_doc\].+\[\/g_doc\]')

    def test(self, parent, block):
        return bool(self.G_DOC.search(block))

    def run(self, parent, blocks):
        string = blocks.pop(0)
        document_link = string[string.find('[g_doc]')+7:string.find('[/g_doc]')]
        document_div = etree.SubElement(parent, 'iframe')
        document_div.set("src", document_link)
        document_div.set("style", "width:90%; height:800px; display: block; margin-left:auto; margin-right:auto;")


class GoogleDocExtension(markdown.Extension):

    def extendMarkdown(self, md, md_globals):
        md.parser.blockprocessors.add('google_doc',
                                      GoogleDocProcessor(md.parser),
                                      '_begin')


def makeExtension(configs={}):
    return GoogleDocExtension(**configs)
