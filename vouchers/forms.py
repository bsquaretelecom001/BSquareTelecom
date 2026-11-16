import csv
import io

from django import forms

from plans.models import InternetPlan
from .models import VoucherInventory


class VoucherInventoryImportForm(forms.Form):

    plan = forms.ModelChoiceField(
        queryset=InternetPlan.objects.filter(active=True),
        label="Internet Plan",
    )

    csv_file = forms.FileField(
        label="Omada Voucher CSV",
        help_text="Upload a CSV containing your Omada voucher codes.",
    )

    def clean_csv_file(self):
        uploaded_file = self.cleaned_data["csv_file"]

        if not uploaded_file.name.lower().endswith(".csv"):
            raise forms.ValidationError(
                "Please upload a CSV file."
            )

        try:
            content = uploaded_file.read().decode("utf-8-sig")
            rows = list(csv.reader(io.StringIO(content)))
        except (UnicodeDecodeError, csv.Error):
            raise forms.ValidationError(
                "The CSV file could not be read. Please check its format."
            )

        codes = []

        for row in rows:
            if not row:
                continue

            code = row[0].strip()

            if code.lower() in ("voucher_code", "code", "voucher"):
                continue

            if code:
                codes.append(code)

        if not codes:
            raise forms.ValidationError(
                "No voucher codes were found in this CSV."
            )

        if len(codes) != len(set(codes)):
            raise forms.ValidationError(
                "This CSV contains duplicate voucher codes."
            )

        existing_codes = set(
            VoucherInventory.objects.filter(
                voucher_code__in=codes
            ).values_list("voucher_code", flat=True)
        )

        if existing_codes:
            raise forms.ValidationError(
                "Some voucher codes already exist in your inventory: "
                + ", ".join(list(existing_codes)[:10])
            )

        return codes