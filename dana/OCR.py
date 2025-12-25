import ocrmypdf

# Simple one-liner to convert your PDF to searchable format
ocrmypdf.ocr(
    'Jacques-Martel-Marele-dictionar-al-bolilor-si-afectiunilor.pdf',
    'searchable_output.pdf',
    language='ron',  # Romanian
    deskew=True,
    rotate_pages=True,
    output_type='pdf',
    progress_bar=True
)

print("Done! Your searchable PDF is ready.")