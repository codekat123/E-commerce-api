from rest_framework.generics import ListAPIView,CreateAPIView,UpdateAPIView
from product.models import Product
from product.serializers import ProductSerializer
from product.permissions import IsMerchant
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from order.models import OrderItem
from .serializers import DateSerializer
from django.http import HttpResponse
import csv
# PDF imports
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.utils import timezone



class BaseMerchantProductsView(ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsMerchant]
    throttle_classes = [UserRateThrottle]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    related_field = None  

    def get_queryset(self):
        merchant = self.request.user.merchant_profile
        if not self.related_field:
            raise ValueError("You must define 'related_field' in the subclass.")
        filter_kwargs = {
            "merchant": merchant,
            f"{self.related_field}__isnull": False
        }
        return Product.objects.filter(**filter_kwargs).distinct()


class MerchantOrderedProductsView(BaseMerchantProductsView):
    related_field = "order_item"


class MerchantPaidProductsView(BaseMerchantProductsView):
    related_field = "order_payment"

class MerchantCreateProductsView(CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsMerchant]
    throttle_classes = [UserRateThrottle]



class MerchantUpdateProductsView(UpdateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsMerchant]
    throttle_classes = [UserRateThrottle]
    lookup_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(merchant=self.request.user.merchant_profile)



class MerchantChartDataView(APIView):
    permission_classes = [IsAuthenticated,IsMerchant]

    def get(self, request):
        merchant = request.user.merchant_profile
        data = (
            OrderItem.objects
            .filter(product__merchant=merchant)
            .values('order__created_at__date')
            .annotate(total_sales=Sum('price'))
            .order_by('order__created_at__date')
        )
        labels = [item['order__created_at__date'] for item in data]
        values = [item['total_sales'] for item in data]
        return Response({'labels': labels, 'values': values})






class GenerateReport(APIView):
    permission_classes = [IsAuthenticated, IsMerchant]

    def post(self, request, format=None, *args, **kwargs):
        report_type = kwargs.get("report_type", "csv")  # "csv" or "pdf"

        # Validate input dates
        serializer = DateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        start_date = serializer.validated_data['date_from']
        end_date = serializer.validated_data['date_to']

        merchant = request.user.merchant_profile
        paid_products = (
            OrderItem.objects
            .filter(
                product__merchant=merchant,
                order__created_at__range=(start_date, end_date),
                order__paid=True
            )
            .select_related('product', 'order')
        )

        if report_type == "csv":
            return self.generate_csv(paid_products)
        elif report_type == "pdf":
            return self.generate_pdf(paid_products, merchant, start_date, end_date)
        else:
            return HttpResponse("Invalid report type.", status=400)

    def generate_csv(self, paid_products):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="sales_report.csv"'
        writer = csv.writer(response)

        writer.writerow([
            "First Name", "Last Name", "Email", "City",
            "Product", "Quantity", "Unit Price", "Total Price", "Order Date"
        ])

        for item in paid_products:
            writer.writerow([
                item.order.first_name,
                item.order.last_name,
                item.order.email,
                item.order.city,
                item.product.name,
                item.quantity,
                item.price,
                float(item.price) * item.quantity,
                item.order.created_at.strftime("%Y-%m-%d"),
            ])
        return response

    def generate_pdf(self, paid_products, merchant, start_date, end_date):
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="sales_report.pdf"'

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        y = height - 50

        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, f"Sales Report for {merchant.user.username}")
        p.setFont("Helvetica", 10)
        y -= 20
        p.drawString(50, y, f"Period: {start_date} to {end_date}")
        y -= 30

        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, "Customer")
        p.drawString(200, y, "Product")
        p.drawString(350, y, "Total Price")
        y -= 15
        p.setFont("Helvetica", 10)

        for item in paid_products:
            if y < 50:  # add new page if full
                p.showPage()
                y = height - 50
            total_price = float(item.price) * item.quantity
            p.drawString(50, y, f"{item.order.first_name} {item.order.last_name}")
            p.drawString(200, y, item.product.name)
            p.drawString(350, y, f"{total_price:.2f}")
            y -= 15

        p.showPage()
        p.save()
        return response

 