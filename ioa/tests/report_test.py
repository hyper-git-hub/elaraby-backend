from iof.generic_utils import get_generic_fillups

__author__ = 'SyedUsman'
__version__ = '1.0'

from datetime import datetime, timedelta
import os, urllib.request
import traceback, socket
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
from django.db.models import Avg

from backend import settings
from customer.models import CustomerPreferences, CustomerClients
from hypernet.constants import RESPONSE_MESSAGE, RESPONSE_STATUS, HTTP_SUCCESS_CODE, RESPONSE_DATA, HTTP_ERROR_CODE, \
    TEXT_PARAMS_MISSING
from hypernet.enums import IOFOptionsEnum
from iof.utils import get_clients_invoice
from hypernet.models import Entity, HypernetPostData, InvoiceData
from rest_framework.decorators import api_view, APIView, permission_classes
from hypernet.utils import *
from hypernet.constants import *


style_b = getSampleStyleSheet()
page_info = " Hypernymbiz L.L.C\u00AE"
page_info += " NOTE: This report is system generated and All times are in UTC"

data_folder = Path(settings.STATIC_ROOT + "report_images/")

#FIXME Hypernet logo not working on Production Machine {Unidentified Error}
# image_hypernym = data_folder / "logo-hypernym.png"
# I_hyper = Image(image_hypernym)
# # I = Image(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media/zenath_imgs/zenath_logo.jpg'))
# I_hyper.drawHeight = 0.8 * inch * I_hyper.drawHeight / I_hyper.drawWidth
# I_hyper.drawWidth = 0.8 * inch
# I_hyper.hAlign = 'LEFT'
# I_hyper.vAlign = 'BOTTOM'


class ReportViewInvoice(APIView):

    def myPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, page_info))
        # canvas.drawImage(image_hypernym, x=(720), y=(50), anchor='c', width=60, height=40)
        canvas.restoreState()

    def _create_pdf_invoice(self, fileserver, filename, invoice_data, client_obj, s_date, e_date, preferences):
        try:
            absolute_filename = settings.BASE_DIR + '/' + filename
            current_tz = timezone.now()
            rand_number = str(preferences.invoice_number + 1) + str(current_tz.date().strftime('%d%m%Y'))
            style_h1 = style_b["Heading1"]
            style_h2 = style_b["Heading2"]
            style_h3 = style_b["Heading3"]
            style_n = style_b["Normal"]
    
            style_h4 = style_b["Heading4"]
            style_h4.WordWrap = 'CJK'
    
            text_wraping = style_b["BodyText"]
            text_wraping.WordWrap = 'CJK'
    
            style_para = ParagraphStyle('parrafos',
                               alignment=TA_JUSTIFY,
                               fontSize=13,
                               fontName="Times-Roman")
    
            d_line = Drawing(100, 1)
            d_line.add(Line(0, 0, 280, 0))
    
            doc = SimpleDocTemplate(absolute_filename, pagesize=portrait(A3), rightMargin=45, leftMargin=45, topMargin=50)
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
                
                c_name = "Company Name: <b>"+preferences.company_name+"</b><br/>" if preferences.company_name else ""
                address = "Address: <b>"+preferences.address+"</b><br/>" if preferences.address else ""
                p_no = "Phone No: <b>"+preferences.phone_no+"</b>" if preferences.phone_no else ""
                f_no = "Fax No: <b>"+preferences.fax_no+"</b>" if preferences.fax_no else ""
                email = "Email: <b>"+preferences.email+"</b><br/>" if preferences.email else ""
                website = "Website: <b>"+preferences.url+"</b>" if preferences.url else ""
                
                pref_data = Paragraph("<font color='#014172'>"+
                                      c_name+
                                      address+
                                      p_no+
                                      f_no+
                                      email+
                                      website+"</font>"
                                      , style_h4)
                pref_data.hAlign = 'CENTER'
                pref_data.vAlign = 'TOP'
                invoice.append(pref_data)
    
            if client_obj and (s_date and e_date):
                #FIXME {Comment it, if using postman,}
                s_date = parse(s_date)
                e_date = parse(e_date)
    
                client_name = Paragraph(client_obj.name, style_h4)
                client_party_code = Paragraph(client_obj.party_code, style_h4)
                left_pl_holder = [['Name: ', client_name], ['Party Code: ', client_party_code]]
                if client_obj.contact_number:
                    client_phone_no = Paragraph(client_obj.contact_number, style_h4)
                    left_pl_holder.append(['Phone No: ', client_phone_no])
    
                lt = Table(left_pl_holder, style=[('FONTSIZE', (0, 0), (-1, -1), 11),])
                lt.hAlign = 'LEFT'
                lt._argW[0] = 1.0 * inch
    
    
                client_detail_row = Paragraph("Client Details", style_h3)
                tax_invoice_text = Paragraph("Tax Invoice", style_h3)
    
                right_pl_holder = [['Date: ', str(current_tz.date())], ['Service Type: ' ,'SST'], ['Minimum Trips: ', '-']]
                t = Table(right_pl_holder, style=[('FONTSIZE', (0, 0), (-1, -1), 11),])
                t.hAlign = 'LEFT'
    
                empty = Paragraph("<br/> ", style_h3)
                top_table_data = [[client_detail_row, lt],[tax_invoice_text, t]]
                top_table = KeepTogether(Table([top_table_data], style=[('GRID', (0, 0), (-1, -1), 1, colors.black),
                                                           ('BOX', (0, 0),(-1, -1), 2, colors.black),
                                                            ('FONTSIZE', (0, 0), (-1, -1), 11.5),]))
    
                top_table.hAlign = 'LEFT'
                inv_number = Paragraph("Invoice No. : "+rand_number, style_h4)
                invoice.append(Spacer(1,0.2*inch))
                invoice.append(inv_number)
                invoice.append(Spacer(1, 0.1 * inch))
                invoice.append(top_table)
                invoice.append(Spacer(1,0.1*inch))
    
            particulars = Paragraph("<b>Particulars</b><br/>"+"CHARGES TOWARDS SKIP SERVICE FOR THE DURATION OF "+str(s_date.date())+' To '+str(e_date.date()), style_n)
            part = [particulars]
            part_table = Table([part], style=[('GRID', (0, 0), (-1, -1), 1, colors.black),
                                              ('BOX', (0, 0),(-1, -1), 2, colors.black)])
            part_table.hAlign = 'LEFT'
            invoice.append(part_table)
            invoice.append(Spacer(1, 0.1 * inch))
    
            data = []
            data.append(['Contract#', 'Location', 'Contract Type', 'Trips'+'/'+'Skip Rate', 'Net(AED)', 'VAT', 'Total(AED)'])
            data[1:] = [[x['contract_no'], Paragraph(x['location'] if x['location'] else "No Location", text_wraping), str(x['contract_type']).title(),
            (str(x['trips'])+" @ "+str(x['skip'])), x['net_amount'], str(x['vat'])+"%  "+str(x['vat_per']), x['after_tax']] for x in invoice_data]
    
            total_amount_bt = sum(item['net_amount'] for item in invoice_data)
            total_invoice = sum(item['after_tax'] for item in invoice_data)
    
            inv_table = (Table(data, style=[('GRID', (0, 0), (-1, -1), 1, colors.black),
                                   ('FONTSIZE', (0, 0), (6, 0), 16),
                                   ('FONTSIZE', (0, 0), (-1, -1), 13),
                                   # ('FONTSIZE', (0, 1), (1, 0), 11),
                                   ('FONTSIZE', (1, 1), (1,-1), 10),
                                   ('TEXTFONT', (0, 0), (6, 0), 'Times New Roman Bold'),
                                   ('BACKGROUND', (0, 0), (6, 0), colors.lightgrey),
                                   ('BOX', (0, 0), (-1, -1), 2, colors.black),
                                   ('BOX', (0, 0), (6, 0), 2, colors.black),
                                   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                   ('VALIGN', (3, 1), (3, -1), 'MIDDLE'),
                                   ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
                                   ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
                                   ('ALIGN', (6, 0), (6, -1), 'RIGHT'),
                                   ], rowHeights=0.4*inch))
    
            inv_table.hAlign = 'LEFT'
            inv_table._argW[1] = 3.09 * inch
            inv_table._argW[0] = 1.0 * inch
            inv_table._argW[3] = 1.4 * inch
            inv_table._argW[5] = 1.5 * inch
    
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
                                   ('BOX', (0, 0), (0, 2), 2, colors.black),
                                   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                   ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                                    ], rowHeights=0.4*inch))
    
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
            preferences.invoice_number += 1
            preferences.save()
            try:
                invoice_data = InvoiceData()
                invoice_data.invoice_number = rand_number
                invoice_data.customer = preferences.customer
                #FIXME: hard coded module to be replaces somehow.
                invoice_data.module_id = 1
                invoice_data.total_sum = total_invoice
                invoice_data.client = client_obj
                invoice_data.start_datetime = s_date
                invoice_data.end_datetime = e_date
                invoice_data.invoice_path = fileserver + "/" + filename
                invoice_data.save()
            except:
                traceback.print_exc()
            doc.build(invoice, onFirstPage=self.myPage, onLaterPages=self.myPage)
        except:
            traceback.print_exc()

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
                                               skip=F('contract__skip_rate'), contract_no=F('contract__name'),

                                               vat_per=ExpressionWrapper((F('invoice_sum') * Value(preferences.value_added_tax,
                                                       output_field=FloatField())) / 100,
                                                                       output_field=FloatField())
                                               )

            return invoice_qset

        except:
            print("REPORT QUERY ERROR: \n"+traceback.print_exc())


    def get(self, request, format=None):

        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}

        customer = get_customer_from_request(request, None)
        client = get_default_param(request,'client',None)
        contracts_list = get_list_param(request,'contracts',None)
        s_date = get_default_param(request,'start_datetime', '2018-07-21 00:00')
        e_date = get_default_param(request,'end_datetime', '2018-07-25 00:00')
        generate = get_default_param(request,'generate', 0)

        file_url = urllib.request.urlopen('https://ident.me').read().decode('utf8')

        #FIXME {Un-Comment it if using postman,}
        # client = 1875
        # s_date = now - timedelta(days=10)
        # e_date = now + timedelta(days=10)
        # contracts_list = [8412]

        # try:
        #     client_obj = CustomerClients.objects.get(pk=client)
        # except CustomerClients.DoesNotExist:
        #     client_obj = None
        #
        # try:
        #     preferences = CustomerPreferences.objects.get(customer_id=customer)
        # except CustomerClients.DoesNotExist:
        #     preferences = None
        #
        # if client_obj:
        #     invoice = self.get_invoice_data(customer=customer, client=client, contracts=contracts_list,
        #                     s_date=s_date, e_date=e_date, s_id=[IOFOptionsEnum.WASTE_COLLECTED, IOFOptionsEnum.BIN_PICKED_UP])
        #
        #     name = s_date.split(' ')[0]+'-'+e_date.split(' ')[0]+'-'+str(client_obj.name)+ "-Invoice-Report"
        #     file_with_loc = "media/reports/"+name+".pdf"
        #     file_found = os.path.exists("media/reports/"+name+".pdf")
        #
        #     if file_found:
        #         if generate:
        #             os.remove("media/reports/" + name + ".pdf")
        #         elif generate is 0:
        #             file_url += "/" + file_with_loc
        #     else:
        #         self._create_pdf_invoice(file_with_loc, invoice, client_obj, s_date, e_date, preferences)
        #         file_url += "/" + file_with_loc
        #
        #     if file_url:
        #         response_body[RESPONSE_DATA] = {'file':file_url}
        #         response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
        #         response_body[RESPONSE_MESSAGE] = "Report generated successfully"
        #
        # else:
        #     response_body[RESPONSE_DATA] = {'file': None}
        #     response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
        #     response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        response_body = self.get_report(client, customer, s_date, e_date, contracts_list, file_url, generate, response_body)

        return generic_response(response_body=response_body, http_status=HTTP_SUCCESS_CODE)

    def get_report(self, client, customer, s_date, e_date, contracts_list, file_url, generate, response_body):
        try:
            print('get_report function entered')
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
                                                s_date=s_date, e_date=e_date,
                                                s_id=[IOFOptionsEnum.WASTE_COLLECTED, IOFOptionsEnum.BIN_PICKED_UP])
            
                name = s_date.split(' ')[0] + '-' + e_date.split(' ')[0] + '-' + str(client_obj.name) + "-Invoice-Report"
                file_with_loc = "media/reports/" + name + ".pdf"
                file_found = os.path.exists("media/reports/" + name + ".pdf")
            
                if file_found:
                    if generate:
                        os.remove("media/reports/" + name + ".pdf")
                    elif generate is 0:
                        file_url += "/" + file_with_loc
                else:
                    self._create_pdf_invoice(file_url, file_with_loc, invoice, client_obj, s_date, e_date, preferences)
                    file_url += "/" + file_with_loc
            
                if file_url:
                    response_body[RESPONSE_DATA] = {'file': file_url}
                    response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                    response_body[RESPONSE_MESSAGE] = "Report generated successfully"
        
            else:
                response_body[RESPONSE_DATA] = {'file': None}
                response_body[RESPONSE_STATUS] = HTTP_ERROR_CODE
                response_body[RESPONSE_MESSAGE] = TEXT_PARAMS_MISSING
        except:
            traceback.print_exc()
    
        return response_body

class ReportViewTripSheet(APIView):

    def myPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, page_info))
        # canvas.drawImage(image_hypernym, x=(720), y=(50), anchor='se', width=60, height=40)
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


        c_name = "Company Name: <b>" + preferences.company_name + "</b><br/>" if preferences.company_name else ""
        address = "Address: <b>" + preferences.address + "</b><br/>" if preferences.address else ""
        p_no = "Phone No: <b>" + preferences.phone_no + "</b>" if preferences.phone_no else ""
        f_no = "Fax No: <b>" + preferences.fax_no + "</b>" if preferences.fax_no else ""
        email = "Email: <b>" + preferences.email + "</b><br/>" if preferences.email else ""
        website = "Website: <b>" + preferences.url + "</b>" if preferences.url else ""
        
        if preferences:
            pref_data = Paragraph("<font color='#014172'>"+
                                  c_name+
                                  address+
                                  p_no+" "+f_no+
                                  email+" "+website+
                                  "</font>", style_n)
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

class ReportViewTrucks(APIView):
    def myPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, page_info))
        # canvas.drawImage(image_hypernym, x=(720), y=(50), anchor='c', width=60, height=40)
        canvas.restoreState()

    def _create_pdf_invoice(self, filename, data_ent, meta, cols, s_date, e_date, report_title, preferences, path=None):
        current_tz = timezone.get_current_timezone()
        import json
        import ast
        style_h1 = style_b["Heading1"]
        style_h2 = style_b["Heading2"]
        style_h3 = style_b["Heading3"]
        style_h4 = style_b["Heading4"]
        style_n = style_b["Normal"]

        d_line = Drawing(100, 1)
        d_line.add(Line(0, 0, 280, 0))

        if len(cols) <= 6:
            doc = SimpleDocTemplate(filename, pagesize=portrait(A4), rightMargin=50, leftMargin=45, topMargin=50)
        else:
            doc = SimpleDocTemplate(filename, pagesize=landscape(A4), rightMargin=50, leftMargin=45, topMargin=50)

        invoice = []  # Main List of items for PDF.

        data_folder = Path(settings.STATIC_ROOT + "report_images/")
        image_file = data_folder / "zenath_logo.jpg"

       # file_found = os.path.exists(str(image_file))
        #if file_found:
        #    print("Image exists")
        print(image_file)
        invoice_para = Paragraph(report_title, style_h2)
        invoice_para.hAlign = 'CENTER'
        invoice.append(invoice_para)
        invoice.append(Spacer(1, 0.5 * inch))
        styleSheet = style_b

        try:
            I = Image(image_file)
            # I = Image(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media/zenath_imgs/zenath_logo.jpg'))
            I.drawHeight = 2 * inch * I.drawHeight / I.drawWidth
            I.drawWidth = 2 * inch
            I.hAlign = 'LEFT'
            I.vAlign = 'TOP'
            invoice.append(I)
        except:
            traceback.print_exc()
        '''
        c_name = "Company Name: <b>" + preferences.company_name + "</b><br/>" if preferences.company_name else ""
        address = "Address: <b>" + preferences.address + "</b><br/>" if preferences.address else ""
        p_no = "Phone No: <b>" + preferences.phone_no + "</b>" if preferences.phone_no else ""
        f_no = "Fax No: <b>" + preferences.fax_no + "</b>" if preferences.fax_no else ""
        email = "Email: <b>" + preferences.email + "</b><br/>" if preferences.email else ""
        website = "Website: <b>" + preferences.url + "</b>" if preferences.url else ""

        if preferences:
            pref_data = Paragraph("<font color='#014172'>" +
                                  c_name +
                                  address +
                                  p_no + " " + f_no +
                                  email + " " + website +
                                  "</font>", style_n)
            pref_data.hAlign = 'CENTER'
            pref_data.vAlign = 'TOP'
            invoice.append(pref_data)
        '''
        #client_data = Paragraph("Client Name: " + client_obj.name + '-(' + client_obj.party_code + ')', style_h2)
        #client_data.hAlign = 'CENTER'
        #client_data.vAlign = 'TOP'
        #invoice.append(client_data)

        if s_date and e_date:
            s_date = parse(s_date)
            e_date = parse(e_date)
            date_data = Paragraph( report_title + " Report - from: " + str(s_date.date()) + ' To ' + str(e_date.date()), style_h3)
            date_data.hAlign = 'CENTER'
            date_data.vAlign = 'TOP'
            invoice.append(date_data)
            invoice.append(d_line)
            invoice.append(Spacer(1, 0.5 * inch))

        left_pl_holder = meta


        lt = Table(left_pl_holder, style=[('FONTSIZE', (0, 0), (-1, -1), 11), ])
        lt.hAlign = 'LEFT'
        lt._argW[0] = 2.0 * inch

        client_detail_row = Paragraph("Meta Information", style_h3)

        empty = Paragraph("<br/> ", style_h3)
        top_table_data = [[client_detail_row, lt]]
        top_table = KeepTogether(Table([top_table_data], style=[('GRID', (0, 0), (-1, -1), 1, colors.black),
                                                                ('FONTSIZE', (0, 0), (-1, -1), 11.5), ]))
        invoice.append(top_table)
        invoice.append(Spacer(1, 0.2 * inch))
        invoice.append(Spacer(1, 0.2 * inch))
        data = []
        data.append(cols)
        x = {}
        result = []

        report_data = Paragraph("Report Data: ", style_h3)

        invoice.append(report_data)
        invoice.append(Spacer(1, 0.2 * inch))
        #result = result.split(' ')
        inner_list = []

        for x in data_ent:
            inner_list=[]
            for i in cols:
                inner_list.append(x[i])
            result.append(inner_list)

        data[1:] = result
        cols_size = len(cols)-1
        t = Table(data, style=[('GRID', (0, 0), (-1, -1), 1, colors.black),
                               ('FONTSIZE', (0, 0), (cols_size, 0), 14),
                               ('FONTSIZE', (0, 0), (-1, -1), 10),
                               ('TEXTFONT', (0, 0), (cols_size, 0), 'Times New Roman Bold'),
                               ('BACKGROUND', (0, 0), (cols_size, 0), colors.lightgrey),
                               ('BOX', (0, 0), (-1, -1), 2, colors.black),
                               ('BOX', (0, 0), (cols_size, 0), 2, colors.black),
                               ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                               ])
        t.hAlign = 'LEFT'
        invoice.append(t)

        # invoice.append(Spacer(1, 0.2 * inch))
        # route = Paragraph("Route: ", style_h3)
        # invoice.append(Spacer(1, 0.2 * inch))
        # invoice.append(route)

        if path:
            data_folder = Path(settings.MEDIA_ROOT + "/avatars/")
            image_file = data_folder / path+'.jpg'

            I = Image(image_file)
            # I = Image(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media/zenath_imgs/zenath_logo.jpg'))
            I.drawHeight = 2 * inch * I.drawHeight / I.drawWidth
            I.drawWidth = 2 * inch
            I.hAlign = 'LEFT'
            I.vAlign = 'TOP'
            invoice.append(I)

        doc.build(invoice, onFirstPage=self.myPage, onLaterPages=self.myPage)

    def get_truck_data(self, customer, truck_id, s_date, e_date):
        import itertools
        from django.db.models.functions import TruncDate
        result = []
        try:
            preferences = CustomerPreferences.objects.get(customer_id=customer)
            post_data = HypernetPostData.objects.filter(timestamp__range=[s_date,e_date]).\
                annotate(date = TruncDate('timestamp')).values('date').annotate(d_t=Avg('distance_travelled'),v_l=Avg('volume_consumed'))

            print(post_data)
            return result
        except:
            traceback.print_exc()
            print("REPORT QUERY ERROR: \n" + traceback.print_exc())

    def get_report(self, customer, s_date, e_date, meta, data, cols, file_url, generate,report_title,
                                        response_body, path = None):
        try:
            preferences = CustomerPreferences.objects.get(customer_id=customer)
        except CustomerClients.DoesNotExist:
            preferences = None

        name = s_date.split(' ')[0] + '-' + e_date.split(' ')[0] + '-' + report_title +"-Report"
        file_with_loc = "media/reports/" + name + ".pdf"
        file_found = os.path.exists("media/reports/" + name + ".pdf")

        if file_found:
            #if generate:
            os.remove("media/reports/" + name + ".pdf")
            #elif generate is 0:
                #file_url += "/" + file_with_loc
        #else:
        self._create_pdf_invoice(file_with_loc, data, meta, cols, s_date, e_date, report_title, preferences, path)
        file_url += "/" + file_with_loc

        if file_url:
            response_body[RESPONSE_DATA] = {'file': file_url}
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            response_body[RESPONSE_MESSAGE] = "Report generated successfully"


        return response_body


    def parse_meta(self,meta):
        if meta:
            inner_list = []
            outer_list = []
            for k,v in meta.items():
                inner_list = []
                inner_list.append(k)
                inner_list.append(v)
                outer_list.append(inner_list)
            print(outer_list)
        return outer_list

    def check_image(self, img_url, s_date, e_date, img_title, generate):
        if img_url:
            name = s_date.split(' ')[0] + '-' + e_date.split(' ')[0] + '-' + img_title
            try:
                file_with_loc = "media/avatars/" + name
                file_found = os.path.exists("media/avatars/" + name + ".jpg")

                if file_found:
                    path = name
                else:
                    path = self.generate_image(s_date,e_date,img_title,img_url)
            except:
                traceback.print_exc()
            return name

    def generate_image(self,s_date,e_date, img_title,url):

        from PIL import Image
        from PIL import ImageDraw
        from urllib.request import urlretrieve

        img = Image.new('RGB', (500, 500))
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), "Sample Text", (255, 255, 255))

        try:
            #name = str(s_date) + '-' +  str(e_date)+ '-'  + img_title +'.jpg'
            name = s_date.split(' ')[0] + '-' + e_date.split(' ')[0] + '-' +img_title+'.jpg'
            #name='test.jpg'
            img.save('media/avatars/{}'.format(name))
        except:
            traceback.print_exc()
        #path = 'media/reports/{}'.format(name)

        path = 'media/avatars/{}'.format(name)
        urlretrieve(url,path)
        return name



    def post(self, request, format=None):
        import json
        import ast
        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}

        customer = get_customer_from_request(request, None)
        s_date = get_data_param(request, 'start_datetime', None)
        e_date = get_data_param(request, 'end_datetime', None)
        generate = get_data_param(request, 'generate', 0)
        img_url = get_data_param(request, 'url', None)


        file_url = request.get_host()
        print(file_url)
        report_title = get_data_param(request, 'report_title', None)
        meta = get_data_param(request, 'meta', None)
        cols = get_data_param(request, 'cols', None)
        data = get_data_param(request,'data',None)

        if meta:
            meta = ast.literal_eval(meta)
            result = self.parse_meta(meta)

            print(result)
        if data:
            data = eval(data)

        if img_url:
            path = self.check_image(img_url, s_date, e_date, report_title, generate)
        else:
            path = None
        response_body = self.get_report(customer, s_date, e_date, result, data,cols, file_url, generate,report_title,
                                    response_body, path)

        return generic_response(response_body=response_body, http_status=HTTP_SUCCESS_CODE)

class ReportViewActivities(APIView):
    def myPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, page_info))
        # canvas.drawImage(image_hypernym, x=(720), y=(50), anchor='c', width=60, height=40)
        canvas.restoreState()

    def _create_pdf_activities(self, filename, data_ent, meta, cols, s_date, e_date, report_title, preferences, path=None,
                               assets_col=None, assets_data=None):
        current_tz = timezone.get_current_timezone()
        import json
        import ast
        style_h1 = style_b["Heading1"]
        style_h2 = style_b["Heading2"]
        style_h3 = style_b["Heading3"]
        style_h4 = style_b["Heading4"]
        style_n = style_b["Normal"]

        d_line = Drawing(100, 1)
        d_line.add(Line(0, 0, 280, 0))

        doc = SimpleDocTemplate(filename, pagesize=landscape(A4), rightMargin=50, leftMargin=45, topMargin=50)

        invoice = []  # Main List of items for PDF.

        data_folder = Path(settings.STATIC_ROOT + "report_images/")

        if preferences.customer_id == 1: # Zenath logo in report
            image_file = data_folder / "zenath_logo.jpg"
        else:
            image_file = data_folder / "suez_logo.png"

        invoice_para = Paragraph(report_title, style_h2)
        invoice_para.hAlign = 'CENTER'
        invoice.append(invoice_para)
        invoice.append(Spacer(1, 0.5 * inch))
        styleSheet = style_b

        I = Image(image_file)
        # I = Image(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media/zenath_imgs/zenath_logo.jpg'))
        I.drawHeight = 3 * inch * I.drawHeight / I.drawWidth
        I.drawWidth = 3 * inch
        I.hAlign = 'LEFT'
        I.vAlign = 'TOP'
        invoice.append(I)

        '''
        c_name = "Company Name: <b>" + preferences.company_name + "</b><br/>" if preferences.company_name else ""
        address = "Address: <b>" + preferences.address + "</b><br/>" if preferences.address else ""
        p_no = "Phone No: <b>" + preferences.phone_no + "</b>" if preferences.phone_no else ""
        f_no = "Fax No: <b>" + preferences.fax_no + "</b>" if preferences.fax_no else ""
        email = "Email: <b>" + preferences.email + "</b><br/>" if preferences.email else ""
        website = "Website: <b>" + preferences.url + "</b>" if preferences.url else ""

        if preferences:
            pref_data = Paragraph("<font color='#014172'>" +
                                  c_name +
                                  address +
                                  p_no + " " + f_no +
                                  email + " " + website +
                                  "</font>", style_n)
            pref_data.hAlign = 'CENTER'
            pref_data.vAlign = 'TOP'
            invoice.append(pref_data)
        '''
        #client_data = Paragraph("Client Name: " + client_obj.name + '-(' + client_obj.party_code + ')', style_h2)
        #client_data.hAlign = 'CENTER'
        #client_data.vAlign = 'TOP'
        #invoice.append(client_data)

        if s_date and e_date:
            s_date = parse(s_date)
            e_date = parse(e_date)
            date_data = Paragraph(report_title, style_h3)
            date_data.hAlign = 'CENTER'
            date_data.vAlign = 'TOP'
            invoice.append(date_data)
            invoice.append(d_line)
            invoice.append(Spacer(1, 0.5 * inch))

        left_pl_holder = meta


        lt = Table(left_pl_holder, style=[('FONTSIZE', (0, 0), (-1, -1), 11),])
        lt.hAlign = 'LEFT'
        lt._argW[0] = 2.0 * inch
        lt._argW[1] = 2.0 * inch
        client_detail_row = Paragraph("Meta Information", style_h3)

        empty = Paragraph("<br/> ", style_h3)
        top_table_data = [[client_detail_row, lt]]
        top_table = KeepTogether(Table([top_table_data], style=[('GRID', (0, 0), (-1, -1), 1, colors.black),
                                                                ('FONTSIZE', (0, 0), (-1, -1), 11.5), ]))
        invoice.append(top_table)

        #invoice.append(top_table)
        invoice.append(Spacer(2, 0.2 * inch))
        invoice.append(Spacer(1, 0.2 * inch))

        route = Paragraph("Route: ", style_h3)
        invoice.append(Spacer(1, 0.6 * inch))

        invoice.append(route)

        if path:
            path = path + '.jpg'
            data_folder = Path(settings.MEDIA_ROOT + "/avatars/")
            image_file = data_folder / path

            I = Image(image_file)
            # I = Image(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media/zenath_imgs/zenath_logo.jpg'))
            I.drawHeight = 5.5 * inch * I.drawHeight / I.drawWidth
            I.drawWidth = 6.0 * inch
            I.hAlign = 'CENTER'
            I.vAlign = 'TOP'
            invoice.append(I)

        invoice.append(Spacer(1, 0.2 * inch))
        invoice.append(Spacer(1, 0.2 * inch))

        if assets_col and assets_data:
            a_data = []
            a_data.append(assets_col)
            x = {}
            assets_result = []

            assets_heading = Paragraph("Asset Details: ", style_h3)

            invoice.append(assets_heading)
            invoice.append(Spacer(1, 0.2 * inch))
            # result = result.split(' ')

            for a in assets_data:
                assets_inner_list = []
                for c in assets_col:
                    assets_inner_list.append(a[c])
                assets_result.append(assets_inner_list)

            a_data[1:] = assets_result
            cols_size = len(assets_col) - 1
            a_t = Table(a_data, style=[('GRID', (0, 0), (-1, -1), 1, colors.black),
                                   ('FONTSIZE', (0, 0), (cols_size, 0), 14),
                                   ('FONTSIZE', (0, 0), (-1, -1), 10),
                                   ('TEXTFONT', (0, 0), (cols_size, 0), 'Times New Roman Bold'),
                                   ('BACKGROUND', (0, 0), (cols_size, 0), colors.lightgrey),
                                   ('BOX', (0, 0), (-1, -1), 2, colors.black),
                                   ('BOX', (0, 0), (cols_size, 0), 2, colors.black),
                                   ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                   ])
            a_t.hAlign = 'LEFT'
            invoice.append(a_t)

            invoice.append(Spacer(1, 0.2 * inch))


        data = []
        data.append(cols)
        x = {}
        result = []

        report_data = Paragraph("Activity Details: ", style_h3)

        invoice.append(report_data)
        invoice.append(Spacer(1, 0.2 * inch))
        #result = result.split(' ')
        #inner_list = []

        for x in data_ent:
            inner_list=[]
            for i in cols:
                inner_list.append(x[i])
            result.append(inner_list)

        data[1:] = result
        cols_size = len(cols)-1
        t = Table(data, style=[('GRID', (0, 0), (-1, -1), 1, colors.black),
                               ('FONTSIZE', (0, 0), (cols_size, 0), 14),
                               ('FONTSIZE', (0, 0), (-1, -1), 10),
                               ('TEXTFONT', (0, 0), (cols_size, 0), 'Times New Roman Bold'),
                               ('BACKGROUND', (0, 0), (cols_size, 0), colors.lightgrey),
                               ('BOX', (0, 0), (-1, -1), 2, colors.black),
                               ('BOX', (0, 0), (cols_size, 0), 2, colors.black),
                               ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                               ])
        t.hAlign = 'LEFT'
        invoice.append(t)

        invoice.append(Spacer(1, 0.2 * inch))

        doc.build(invoice, onFirstPage=self.myPage, onLaterPages=self.myPage)

    def get_truck_data(self, customer, truck_id, s_date, e_date):
        import itertools
        from django.db.models.functions import TruncDate
        result = []
        try:
            preferences = CustomerPreferences.objects.get(customer_id=customer)
            post_data = HypernetPostData.objects.filter(timestamp__range=[s_date,e_date]).\
                annotate(date = TruncDate('timestamp')).values('date').annotate(d_t=Avg('distance_travelled'),v_l=Avg('volume_consumed'))

            print(post_data)
            return result
        except:
            traceback.print_exc()
            print("REPORT QUERY ERROR: \n" + traceback.print_exc())

    def get_report(self, customer, s_date, e_date, meta, data, cols, file_url, generate,report_title,
                                        response_body, assets_col, assets_data, path = None):
        try:
            preferences = CustomerPreferences.objects.get(customer_id=customer)
        except CustomerClients.DoesNotExist:
            preferences = None

        name = s_date.split(' ')[0] + '-' + e_date.split(' ')[0] + '-' + report_title +"-Report"
        file_with_loc = "media/reports/" + name + ".pdf"
        file_found = os.path.exists("media/reports/" + name + ".pdf")

        if file_found:
            #if generate:
            os.remove("media/reports/" + name + ".pdf")
            #elif generate is 0:
                #file_url += "/" + file_with_loc
        #else:
        self._create_pdf_activities(file_with_loc, data, meta, cols, s_date, e_date, report_title, preferences, path, assets_col, assets_data)
        file_url += "/" + file_with_loc
        if file_url:
            response_body[RESPONSE_DATA] = {'file': file_url}
            response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
            response_body[RESPONSE_MESSAGE] = "Report generated successfully"


        return response_body


    def parse_meta(self,meta):
        if meta:
            inner_list = []
            outer_list = []
            for k,v in meta.items():
                inner_list = []
                inner_list.append(k)
                inner_list.append(v)
                outer_list.append(inner_list)
            print(outer_list)
        return outer_list

    def check_image(self, img_url, s_date, e_date, img_title, generate):
        if img_url:
            name = s_date.split(' ')[0] + '-' + e_date.split(' ')[0] + '-' + img_title

            file_with_loc = "media/avatars/" + name
            file_found = os.path.exists("media/avatars/" + name + ".jpg")

            if file_found is False:
                self.generate_image(s_date,e_date,img_title,img_url)

            return name

    def generate_image(self,s_date,e_date, img_title,url):

        from PIL import Image
        from PIL import ImageDraw
        from urllib.request import urlretrieve

        img = Image.new('RGB', (1300, 1000))
        draw = ImageDraw.Draw(img)
        #draw.text((0, 0), "Sample Text", (255, 255, 255))

        try:
            #name = str(s_date) + '-' +  str(e_date)+ '-'  + img_title +'.jpg'
            name = s_date.split(' ')[0] + '-' + e_date.split(' ')[0] + '-' +img_title+'.jpg'
            #name='test.jpg'
            img.save('media/avatars/{}'.format(name))
        except:
            traceback.print_exc()
        #path = 'media/reports/{}'.format(name)

        path = 'media/avatars/{}'.format(name)
        urlretrieve(url,path)
        return None



    def post(self, request, format=None):
        import json
        import ast
        response_body = {RESPONSE_MESSAGE: "", RESPONSE_STATUS: HTTP_SUCCESS_CODE, RESPONSE_DATA: {}}

        customer = get_customer_from_request(request, None)
        client = get_default_param(request, 'client', None)
        contracts_list = get_list_param(request, 'contracts', None)
        #s_date = get_default_param(request, 'start_datetime', None)
        #e_date = get_default_param(request, 'end_datetime', None)
        s_date = get_data_param(request,'start_datetime', '2018-07-21 00:00')
        e_date = get_data_param(request,'end_datetime', '2018-07-25 00:00')
        generate = get_data_param(request, 'generate', 0)
        img_url = get_data_param(request, 'url', None)


        #file_url = urllib.request.urlopen('https://ident.me').read().decode('utf8')
        file_url = request.get_host()
        print(file_url)
        report_title = get_data_param(request, 'report_title', None)
        meta = get_data_param(request, 'meta', None)
        cols = get_data_param(request, 'cols', None)
        data = get_data_param(request,'data',None)

        assets_col = get_data_param(request, 'assets_cols', None)
        assets_data = get_data_param(request, 'assets_data', None)
        #path = get_default_param(request,'path',None)

        if meta:
            meta = ast.literal_eval(meta)
            result = self.parse_meta(meta)

            print(result)
        if data:
            data = eval(data)

        if assets_data:
            assets_data = eval(assets_data)

        if img_url:
            path = self.check_image(img_url, s_date, e_date, report_title, generate)
        else:
            path = None
        response_body = self.get_report(customer, s_date, e_date, result, data,cols, file_url, generate,report_title,
                                    response_body, assets_col, assets_data, path)

        return generic_response(response_body=response_body, http_status=HTTP_SUCCESS_CODE)

class ReportViewGeneric(APIView):
    def myPage(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, page_info))
        # canvas.drawImage(image_hypernym, x=(720), y=(50), anchor='c', width=60, height=40)
        canvas.restoreState()

    def _create_pdf_generic(self, fileserver, filename, s_date, e_date, heading, data, report_title, table_cols = None, table_data = None):
        try:
            absolute_filename = settings.BASE_DIR + '/' + filename
            current_tz = timezone.now()
            style_h1 = style_b["Heading1"]
            style_h2 = style_b["Heading2"]
            style_h3 = style_b["Heading3"]
            style_n = style_b["Normal"]

            style_h4 = style_b["Heading4"]
            style_h4.WordWrap = 'CJK'

            text_wraping = style_b["BodyText"]
            text_wraping.WordWrap = 'CJK'

            style_para = ParagraphStyle('parrafos',
                                        alignment=TA_JUSTIFY,
                                        fontSize=13,
                                        fontName="Times-Roman")

            d_line = Drawing(100, 1)
            d_line.add(Line(0, 0, 280, 0))

            doc = SimpleDocTemplate(absolute_filename, pagesize=portrait(A3), rightMargin=45, leftMargin=45,
                                    topMargin=50)
            invoice = []  # Main List of items for PDF.

            image_zenath = data_folder / "zenath_logo.jpg"

            invoice_para = Paragraph(heading, style_h2)
            invoice_para.hAlign = 'CENTER'
            invoice.append(invoice_para)
            invoice.append(Spacer(1, 0.5 * inch))

            I = Image(image_zenath)
            I.drawHeight = 2 * inch * I.drawHeight / I.drawWidth
            I.drawWidth = 2 * inch
            I.hAlign = 'LEFT'
            I.vAlign = 'TOP'
            invoice.append(I)

            if s_date and e_date:
                s_date = parse(s_date)
                e_date = parse(e_date)
                date_data = Paragraph(
                    report_title + " Report - from: " + str(s_date.date()) + ' To ' + str(e_date.date()), style_h3)
                date_data.hAlign = 'CENTER'
                date_data.vAlign = 'TOP'
                invoice.append(date_data)
                invoice.append(d_line)
                invoice.append(Spacer(1, 0.5 * inch))

            try:
                if data:
                    if len(data) == 0:
                        para = Paragraph(
                            "No data to display from: " + str(s_date.date()) + ' To ' + str(e_date.date()), style_h3)
                    else:
                        for i in data:
                            para = Paragraph(i, style_h3)
                            invoice.append(para)

                else:
                    if table_cols and table_data:
                        data = []
                        data.append(table_cols)
                        x = {}
                        result = []
                        invoice.append(Spacer(1, 0.2 * inch))
                        # result = result.split(' ')
                        inner_list = []

                        for x in table_data:
                            print(x)
                            inner_list = []
                            for i in table_cols:
                                inner_list.append(x[i])
                            result.append(inner_list)

                        data[1:] = result
                        cols_size = len(table_cols) - 1
                        t = Table(data, style=[('GRID', (0, 0), (-1, -1), 1, colors.black),
                                               ('FONTSIZE', (0, 0), (cols_size, 0), 14),
                                               ('FONTSIZE', (0, 0), (-1, -1), 10),
                                               ('TEXTFONT', (0, 0), (cols_size, 0), 'Times New Roman Bold'),
                                               ('BACKGROUND', (0, 0), (cols_size, 0), colors.lightgrey),
                                               ('BOX', (0, 0), (-1, -1), 2, colors.black),
                                               ('BOX', (0, 0), (cols_size, 0), 2, colors.black),
                                               ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                               ])
                        t.hAlign = 'LEFT'
                        invoice.append(t)
                invoice.append(Spacer(1, 0.5 * inch))

            except:
                traceback.print_exc()
            doc.build(invoice, onFirstPage=self.myPage, onLaterPages=self.myPage)
        except:
            traceback.print_exc()

    def get_report(self,s_date, e_date, file_url, generate, response_body, heading, data, report_title, table_cols=None, table_data=None):
        try:

            name = s_date.split(' ')[0] + '-' + e_date.split(' ')[0] + '-' + str(
                report_title)
            file_with_loc = "media/reports/" + name + ".pdf"
            file_found = os.path.exists("media/reports/" + name + ".pdf")

            if file_found:
                if generate:
                    os.remove("media/reports/" + name + ".pdf")
                elif generate is 0:
                    file_url += "/" + file_with_loc
            else:
                self._create_pdf_generic(file_url, file_with_loc, s_date, e_date, heading, data,report_title, table_cols,table_data)
                file_url += "/" + file_with_loc

            if file_url:
                response_body[RESPONSE_DATA] = {'file': file_url}
                response_body[RESPONSE_STATUS] = HTTP_SUCCESS_CODE
                response_body[RESPONSE_MESSAGE] = "Report generated successfully"
        except:
            traceback.print_exc()

        return response_body

