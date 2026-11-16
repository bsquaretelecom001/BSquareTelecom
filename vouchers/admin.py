from django.contrib import admin, messages
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.urls import path

from .models import Voucher, VoucherInventory
from .forms import VoucherInventoryImportForm
from .notifications import check_voucher_stock

@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):

    list_display = (
        "voucher_code",
        "customer",
        "plan_name",
        "data",
        "status",
        "device_limit",
        "expires_at",
    )

    search_fields = (
        "voucher_code",
        "customer__user__username",
    )

    list_filter = (
        "status",
    )


@admin.register(VoucherInventory)
class VoucherInventoryAdmin(admin.ModelAdmin):

    list_display = (
        "voucher_code",
        "plan",
        "status",
        "assigned_order",
        "imported_at",
        "issued_at",
    )

    search_fields = (
        "voucher_code",
        "plan__name",
    )

    list_filter = (
        "plan",
        "status",
    )

    readonly_fields = (
        "imported_at",
        "issued_at",
    )

    change_list_template = (
        "admin/vouchers/voucherinventory/change_list.html"
    )

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "import-csv/",
                self.admin_site.admin_view(self.import_csv),
                name="voucher-inventory-import",
            ),
        ]

        return custom_urls + urls

    def import_csv(self, request):

        if request.method == "POST":

            form = VoucherInventoryImportForm(
                request.POST,
                request.FILES,
            )

            if form.is_valid():

                plan = form.cleaned_data["plan"]
                codes = form.cleaned_data["csv_file"]

                try:
                    with transaction.atomic():

                        existing_codes = set(
                            VoucherInventory.objects.filter(
                                voucher_code__in=codes
                            ).values_list(
                                "voucher_code",
                                flat=True,
                            )
                        )

                        if existing_codes:
                            raise ValueError(
                                "Some voucher codes already exist: "
                                + ", ".join(
                                    list(existing_codes)[:10]
                                )
                            )

                        VoucherInventory.objects.bulk_create(
                            [
                                VoucherInventory(
                                    plan=plan,
                                    voucher_code=code,
                                )
                                for code in codes
                            ]
                        )

                    self.message_user(
                        request,
                        f"Successfully imported {len(codes)} "
                        f"vouchers for {plan.name}.",
                        messages.SUCCESS,
                    )
                    check_voucher_stock(plan)

                    return redirect(
                        "admin:vouchers_voucherinventory_changelist"
                    )

                except ValueError as e:
                    self.message_user(
                        request,
                        str(e),
                        messages.ERROR,
                    )

                except IntegrityError:
                    self.message_user(
                        request,
                        "Import failed. One or more voucher codes "
                        "already exist. No vouchers were imported.",
                        messages.ERROR,
                    )

        else:
            form = VoucherInventoryImportForm()

        context = {
            **self.admin_site.each_context(request),
            "form": form,
            "title": "Import Omada Voucher Codes",
            "opts": self.model._meta,
        }

        return render(
            request,
            "admin/vouchers/voucherinventory/import.html",
            context,
        )