from spire.pdf import PdfDocument
from spire.pdf import FileFormat

doc = PdfDocument()
doc.LoadFromFile("./2024年政府公报第1期.pdf")
doc.SaveToFile("output.html", FileFormat.HTML)