import scrapy
from urllib.parse import urljoin

class DocsSpider(scrapy.Spider):
    name = "docs"
    start_urls = ['https://nextjs.org/docs']  # Replace with the main documentation URL
    visited_links = set()  # To track visited links

    def parse(self, response):
        self.visited_links.add(response.url)

        # Track the hierarchy
        hierarchy_stack = []
        document_structure = []

        # Select headings, paragraphs, and code blocks in the order they appear
        for element in response.css('h1, h2, h3, h4, h5, h6, p, pre, code '):
            tag = element.root.tag
            text = element.css('::text').get().strip()

            if tag.startswith('h'):  # Handling heading tags
                level = int(tag[1])  # Extract heading level (1-6)
                heading_node = {"title": text, "content": [], "subheadings": []}

                # Adjust the stack to the correct hierarchy level
                while hierarchy_stack and hierarchy_stack[-1]['level'] >= level:
                    hierarchy_stack.pop()

                if hierarchy_stack:
                    hierarchy_stack[-1]['node']['subheadings'].append(heading_node)
                else:
                    document_structure.append(heading_node)

                # Push current heading to the stack
                hierarchy_stack.append({"level": level, "node": heading_node})

            elif tag == 'p'or tag == 'code' or tag== 'pre':  # Handling paragraph tags
                if hierarchy_stack:
                    hierarchy_stack[-1]['node']['content'].append(text)
                else:
                    # Paragraph without a heading (rare case)
                    document_structure.append({"title": "No Heading", "content": [text], "subheadings": []})

            elif tag in ['code']:  # Handling code blocks
                if hierarchy_stack:
                    hierarchy_stack[-1]['node']['content'].append(f"```{text}```")
                else:
                    # Code block without a heading (rare case)
                    document_structure.append({"title": "No Heading", "content": [f"```{text}```"], "subheadings": []})

        yield {
            "url": response.url,
            "structure": document_structure
        }

        # Follow internal links that start with '/docs'
        for link in response.css('a::attr(href)').getall():
            if link.startswith('/docs'):
                absolute_url = urljoin(response.url, link)
                if absolute_url not in self.visited_links:
                    self.visited_links.add(absolute_url)
                    yield response.follow(absolute_url, callback=self.parse)
