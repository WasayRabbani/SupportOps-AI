from pathlib import Path

# Main purpose is to take a text file, convert it into langchain document object
from langchain_community.document_loaders import TextLoader


# Makes any link, system link

policy_folder = Path(r"D:\Coding Stuff\SupportOps AI\data\policies")

documents = []


# Here we fetch all the files in that link that are having .md at the back.

# every md file it finds, temporarily calls that file
# file is Path object (Path that we fetched earlier), not filename
for file in policy_folder.glob("*.md"):

    # file -> Path("D:/Coding Stuff/.../faq.md")
    # str(file) gives  "D:/Coding Stuff/.../faq.md" like a normal string
    # Then we give it to TextLoader and it loads the documents  but when we use .load , it shows to user

    # Now we need to add extracted documents into list
    documents.extend(TextLoader(str(file)).load())

# for document in documents:
#         print(document.page_content)
print(documents[0].page_content)
