# -*- coding: utf-8 -*-
r"""
>>> import markdown
>>> md = markdown.Markdown(extensions=['spoiler'])
>>> inp = u'!~~~Click me to expand!\nText inside spoiler!\n\nFew lines!\n/~~~'
>>> md.convert(inp)
u'<details><summary>Click me to expand!</summary><p>Text inside spoiler!</p>\n<p>Few lines!</p>\n</details>'
"""
import re
import markdown
from markdown.util import etree


OPEN_TAG = r'\!~{2,}'
CLOSE_TAG = r'\/\!?~{2,}'


class SpoilerProcessor(markdown.blockprocessors.BlockProcessor):
    OPEN_RE = re.compile(r'(?:^|\n)'
                         + OPEN_TAG
                         + r'[\ \t]*(?P<summary>[^\n]*)'
                           r'(?:$|\n)', re.M | re.I | re.U)
    CLOSE_RE = re.compile(r'(?:^|\n)'
                          + CLOSE_TAG
                          + r'[\ \t]*(?:$|\n)', re.M | re.I | re.U)

    def test(self, parent, block):
        return bool(self.OPEN_RE.search(block) or self.CLOSE_RE.search(block))

    def run(self, parent, blocks):
        block = blocks.pop(0)
        open_match = self.OPEN_RE.search(block)
        if open_match:
            before = block[:open_match.start()]
            rest = block[open_match.start():]
            if before:
                # some block before opening spoiler tag
                blocks.insert(0, rest)
                blocks.insert(0, before)
                return

            name = open_match.group('summary')
            details = etree.SubElement(parent, 'details')
            summary = etree.SubElement(details, 'summary')
            summary.text = name

            rest = block[open_match.end():]

            if rest:
                blocks.insert(0, rest)
                return

        close_match = self.CLOSE_RE.search(block)
        if close_match:
            before = block[:close_match.start()]
            if before:
                rest = block[close_match.start():]
                if rest:
                    blocks.insert(0, rest)
                blocks.insert(0, before)
                return
            etree.SubElement(parent, 'end-of-spoiler')
            rest = block[close_match.end():]
            if rest:
                blocks.insert(0, rest)



class DetailsProcessor(markdown.treeprocessors.Treeprocessor):

    def run(self, root):
        spoiler_tag = 'details'
        closing_tag = 'end-of-spoiler'
        spoilers =[]
        for child_node in root:
            if child_node.tag.lower() == closing_tag:
                if spoilers:
                    spoilers.pop()
                root.remove(child_node)
                continue
            if spoilers:
                spoilers[-1].append(child_node)
                root.remove(child_node)
            if child_node.tag.lower() == spoiler_tag:
                spoilers.append(child_node)




class SpoilerExtension(markdown.Extension):
    """ Add tables to Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Add an instance of TableProcessor to BlockParser. """
        md.parser.blockprocessors.add('spoiler',
                                      SpoilerProcessor(md.parser),
                                      '_begin')
        md.treeprocessors.add('spoiler', DetailsProcessor(), '_end')

def makeExtension(configs=None):
    if configs is None:
        configs = {}
    return SpoilerExtension(**configs)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
