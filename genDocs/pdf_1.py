# pip install --upgrade fpdf2
import csv
# from fpdf import FPDF
# from fpdf.fonts import FontFace
# from fpdf.enums import TableCellFillMode

def cobros():
    # object
    # layout 'P', 'L'
    # units 'mm', 'cm', 'in'
    # format 'A3', 'A4', 'letter', 'legal', (110,150)
    pdf = FPDF('P', 'mm', 'letter')

    # add a page
    pdf.add_page()

    # fonts ('times', 'courier', 'helvetica', 'symbol') 
    # 'B' bold, 'U' underline, 'I' italics, '' regular, combination 'BU'
    # size 4 ~ ...
    pdf.set_font('helvetica', 'BIU', '16')

    # Color
    pdf.set_text_color(220,50,50)

    # add text
    # w = width
    # h = height
    # text
    # ln= next line
    # border= border line arown the cel
    pdf.cell(80, 10, 'Hello World')
    pdf.cell(80, 10, 'Good Bye World', ln=True)

    pdf.set_font('times', '', 12)
    pdf.cell(50, 30, 'Next Line', border=True)

    pdf.set_font('times', '', 12)

    # generar el archivo
    pdf.output('docs/pdf_1.pdf')

    return
    

def cobros_2():
    pdf = FPDF('P', 'mm', 'letter')

    # add a page
    pdf.add_page()
    pdf.set_font('helvetica', 'BIU', 16)

    # add text
    pdf.cell(80, 10, 'Hello World')
    pdf.cell(80, 10, 'Good Bye World', ln=True)
    pdf.cell(50, 30, 'Next Line', ln=True)

    pdf.set_font('times', '', 12)
    for i in range(1, 41):
        pdf.cell(0, 10, f'This is line {i}', ln=True)


    pdf.output('docs/pdf_2.pdf')

    return


def reporteCobros(client, ventas):
    pdf = FPDF('P', 'mm', 'letter')
    pdf.add_page()
    
    for c in client:
        pdf.set_font('helvetica', 'BIU', 16)
        pdf.cell(60, 3, '-'*44, ln=True)
        pdf.cell(80, 15, c, ln=True)

        for venta in ventas:
            pdf.set_font('times', '', 7)
            if venta['cliente'] == c:
                pdf.cell(4, 5, str(venta['qty']))
                pdf.cell(70,5, venta['producto'])
                pdf.cell(20, 5, str(venta['total']), ln=True)
    
        pdf.set_font('times', '', 10)
        pdf.cell(90, 3, '', ln=True)

        pdf.cell(60, 5, 'Rosa Liliana Rivera, C.C. 55.177.973', ln=True)
        pdf.cell(60, 5, 'C. Ahorros No. 18876368419. Bancolombia', ln=True)
        pdf.cell(60, 5, 'Nequi: 310 340 2169', ln=True)

    pdf.output('docs/pdf_3.pdf')

    return


def julioV():
    with open("docs/countries.txt", encoding="utf8") as csv_file:
        data = list(csv.reader(csv_file, delimiter=","))

    pdf = FPDF()
    pdf.set_font("helvetica", size=14)

    # Basic table:
    pdf.add_page()
    with pdf.table() as table:
        for data_row in data:
            row = table.row()
            for datum in data_row:
                row.cell(datum)

    # Styled table:
    pdf.add_page()
    pdf.set_draw_color(255, 0, 0)
    pdf.set_line_width(0.3)
    headings_style = FontFace(emphasis="BOLD", color=255, fill_color=(255, 100, 0))
    with pdf.table(
        borders_layout="NO_HORIZONTAL_LINES",
        cell_fill_color=(224, 235, 255),
        cell_fill_mode=TableCellFillMode.ROWS,
        col_widths=(42, 39, 35, 42),
        headings_style=headings_style,
        line_height=6,
        text_align=("LEFT", "CENTER", "RIGHT", "RIGHT"),
        width=160,
    ) as table:
        for data_row in data:
            row = table.row()
            for datum in data_row:
                row.cell(datum)

    pdf.output("docs/tuto5.pdf")

