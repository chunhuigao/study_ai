import fitz

doc = fitz.open("./2024年政府公报第1期.pdf")
print(f"PDF总页数: {doc.page_count}")

html_parts = []
for i, page in enumerate(doc):
    html_parts.append(page.get_text("html"))
    if (i + 1) % 10 == 0:
        print(f"已转换 {i + 1}/{doc.page_count} 页")

with open("output_pymupdf.html", "w", encoding="utf-8") as f:
    f.write("<html><head><meta charset='utf-8'></head><body>")
    f.write("\n".join(html_parts))
    f.write("</body></html>")

print(f"转换完成，共 {doc.page_count} 页，输出文件: output_pymupdf.html")
doc.close()