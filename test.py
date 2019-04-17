from xml import xml

document = xml.parse_file("testxml.xml")

print(document.root.name)
