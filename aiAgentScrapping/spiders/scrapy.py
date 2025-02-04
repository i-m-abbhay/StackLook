import scrapy
from urllib.parse import urljoin
import logging

class DocsSpider(scrapy.Spider):
    name = "docs_code"
    start_urls = ['https://laravel.com/docs/11.x']
    visited_links = set()

    def parse(self, response):
        if response.url in self.visited_links:
            return
        self.visited_links.add(response.url)

        hierarchy_stack = []
        document_structure = []

        # Extract both content and code blocks
        for element in response.css('h1, h2, h3, h4, h5, h6, p, pre, code, .syntax-highlighter'):
            tag = element.root.tag
            
            # Handle code blocks specially
            if tag in ['pre', 'code'] or 'syntax-highlighter' in element.attrib.get('class', ''):
                text = " ".join(element.css("::text").getall()).strip()
                code_lang = element.attrib.get('class', '').split('-')[-1] if 'language-' in element.attrib.get('class', '') else ''
                content = f"```{code_lang}\n{text}\n```" if text else ''
            else:
                content = " ".join(element.css("::text").getall()).strip()

            if not content:
                continue

            if tag.startswith('h'):
                level = int(tag[1])
                heading_node = {
                    "title": content,
                    "content": [],
                    "subheadings": [],
                    "url": response.url,
                    "section_id": element.attrib.get('id', '')
                }
                
                while hierarchy_stack and hierarchy_stack[-1]['level'] >= level:
                    hierarchy_stack.pop()
                
                if hierarchy_stack:
                    hierarchy_stack[-1]['node']['subheadings'].append(heading_node)
                else:
                    document_structure.append(heading_node)
                    
                hierarchy_stack.append({"level": level, "node": heading_node})
            else:
                if hierarchy_stack:
                    hierarchy_stack[-1]['node']['content'].append(content)
                else:
                    document_structure.append({
                        "title": "No Heading",
                        "content": [content],
                        "subheadings": [],
                        "url": response.url
                    })

        # Yield the structured content
        yield {
            "url": response.url,
            "structure": document_structure,
            "title": response.css('title::text').get(),
            "last_updated": response.css('.last-updated::text').get()
        }

        # Follow documentation links
        for link in response.css('a[href^="/docs"]::attr(href)').getall():
            absolute_url = urljoin(response.url, link)
            if absolute_url not in self.visited_links:
                yield response.follow(absolute_url, callback=self.parse)

        logging.info(f"Processed {response.url}, found {len(document_structure)} sections")