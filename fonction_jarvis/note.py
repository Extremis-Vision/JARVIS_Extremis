import markdown

with open('note.md', 'r') as f:
    markdown_text = f.read()

html_text = markdown.markdown(markdown_text)
print(html_text)