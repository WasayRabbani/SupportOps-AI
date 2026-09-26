from pathlib import Path

# Main purpose is to take a text file, convert it into langchain document object
from langchain_core.documents import Document


class fetch_data:
    def __init__(self, path):

        self.path = Path(path)
        # Makes any link, system link

    def fetch_docs(self):

        documents = []

        # Here we fetch all the files in that link that are having .md at the back.

        # every md file it finds, temporarily calls that file
        # file is Path object (Path that we fetched earlier), not filename
        for file in self.path.glob("*.md"):

            # file -> Path("D:/Coding Stuff/.../faq.md")
            # str(file) gives  "D:/Coding Stuff/.../faq.md" like a normal string

            text = file.read_text(encoding="utf-8")

            document = Document(
                page_content=text,
                metadata={"source": str(file)}
            )

            documents.append(document)

        # for document in documents:
        #         print(document.page_content)
        return (documents[0].page_content)


obj = fetch_data(r"D:\Coding Stuff\SupportOps AI\data\policies")
print(obj.fetch_docs())
