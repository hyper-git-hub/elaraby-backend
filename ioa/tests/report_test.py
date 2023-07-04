from datetime import datetime, timedelta
import os
import traceback
from dateutil.parser import parse
from django.db.models import Sum, F, Value, FloatField, ExpressionWrapper, Count
from django.utils import timezone
from reportlab.graphics.shapes import Drawing, Line
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import portrait, A4, A3, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image, KeepTogether
from reportlab.lib import colors
from rest_framework.views import APIView
from pathlib import Path
import inflect


from backend import settings
from customer.models import CustomerPreferences, CustomerClients
from hypernet.constants import RESPONSE_MESSAGE, RESPONSE_STATUS, HTTP_SUCCESS_CODE, RESPONSE_DATA, HTTP_ERROR_CODE, \
    TEXT_PARAMS_MISSING
from hypernet.enums import IOFOptionsEnum
from hypernet.utils import generic_response, get_customer_from_request, get_default_param, get_list_param
from iof.utils import get_clients_invoice

style_b = getSampleStyleSheet()
page_info = " Hypernymbiz L.L.C\u00AE"
page_info += " NOTE: This report is system generated and All times are in UTC"

data_folder = Path(settings.STATIC_ROOT + "report_images/")
image_hypernym = data_folder / "logo-hypernym.png"
I_hyper = Image(image_hypernym)
# I = Image(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media/zenath_imgs/zenath_logo.jpg'))
I_hyper.drawHeight = 0.8 * inch * I_hyper.drawHeight / I_hyper.drawWidth
I_hyper.drawWidth = 0.8 * inch
I_hyper.hAlign = 'LEFT'
I_hyper.vAlign = 'BOTTOM'


class ReportViewInvoice(APIView):

    def myPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, page_info))
        canvas.drawImage(image_hypernym, x=(720), y=(50), anchor='c', width=60, height=40)
        canvas.restoreState()

    def _create_pdf_invoice(self, filename, invoice_data, client_obj, s_date, e_date, preferences):
        current_tz = timezone.get_current_timezone()

        style_h1 = style_b["Heading1"]
        style_h2 = style_b["Heading2"]
        style_h3 = style_b["Heading3"]
        style_h4 = style_b["Heading4"]
        style_n = style_b["Normal"]

        style_para = ParagraphStyle('parrafos',
                           alignment=TA_JUSTIFY,
                           fontSize=13,
                           fontName="Times-Roman")

        d_line = Drawing(100, 1)
        d_line.add(Line(0, 0, 280, 0))

        doc = SimpleDocTemplate(filename, pagesize=portrait(A3), rightMargin=45, leftMargin=45, topMargin=50)
        invoice = [] #Main List of items for PDF.

        image_zenath = data_folder / "zenath_logo.jpg"

        invoice_para = Paragraph("Invoice Report ", style_h2)
        invoice_para.hAlign = 'CENTER'
        invoice.append(invoice_para)
        invoice.append(Spacer(1, 0.5 * inch))

        I = Image(image_zenath)
        I.drawHeight = 2 * inch * I.drawHeight / I.drawWidth
        I.drawWidth = 2 * inch
        I.hAlign = 'LEFT'
        I.vAlign = 'TOP'
        invoice.append(I)

        if preferences:
            pref_data = Paragraph("<font color='#014172'>"+"Company Name: "+preferences.company_name+"<br/>"+"Address: "+preferences.address+"<br/>"+
                                  "Phone No: "+preferences.phone_no+"<br/>"+"Fax No"+preferences.fax_no+"<br/>"+"Email: "+preferences.email+"<br/>"+
                                  "Website: "+preferences.url+"</font>", style_n)
            pref_data.hAlign = 'CENTER'
            pref_data.vAlign = 'TOP'
            invoice.append(pref_data)

        if client_obj and (s_date and e_date):
            #FIXME {Comment it if using postman,}
            s_date = parse(s_date)
            e_date = parse(e_date)

            client_name = Paragraph(client_obj.name+"<br/>"+client_obj.party_code+"<br/>"+
                                    " " if not client_obj.contact_number else client_obj.contact_number +"<br/>", style_h4)
            client_name.hAlign = 'LEFT'
            client_name.vAlign = 'TOP'

            client_party_code = Paragraph(client_obj.party_code+"<br/>", style_h4)
            client_party_code.hAlign = 'LEFT'
            client_party_code.vAlign = 'TOP'

            client_phone = Paragraph(" " if not client_obj.contact_number else client_obj.contact_number +"<br/>", style_h4)
            client_phone.hAlign = 'LEFT'
            client_phone.vAlign = 'TOP'

            tax_invoice_text = Paragraph("Tax Invoice", style_h3)
            # right_pl_holder = Paragraph("Duration: "+ str(s_date.date())+' To '+str(e_date.date())+"<br/>"+
            #                             "Service Type: SST<br/>"+"Minimum Trips: -", style_n)
            right_pl_holder = [['Duration: ', str(s_date.date())+' To '+str(e_date.date())], ['Service Type: ' ,'SST'], ['Minimum Trips: ', '-']]
            t = Table(right_pl_holder, style=[
                                ('FONTSIZE', (0, 0), (-1, -1), 11),
                                # ('BOX', (0, 0), (0, 1), 1, colors.black),
                                   ])
            t.hAlign = 'LEFT'
            empty = Paragraph(" ", style_h3)
            top_table_data = [[client_name, empty, empty],[tax_invoice_text, t]]

            top_table = KeepTogether(Table([top_table_data], style=[('GRID', (0, 0), (-1, -1), 1, colors.black),
                                                       ('BOX', (0, 0),(0, 1), 2, colors.gray),
                                   ('FONTSIZE', (0, 0), (-1, -1), 11),
                                   ]))
            top_table.hAlign = 'LEFT'
            invoice.append(Spacer(1,0.2*inch))
            invoice.append(top_table)
            invoice.append(Spacer(1,0.2*inch))

        data = []
        data.append(['Contract#', 'Location', 'Contract Type', 'Trips', 'Skip Rate', 'VAT', 'Net(AED)', 'Total(AED)'])
        data[1:] = [[x['contract_no'], x['location'], x['contract_type'], x['trips'], x['skip'], x['vat'], x['net_amount'], x['after_tax']] for x in invoice_data]

        total_amount_bt = sum(item['net_amount'] for item in invoice_data)
        total_invoice = sum(item['after_tax'] for item in invoice_data)

        inv_table = (Table(data, style=[('GRID', (0, 0), (-1, -1), 1, colors.black),
                               ('FONTSIZE', (0, 0), (7, 0), 16),
                               ('FONTSIZE', (0, 0), (-1, -1), 13),
                               # ('FONTSIZE', (0, 1), (1, 0), 11),
                               ('FONTSIZE', (1, 1), (1,-1), 10),
                               ('TEXTFONT', (0, 0), (7, 0), 'Times New Roman Bold'),
                               ('BACKGROUND', (0, 0), (7, 0), colors.lightgrey),
                               ('BOX', (0, 0), (-1, -1), 2, colors.black),
                               ('BOX', (0, 0), (7, 0), 2, colors.black),
                               ('VALIGN', (0, 0), (7, 0), 'MIDDLE'),
                               ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
                               ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
                               ('ALIGN', (6, 1), (6, -1), 'RIGHT'),
                               ('ALIGN', (7, 1), (7, -1), 'RIGHT'),
                               ], rowHeights=0.4*inch))

        inv_table.hAlign = 'LEFT'
        inv_table._argW[1] = 3.74 * inch
        inv_table._argW[0] = 1.0 * inch
        inv_table._argW[7] = 1.25 * inch
        inv_table._argW[3] = 0.6 * inch
        # inv_table._arqW[1] =

        invoice.append(inv_table)
        invoice.append(Spacer(1, 0.2*inch))
        amount_data = []

        invoice_total_bt_plh = Paragraph("Invoice Total Before Tax(AED):<br/>", style_para)
        invoice_total_bt_amnt = Paragraph("<b>"+"{0:.2f}".format(total_amount_bt)+"</b><br/>", style_para)
        amount_data.append([invoice_total_bt_plh, invoice_total_bt_amnt])

        invoice_total_at_plh = Paragraph("Invoice Total After Tax(AED):<br/>", style_para)
        invoice_total_at_amnt = Paragraph("<b>" + "{0:.2f}".format(total_invoice)+"</b><br/>", style_para)
        amount_data.append([invoice_total_at_plh, invoice_total_at_amnt])

        coverter = inflect.engine()
        in_words_amount = coverter.number_to_words(int(total_invoice))
        in_words_amount = in_words_amount.replace('-', " ")
        in_words_amount_para_plh = Paragraph("Invoice Total After Tax(AED) in words:<br/>", style_para)
        in_words_amount_para_amnt = Paragraph("<b>" + in_words_amount.title()+" Only</b><br/>", style_para)
        amount_data.append([in_words_amount_para_plh, in_words_amount_para_amnt])

        amount_table = KeepTogether(Table(amount_data, style=[('GRID', (0, 0), (-1, -1), 1, colors.black),
                               ('FONTSIZE', (0, 0), (0, 2), 14),
                               ('FONTSIZE', (0, 0), (-1, -1), 12),
                               ('TEXTFONT', (0, 0), (0, 2), 'Times New Roman Bold'),
                               ('BOX', (0, 0), (-1, -1), 2, colors.black),
                               ('BOX', (0, 0), (0, 2), 2, colors.black),], rowHeights=0.4*inch))

        amount_table.hAlign = 'LEFT'
        invoice.append(amount_table)
        discription = "PLEASE ASK FOR OFFICIAL RECEIPT WHEN MAKING PAYMENT. THIS IS A SYSTEM GENERATED INVOICE " \
                      "AND DOES NOT REQUIRE A SIGNATURE <br/>PAYMENT SHOULD BE MADE BY A/C PAYEE CHEQUES FAVORING THE COMPANY.\n" \
                      "ANY DISCREPANCY SHOULD BE INTIMIDATED WITHIN SEVEN DAYS OTHERWISE THIS INVOICE WILL BE TREATED AS CORRECT\n"
        heading_d = Paragraph("<b>DISCLAIMER:</b>", style_h2)
        des = Paragraph(discription, style_h4)
        des.hAlign = 'LEFT'
        heading_d.hAlign = 'LEFT'
        invoice.append(Spacer(1, 0.2 * inch))
        invoice.append(heading_d)
        invoice.append(des)

        doc.build(invoice, onFirstPage=self.myPage, onLaterPages=self.myPage)

    def get_invoice_data(self, customer, client, contracts, s_date, e_date, s_id):
        try:
            preferences = CustomerPreferences.objects.get(customer_id=customer)
            invoice_qset = get_clients_invoice(client=client, customer=customer, start_datetime=s_date,
                                               end_datetime=e_date,
                                               contracts=contracts, status=s_id)

            if contracts:
                invoice_qset = invoice_qset.filter(contract_id__in=contracts)

            invoice_qset = invoice_qset.values('contract__name').annotate(invoice_sum=Sum('invoice'),
                                                                          total=ExpressionWrapper(F('invoice_sum') + (
                                                                          F('invoice_sum') * Value(
                                                                              preferences.value_added_tax,
                                                                              output_field=FloatField())) / 100,
                                                                                                  output_field=FloatField()))

            invoice_qset = invoice_qset.values(trips=Count('contract_id'),
                                               contract_type=F('contract__leased_owned__label'),
                                               client_name=F('client__party_code'),
                                               client_party_code=F('client__party_code'),
                                               location=F('area__name'), net_amount=F('invoice_sum'),
                                               after_tax=F('total'), vat=Value(preferences.value_added_tax,
                                                                               output_field=FloatField()),
                                               skip=F('contract__skip_rate'), contract_no=F('contract__name'))

            return invoice_qset

        except:
            print("REPORT QUERY ERROR:")
            traceback.print_exc()

    def get(self, request, format=None):

        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}

        customer = get_customer_from_request(request, None)
        client = get_default_param(request,'client',None)
        contracts_list = get_list_param(request,'contracts',None)
        s_date = get_default_param(request,'start_datetime',None)
        e_date = get_default_param(request,'end_datetime',None)

        now = datetime.now()
        dirc = os.makedirs(settings.MEDIA_ROOT + "/reports/", exist_ok=True)
        file_name = str(now.date()) + "-Invoice-Report"

        #FIXME {Un-Comment it if using postman,}
        # client = 3001
        # s_date = now - timedelta(days=10)
        # e_date = now + timedelta(days=10)
        # contracts_list = [8412]
        try:
            client_obj = CustomerClients.objects.get(pk=client)
        except CustomerClients.DoesNotExist:
            client_obj = None

        try:
            preferences = CustomerPreferences.objects.get(customer_id=customer)
        except CustomerClients.DoesNotExist:
            preferences = None

        if client_obj:
            invoice = self.get_invoice_data(customer=customer, client=client, contracts=contracts_list,
                            s_date=s_date, e_date=e_date, s_id=[IOFOptionsEnum.WASTE_COLLECTED, IOFOptionsEnum.BIN_PICKED_UP])

            self._create_pdf_invoice("media/reports/"+file_name + ".pdf", invoice, client_obj, s_date, e_date, preferences)

            file_url = (request.get_host()+"/media/reports/"+file_name + ".pdf")
            # print(os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name+".pdf"))
            response_body[RESPONSE_DATA] = {'file':file_url}
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            response_body[RESPONSE_MESSAGE] = "Report generated successfully"
        else:
            response_body[RESPONSE_DATA] = {'file': None}
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING

        return generic_response(response_body=response_body, http_status=HTTP_SUCCESS_CODE)


class ReportViewTripSheet(APIView):

    def myPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, page_info))
        canvas.drawImage(image_hypernym, x=(720), y=(50), anchor='se', width=60, height=40)
        canvas.restoreState()

    def _create_pdf_trips(self, filename, invoice_data, client_obj, s_date, e_date, preferences):
        current_tz = timezone.get_current_timezone()

        style_h1 = style_b["Heading1"]
        style_h2 = style_b["Heading2"]
        style_h3 = style_b["Heading3"]
        style_h4 = style_b["Heading4"]
        style_n = style_b["Normal"]

        d_line = Drawing(100, 1)
        d_line.add(Line(0, 0, 280, 0))

        doc = SimpleDocTemplate(filename, pagesize=landscape(A4), rightMargin=50, leftMargin=45, topMargin=50)

        invoice = [] #Main List of items for PDF.

        data_folder = Path(settings.STATIC_ROOT + "report_images/")
        image_file = data_folder / "zenath_logo.jpg"

        invoice_para = Paragraph("Trip Sheet", style_h2)
        invoice_para.hAlign = 'CENTER'
        invoice.append(invoice_para)
        invoice.append(Spacer(1, 0.5 * inch))
        styleSheet = style_b

        I = Image(image_file)
        # I = Image(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media/zenath_imgs/zenath_logo.jpg'))
        I.drawHeight = 2 * inch * I.drawHeight / I.drawWidth
        I.drawWidth = 2 * inch
        I.hAlign = 'LEFT'
        I.vAlign = 'TOP'
        invoice.append(I)

        if preferences:
            pref_data = Paragraph("<font color='#014172'>"+preferences.company_name+"<br/>"+ preferences.address+"<br/>"+preferences.phone_no+" "+preferences.fax_no
                                  +"<br/>"+preferences.email+" "+preferences.url+"</font>", style_n)
            pref_data.hAlign = 'CENTER'
            pref_data.vAlign = 'TOP'
            invoice.append(pref_data)

        if client_obj:
            client_data = Paragraph("Client Name: " + client_obj.name+ '-('+client_obj.party_code+')', style_h2)
            client_data.hAlign = 'CENTER'
            client_data.vAlign = 'TOP'
            invoice.append(client_data)

        if s_date and e_date:
            s_date = parse(s_date)
            e_date = parse(e_date)
            date_data = Paragraph("Trips Report - from: " + str(s_date.date())+' To '+str(e_date.date()), style_h3)
            date_data.hAlign = 'CENTER'
            date_data.vAlign = 'TOP'
            invoice.append(date_data)
            invoice.append(d_line)
            invoice.append(Spacer(1, 0.5 * inch))

        data = []
        data.append(['Bin', 'Contract', 'Area', 'Contract Type', 'Skip Rate', 'Supervisor', 'Date Time', 'Verified'])
        data[1:] = [[x['bin'], x['contract_no'], x['location'], x['contract_type'], x['skip'], x['supervisor_name'], str(x['time']).split('.')[0], 'Yes' if x['verification'] is True else 'No'] for x in invoice_data]

        t = Table(data, style=[('GRID', (0, 0), (-1, -1), 1, colors.black),
                               ('FONTSIZE', (0, 0), (7, 0), 14),
                               ('FONTSIZE', (0, 0), (-1, -1), 10),
                               ('TEXTFONT', (0, 0), (7, 0), 'Times New Roman Bold'),
                               ('BACKGROUND', (0, 0), (7, 0), colors.lightgrey),
                               ('BOX', (0, 0), (-1, -1), 2, colors.black),
                               ('BOX', (0, 0), (7, 0), 2, colors.black),
                               ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                               ])
        t.hAlign = 'LEFT'
        invoice.append(t)
        doc.build(invoice, onFirstPage=self.myPage, onLaterPages=self.myPage)

    def get_trips_data(self, customer, client, contracts, s_date, e_date, s_id):
        trips_qset = get_clients_invoice(client=client, customer=customer, start_datetime=s_date, end_datetime=e_date, contracts=contracts, status=s_id)

        trips_qset = trips_qset.values(verification=F('verified'), contract_no=F('contract__name'), client_name=F('client__party_code'), location=F('area__name'),
        bin=F('action_item__name'), supervisor_name=F('supervisor__name'),  skip=F('contract__skip_rate'), time=F('timestamp'), contract_type=F('contract__leased_owned__label'))
        return trips_qset

    def get(self, request, format=None):

        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}

        customer = get_customer_from_request(request, None)
        client = get_default_param(request,'client',None)
        contracts_list = get_list_param(request,'contracts',None)
        s_date = get_default_param(request,'start_datetime',None)
        e_date = get_default_param(request,'end_datetime',None)

        now = datetime.now()
        dirc = os.makedirs(settings.MEDIA_ROOT + "/reports/", exist_ok=True)
        file_name = str(now.date()) + "-Trip-Report"
        # s_date = now - timedelta(days=30)
        # e_date = now + timedelta(days=30)

        # FIXME Testing
        # client = 2589

        try:
            client_obj = CustomerClients.objects.get(pk=client)
        except CustomerClients.DoesNotExist:
            client_obj = None

        try:
            preferences = CustomerPreferences.objects.get(customer_id=customer)

        except CustomerClients.DoesNotExist:
            preferences = None

        if client_obj:
            invoice = self.get_trips_data(customer=customer, client=client, contracts=contracts_list,
                    s_date=s_date, e_date=e_date, s_id=[IOFOptionsEnum.WASTE_COLLECTED,IOFOptionsEnum.BIN_PICKED_UP, IOFOptionsEnum.DROPOFF_BIN])
            # if dirc:
            self._create_pdf_trips("media/reports/"+file_name + ".pdf", invoice, client_obj, s_date, e_date, preferences)

            file_url = (request.get_host()+"/media/reports/"+file_name + ".pdf")
            # print(os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name+".pdf"))
            response_body[RESPONSE_DATA] = {'file':file_url}
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            response_body[RESPONSE_MESSAGE] = "Report generated successfully"
        else:
            response_body[RESPONSE_DATA] = {'file': None}
            response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
            response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING

        return generic_response(response_body=response_body, http_status=HTTP_SUCCESS_CODE)
