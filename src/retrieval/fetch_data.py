import pdfplumber
from pathlib import Path


class Fetch_data:
    def __init__(self, path):
        self.path = Path(path)

    def fetch_pdf(self):

        all_pages = []
        for file in self.path.glob("*.pdf"):  # fetches the files one by one.
            with pdfplumber.open(file) as pdf:  # opens first pdf using library
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    table = page.extract_tables()
                    page_data = {
                        'file_name': file.name, 'page_num': i, 'text': text, 'tables': table}
                    all_pages.append(page_data)
        return all_pages
# Output


obj = Fetch_data(r'D:\Coding Stuff\SupportOps AI\data\policies')
pages = (obj.fetch_pdf())


for p in (pages):
    print(p['file_name'], (((p['text'][0:200]))))


"""
What we did
Step 1: Fetched all the text and tables from all the pdf in an organized way. Got page numbers, file names and the text it has and the tables per page.
"""
